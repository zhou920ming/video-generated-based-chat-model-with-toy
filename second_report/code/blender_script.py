# 记录第一次接收到帧的时间
import bpy
import bmesh
import math
import os
import time
import threading
import winsound
import subprocess
import sys
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, FloatProperty

class OBJECT_OT_content_driven_animation(Operator):
    bl_idname = "object.content_driven_animation"
    bl_label = "Content Driven Animation"
    bl_description = "25fps线性插值动画 Windows"

    # 参数
    content_file: StringProperty(name="Content文件路径", default="C:\\Users\\zhou\\Desktop\\7_13\\content.txt")
    audio_path: StringProperty(name="音频路径", default="C:\\Users\\zhou\\Desktop\\7_13\\data\\2025-07-16_17")
    buffer_size: IntProperty(name="缓冲帧数", default=20, min=10, max=201)
    delay: FloatProperty(name="延迟秒数", default=0.5, min=0.0, max=5.0, description="从开始接收帧计时的延迟")
    fps: IntProperty(name="播放帧率", default=25, min=1, max=60)
    
    # 插值参数
    interpolate_frames: IntProperty(name="插值间隔", default=5, min=1, max=20, description="每N帧进行线性插值")
    max_interpolation_gap: IntProperty(name="最大插值间隔", default=200, min=10, max=1000, description="超过此间隔不进行插值")

    # 内部状态
    _timer = None
    _current_playback_frame = 0
    _last_generated_frame = 0
    _is_playing = False
    _can_start_playing = False
    _animation_data = {}  # 存储关键帧数据
    _interpolated_data = {}  # 存储插值帧数据
    _object_mapping = {}
    _last_states = {}
    _file_last_modified = 0
    _file_last_position = 0
    _processed_frames = set()
    _max_frame_in_file = 0
    _audio_files = {}  # 存储音频文件信息：{frame: audio_filename}
    _audio_threads = {}  # 存储音频播放定时器
    
    # 精确时间控制
    _animation_start_time = 0
    _frame_duration = 0
    _last_max_frame_update = 0
    
    # 缓冲区管理
    _buffer_ready = False
    _delay_start_time = 0
    _delay_completed = False
    _first_frame_received_time = 0  
    
    # 性能监控
    _frame_times = []
    _last_perf_report = 0
    
    # 插值状态跟踪 - 移除手动插值，依赖Blender自动插值
    _last_keyframe_per_object = {}  

    def read_new_content(self):
        
        current_modified = os.path.getmtime(self.content_file)
        
        if current_modified <= self._file_last_modified and self._animation_data:
            return False
        
        old_max_frame = self._max_frame_in_file
        
        with open(self.content_file, 'r', encoding='utf-8') as f:
            if not self._animation_data:
                f.seek(0)
                new_lines = f.readlines()
                self._file_last_position = f.tell()
            else:
                f.seek(self._file_last_position)
                new_lines = f.readlines()
                self._file_last_position = f.tell()
        
        if not new_lines:
            return False
        
        self._file_last_modified = current_modified
        new_data = {} 
        new_audio = {}
        
        for line in new_lines:
            line = line.strip()
            if not line:
                continue
            
            # 处理音频文件行
            if line.endswith('.wav'):
                parts = line.split('|')
                if len(parts) == 2:
                    try:
                        frame = int(parts[0])
                        audio_filename = parts[1]
                        if frame not in self._audio_files:
                            self._audio_files[frame] = audio_filename
                            new_audio[frame] = audio_filename
                           
                            if self._is_playing:
                                self.schedule_audio_playback(frame, audio_filename)
                    except ValueError:
                        continue
                continue
            
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 2:
                    try:
                        frame = int(parts[0])
                        self._max_frame_in_file = max(self._max_frame_in_file, frame)
                        
                        # 合并数据
                        if frame not in new_data:
                            new_data[frame] = {}
                        
                        
                        for part in parts[1:]:
                            if ':' in part:
                                obj_id, data_str = part.split(':', 1)
                                obj_id = int(obj_id)
                                data = [float(x) for x in data_str.split(',')]
                              
                                new_data[frame][obj_id] = data
                        
                        # 标记该帧已处理
                        self._processed_frames.add(frame)
                            
                    except ValueError:
                        continue
        
       
        if new_data and self._first_frame_received_time == 0:
            self._first_frame_received_time = time.time()
        
        if new_data:
            # 合并新数据到现有动画数据
            for frame, frame_data in new_data.items():
                if frame in self._animation_data:
                   
                    self._animation_data[frame].update(frame_data)
                else:
                    # 新帧
                    self._animation_data[frame] = frame_data
            
            # 立即为每个新帧生成关键帧
            for frame in sorted(new_data.keys()):
                # 立即生成该帧的关键帧（不论是否与前一帧相同）
                frame_success = self.generate_keyframes_for_frame(frame)
                if frame_success:
                    self._last_generated_frame = max(self._last_generated_frame, frame)

            
            # 检查是否有新的最大帧数
            if self._max_frame_in_file > old_max_frame:
                self._last_max_frame_update = time.time()
            
            return True
        
        if new_audio:
            return True
        
        return False

    def read_entire_file(self):
        """启动时读取整个文件"""
        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                return False
            
            initial_data = {} 
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 处理音频文件行
                if line.endswith('.wav'):
                    parts = line.split('|')
                    if len(parts) == 2:
                        try:
                            frame = int(parts[0])
                            audio_filename = parts[1]
                            self._audio_files[frame] = audio_filename
                            
                        except ValueError:
                            continue
                    continue
                
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        try:
                            frame = int(parts[0])
                            self._max_frame_in_file = max(self._max_frame_in_file, frame)
                            
                            # 修改：如果该帧已存在，合并数据而不是覆盖
                            if frame not in initial_data:
                                initial_data[frame] = {}
                            
                            # 处理该行中的所有对象数据
                            for part in parts[1:]:
                                if ':' in part:
                                    obj_id, data_str = part.split(':', 1)
                                    obj_id = int(obj_id)
                                    data = [float(x) for x in data_str.split(',')]
                                    # 添加到该帧的数据中
                                    initial_data[frame][obj_id] = data
                            
                            # 标记该帧已处理
                            self._processed_frames.add(frame)
                                
                        except ValueError:
                            continue
            
            if initial_data:
                self._animation_data.update(initial_data)
                
                # 记录第一次接收到帧的时间
                if self._first_frame_received_time == 0:
                    self._first_frame_received_time = time.time()
                

               
                return True
            
            return False
            
        except Exception as e:
            print(f"读取文件错误: {e}")
            return False
        
    def invoke(self, context, event):
        
        
        # 计算精确的帧持续时间
        self._frame_duration = 1.0 / self.fps
        
        # 检查文件是否存在，不存在则创建
        if not os.path.exists(self.content_file):
            try:
                os.makedirs(os.path.dirname(self.content_file), exist_ok=True)
                with open(self.content_file, 'w', encoding='utf-8') as f:
                    f.write("")
            except Exception as e:
                self.report({'ERROR'}, f"无法创建文件: {self.content_file}, 错误: {e}")
                return {'CANCELLED'}
        
        # 初始化对象映射
        self.setup_object_mapping()
        
        # 设置所有对象的第0帧默认状态
        self.set_initial_frame_zero_state(context)
        
        # 读取文件内容
        file_has_data = self.read_entire_file()
        if not file_has_data:
            self._animation_data = {}
            self._interpolated_data = {}
            self._processed_frames = set()
            self._max_frame_in_file = 0
        
        # 设置文件监控状态
        self._file_last_modified = os.path.getmtime(self.content_file)
        with open(self.content_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            self._file_last_position = f.tell()
        
        # 初始化状态
        self._last_max_frame_update = time.time()
        self._delay_start_time = 0
        self._delay_completed = False
        self._last_keyframe_per_object = {}
        self._first_frame_received_time = 0
        self._audio_threads = {}
        
        # 初始化Windows音频系统
        self.initialize_audio_system()
        
        return self.execute(context)

    def setup_object_mapping(self):
        """设置对象映射"""
        self._object_mapping = {}
        
        # 物体列表（编号0-2）
        object_names = ['eye.L', 'eye.R', 'pikachu']
        
        # 骨骼列表（编号3-24）
        bone_names = [
            'body3', 'body2', 'body1', 'head', 'ear1.R', 'ear2.R', 'ear3.R',
            'ear1.L', 'ear2.L', 'ear3.L', 'arm1.R', 'arm2.R', 'arm3.R',
            'arm1.L', 'arm2.L', 'arm3.L', 'leg1.R', 'leg2.R', 'leg3.R',
            'leg1.L', 'leg2.L', 'leg3.L'
        ]
        
        # 形态键列表（编号25-31）
        shape_key_names = ['erb', 'erc', 'elb', 'elc', 'm1', 'm2', 'm3']
        
        # 映射物体
        for i, obj_name in enumerate(object_names):
            obj = bpy.data.objects.get(obj_name)
            if obj:
                self._object_mapping[i] = ('object', obj)
        
        # 映射骨骼
        armature = bpy.data.objects.get('skeleton')
        if armature and armature.type == 'ARMATURE':
            for i, bone_name in enumerate(bone_names):
                bone_id = i + 3
                if bone_name in armature.data.bones:
                    self._object_mapping[bone_id] = ('bone', armature, bone_name)
        
        # 映射形态键
        pikachu = bpy.data.objects.get('pikachu')
        if pikachu and pikachu.data.shape_keys:
            for i, key_name in enumerate(shape_key_names):
                key_id = i + 25
                if key_name in [key.name for key in pikachu.data.shape_keys.key_blocks]:
                    self._object_mapping[key_id] = ('shape_key', pikachu, key_name)

    def set_initial_frame_zero_state(self, context):
        """设置第0帧的初始状态"""
        # 设置场景到第0帧
        context.scene.frame_set(0)
        
        # 为所有映射的对象设置默认状态
        for obj_id, obj_info in self._object_mapping.items():
            obj_type = obj_info[0]
            
            try:
                if obj_type == 'object':
                    obj = obj_info[1]
                    # 设置默认旋转为0
                    obj.rotation_euler.x = 0
                    obj.rotation_euler.y = 0
                    obj.rotation_euler.z = 0
                    obj.keyframe_insert(data_path="rotation_euler", frame=0)
                    
                elif obj_type == 'bone':
                    armature, bone_name = obj_info[1], obj_info[2]
                    
                    current_active = bpy.context.view_layer.objects.active
                    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
                    
                    bpy.context.view_layer.objects.active = armature
                    bpy.ops.object.mode_set(mode='POSE')
                    
                    pose_bone = armature.pose.bones.get(bone_name)
                    if pose_bone:
                        # 设置默认变换
                        pose_bone.location.x = 0
                        pose_bone.location.y = 0
                        pose_bone.location.z = 0
                        
                        pose_bone.rotation_euler.x = 0
                        pose_bone.rotation_euler.y = 0
                        pose_bone.rotation_euler.z = 0
                        
                        pose_bone.scale.x = 1
                        pose_bone.scale.y = 1
                        pose_bone.scale.z = 1
                        
                        pose_bone.keyframe_insert(data_path="location", frame=0)
                        pose_bone.keyframe_insert(data_path="rotation_euler", frame=0)
                        pose_bone.keyframe_insert(data_path="scale", frame=0)
                    
                    try:
                        bpy.ops.object.mode_set(mode=current_mode)
                        if current_active:
                            bpy.context.view_layer.objects.active = current_active
                    except:
                        pass
                        
                elif obj_type == 'shape_key':
                    mesh_obj, key_name = obj_info[1], obj_info[2]
                    if mesh_obj.data.shape_keys:
                        key_block = mesh_obj.data.shape_keys.key_blocks.get(key_name)
                        if key_block:
                            key_block.value = 0.0
                            key_block.keyframe_insert(data_path="value", frame=0)
                            
            except Exception as e:
                print(f"设置对象 {obj_id} 第0帧状态错误: {e}")

    def initialize_audio_system(self):
        """初始化Windows系统音频播放"""
        try:
            init_time = time.time()
            print(f"初始化时间: {init_time:.3f}")
            
            # 停止Blender音频播放
            if bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
                print("停止Blender音频播放")
            
            # 禁用Blender音频，避免冲突
            bpy.context.scene.use_audio = False
            print("禁用Blender音频系统")
            
            # 清理音频相关数据
            self._audio_threads = {}
            
            print(f"Windows音频系统初始化完成，耗时: {time.time() - init_time:.3f}秒")
            
        except Exception as e:
            print(f"Windows音频系统初始化错误: {e}")

    def calculate_audio_play_time(self, audio_frame):
        """计算音频应该播放的精确时间"""
        if not self._is_playing or self._animation_start_time == 0:
            return None
        
        # 计算音频帧对应的绝对时间
        frame_time_offset = audio_frame * self._frame_duration  # 音频帧相对于动画开始的时间
        audio_target_time = self._animation_start_time + frame_time_offset
        
        return audio_target_time

    def schedule_audio_playback(self, audio_frame, audio_filename):
        """安排音频在指定时间播放"""
        try:
            schedule_time = time.time()
            target_play_time = self.calculate_audio_play_time(audio_frame)
            
            if target_play_time is None:
                print(f"无法计算音频播放时间: 帧{audio_frame}")
                return False
            
            current_time = time.time()
            delay_seconds = target_play_time - current_time

            
            # 特殊处理第0帧：总是立即播放
            if audio_frame == 0:
                print(f"🔊 🎬 第0帧音频立即播放: {audio_filename}")
                self.play_audio_immediately(audio_filename)
                return True
            
            # 如果延迟为负数，说明已经错过了播放时机
            if delay_seconds < -0.1:  # 容忍100ms的误差
                print(f"延迟{delay_seconds:.3f}")
                return False
            
            # 如果延迟很小，立即播放
            if delay_seconds <= 0.05:  # 50ms内立即播放
                print(f"🔊 🎵 立即播放音频: {audio_filename}")
                self.play_audio_immediately(audio_filename)
                return True
            
            # 创建定时播放线程
            audio_key = f"{audio_frame}_{audio_filename}"
            if audio_key not in self._audio_threads:
                thread = threading.Timer(delay_seconds, self.play_audio_immediately, args=[audio_filename])
                thread.daemon = True
                thread.start()
                self._audio_threads[audio_key] = thread
                
               
                return True
            else:
                
                return False
                
        except Exception as e:
         
            return False

    def play_audio_immediately(self, audio_filename):

        try:
            play_start_time = time.time()
            current_frame = bpy.context.scene.frame_current
            

            
            # 构建完整音频路径
            audio_file_path = os.path.join(self.audio_path, audio_filename)
            
            if not os.path.exists(audio_file_path):
      
                return False
            
            # Windows系统播放
            if sys.platform.startswith('win'):
                # 使用异步播放，避免阻塞
                def play_thread():
                    try:
                        thread_start = time.time()
                        
                        
                        # 使用SND_ASYNC避免阻塞，SND_NOSTOP允许同时播放多个音频
                        winsound.PlaySound(
                            audio_file_path, 
                            winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NOSTOP
                        )
                        
                        thread_end = time.time()
     
                        
                    except Exception as e:
                        print(f"播放失败: {e}")
                
                # 在单独线程中播放
                thread = threading.Thread(target=play_thread)
                thread.daemon = True
                thread.start()
                
                return True
            else:

                return False
                
        except Exception as e:

            return False

    def schedule_all_existing_audio(self):
    
        try:
            schedule_time = time.time()
           
            
            scheduled_count = 0
            for frame, audio_filename in self._audio_files.items():
                # 跳过第0帧，因为已经在check_can_start_playing中处理了
                if frame == 0:
                    
                    continue
                    
                success = self.schedule_audio_playback(frame, audio_filename)
                if success:
                    scheduled_count += 1
            
            print(f"音频调度完成: {scheduled_count}/{len(self._audio_files) - (1 if 0 in self._audio_files else 0)} 个文件已调度")
            
        except Exception as e:
            print(f"调度音频错误: {e}")

    def cancel_all_audio(self):
        """取消所有音频播放和定时器"""
        try:
            cancel_time = time.time()
            
            
            # 取消所有定时器
            cancelled_count = 0
            for audio_key, thread in self._audio_threads.items():
                try:
                    thread.cancel()
                    cancelled_count += 1
                except:
                    pass
            
            self._audio_threads.clear()
         
            
            # 停止当前Windows音频播放（如果支持）
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)

            except:
                pass
                
        except Exception as e:
            print(f"错误: {e}")

    def generate_all_keyframes_immediately(self):

        # 获取所有关键帧并排序
        keyframes = sorted(self._animation_data.keys())
        
        if len(keyframes) < 1:
            return
        
        # 直接生成所有关键帧，让Blender处理插值
        for frame in keyframes:
            self.generate_keyframes_for_frame(frame)
        
        # 最后统一设置所有关键帧为线性插值
        self.set_all_keyframes_to_linear()

    def check_buffer_status(self):
  
        # 计算可用的帧数（关键帧 + 插值帧）
        available_frames = self._max_frame_in_file - self._current_playback_frame
        
        # 不再有缓冲限制，只要有帧就播放
        has_enough_buffer = available_frames > 0
        
        if has_enough_buffer:
            return True, f"可用帧数: {available_frames}帧"
        else:
            return False, f"无可用帧: {available_frames}帧"

    def check_can_start_playing(self, current_time):
        """检查是否可以开始播放（从第一次接收到帧开始计时延迟）"""
        if self._can_start_playing:
            return True
        
        # 必须先接收到帧数据
        if self._first_frame_received_time == 0:
            return False
        
        # 从第一次接收到帧开始计时延迟
        time_since_first_frame = current_time - self._first_frame_received_time
        
        if time_since_first_frame >= self.delay:
            # 延迟时间到，只要有数据就开始播放
            if self._animation_data and self._max_frame_in_file > 0:
                # 生成所有可用的关键帧
                self.generate_all_available_frames()
                
                self._can_start_playing = True
                print(f"🔊 🎬 播放开始，调度所有现有音频")
                
                # 特殊处理：优先播放第0帧音频
                if 0 in self._audio_files:

                    self.play_audio_immediately(self._audio_files[0])
                
                # 调度所有其他音频文件
                self.schedule_all_existing_audio()
                
                return True
        
        return False

    def generate_all_available_frames(self):
        """生成所有可用的关键帧"""
        sorted_frames = sorted(self._animation_data.keys())
        
        # 生成所有关键帧
        for frame in sorted_frames:
            self.generate_keyframes_for_frame(frame)
            self._last_generated_frame = max(self._last_generated_frame, frame)

    def smart_generate_frames_ahead(self, context):
        """智能生成后续关键帧"""
        # 读取新内容
        new_content = self.read_new_content()
        
        # 生成所有新的关键帧，不限制缓冲区大小
        sorted_frames = sorted(self._animation_data.keys())
        frames_to_generate = [f for f in sorted_frames 
                             if f > self._last_generated_frame]
        
        if frames_to_generate:
            for frame in frames_to_generate:
                self.generate_keyframes_for_frame(frame)
                self._last_generated_frame = max(self._last_generated_frame, frame)

    def get_frame_data(self, frame):
        """获取帧数据（只从关键帧获取）"""
        if frame in self._animation_data:
            return self._animation_data[frame]
        else:
            return None

    def generate_keyframes_for_frame(self, frame):
        """为特定帧生成关键帧（强制生成，不论是否与前帧相同）"""
        frame_data = self.get_frame_data(frame)
        if not frame_data:
            return False
        
        success_count = 0
        total_count = len(frame_data)
        
        for obj_id, data in frame_data.items():
            if obj_id in self._object_mapping:
                success = self.set_object_state(obj_id, data, frame)
                if success:
                    success_count += 1
                    self._last_states[obj_id] = data
        
        return success_count > 0

    def set_object_state(self, obj_id, data, frame):
        """设置对象状态并添加关键帧 - 强制添加每一帧作为关键帧"""
        if obj_id not in self._object_mapping:
            return False
        
        obj_type, *obj_data = self._object_mapping[obj_id]
        
        try:
            if obj_type == 'object':
                obj = obj_data[0]
                if len(data) >= 3:
                    obj.rotation_euler.x = math.radians(data[0])
                    obj.rotation_euler.y = math.radians(data[1])
                    obj.rotation_euler.z = math.radians(data[2])
                    
                    # 强制插入关键帧，不论值是否相同
                    obj.keyframe_insert(data_path="rotation_euler", frame=frame)
                    
                    # 设置插值类型为线性
                    if obj.animation_data and obj.animation_data.action:
                        for fcurve in obj.animation_data.action.fcurves:
                            if fcurve.data_path == "rotation_euler":
                                for keyframe in fcurve.keyframe_points:
                                    if keyframe.co[0] == frame:
                                        keyframe.interpolation = 'LINEAR'
                    
                    return True
                    
            elif obj_type == 'bone':
                armature, bone_name = obj_data
                
                current_active = bpy.context.view_layer.objects.active
                current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
                
                bpy.context.view_layer.objects.active = armature
                bpy.ops.object.mode_set(mode='POSE')
                
                pose_bone = armature.pose.bones.get(bone_name)
                if pose_bone and len(data) >= 9:
                    pose_bone.location.x = data[0]
                    pose_bone.location.y = data[1]
                    pose_bone.location.z = data[2]
                    
                    pose_bone.rotation_euler.x = math.radians(data[3])
                    pose_bone.rotation_euler.y = math.radians(data[4])
                    pose_bone.rotation_euler.z = math.radians(data[5])
                    
                    pose_bone.scale.x = data[6]
                    pose_bone.scale.y = data[7]
                    pose_bone.scale.z = data[8]
                    
                    # 强制插入关键帧，不论值是否相同
                    pose_bone.keyframe_insert(data_path="location", frame=frame)
                    pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
                    pose_bone.keyframe_insert(data_path="scale", frame=frame)
                    
                    # 设置插值类型为线性
                    if armature.animation_data and armature.animation_data.action:
                        bone_prefix = f'pose.bones["{bone_name}"]'
                        data_paths = [
                            f'{bone_prefix}.location',
                            f'{bone_prefix}.rotation_euler', 
                            f'{bone_prefix}.scale'
                        ]
                        
                        for fcurve in armature.animation_data.action.fcurves:
                            if any(fcurve.data_path.startswith(path) for path in data_paths):
                                for keyframe in fcurve.keyframe_points:
                                    if keyframe.co[0] == frame:
                                        keyframe.interpolation = 'LINEAR'
                    
                    try:
                        bpy.ops.object.mode_set(mode=current_mode)
                        if current_active:
                            bpy.context.view_layer.objects.active = current_active
                    except:
                        pass
                    
                    return True
                elif not pose_bone:
                    return False
                elif len(data) < 9:
                    return False
            
            elif obj_type == 'shape_key':
                mesh_obj, key_name = obj_data
                if mesh_obj.data.shape_keys and len(data) >= 1:
                    key_block = mesh_obj.data.shape_keys.key_blocks.get(key_name)
                    if key_block:
                        value = max(0.0, min(1.0, data[0]))
                        key_block.value = value
                        
                        # 强制插入关键帧，不论值是否相同
                        key_block.keyframe_insert(data_path="value", frame=frame)
                        
                        # 设置插值类型为线性
                        if mesh_obj.data.shape_keys.animation_data and mesh_obj.data.shape_keys.animation_data.action:
                            data_path = f'key_blocks["{key_name}"].value'
                            for fcurve in mesh_obj.data.shape_keys.animation_data.action.fcurves:
                                if fcurve.data_path == data_path:
                                    for keyframe in fcurve.keyframe_points:
                                        if keyframe.co[0] == frame:
                                            keyframe.interpolation = 'LINEAR'
                        
                        return True
                    else:
                        return False
                else:
                    return False
        
        except Exception as e:
            return False
        
        return False

    def set_all_keyframes_to_linear(self):
        """将所有现有关键帧设置为线性插值"""
        try:
            # 处理所有对象的动画
            for obj in bpy.data.objects:
                if obj.animation_data and obj.animation_data.action:
                    for fcurve in obj.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'LINEAR'
            
            # 处理形态键动画
            for mesh in bpy.data.meshes:
                if mesh.shape_keys and mesh.shape_keys.animation_data and mesh.shape_keys.animation_data.action:
                    for fcurve in mesh.shape_keys.animation_data.action.fcurves:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'LINEAR'
            
        except Exception as e:
            print(f"设置线性插值错误: {e}")

    def pregenerate_frames(self, context):
        """预生成初始帧"""
        sorted_frames = sorted(self._animation_data.keys())
        
        # 生成所有关键帧
        for frame in sorted_frames:
            self.generate_keyframes_for_frame(frame)
            self._last_generated_frame = max(self._last_generated_frame, frame)
        
        return {'FINISHED'}

    def get_target_frame_by_time(self, current_time):
        """根据精确时间计算目标帧数"""
        if not self._is_playing or self._animation_start_time == 0:
            return self._current_playback_frame
        
        # 计算从开始播放到现在的时间
        elapsed_time = current_time - self._animation_start_time
        
        # 计算理论上应该播放到的帧数
        target_frame = int(elapsed_time / self._frame_duration)
        
        return target_frame

    def execute(self, context):
        result = self.pregenerate_frames(context)
        if result == {'CANCELLED'}:
            return result

        self._current_playback_frame = 0
        self._is_playing = False

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.005, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            current_time = time.time()
            
            # 如果还没有开始播放，持续检查
            if not self._is_playing:
                self.read_new_content()
                
                if self.check_can_start_playing(current_time):
                    self._is_playing = True
                    self._animation_start_time = current_time
                    
                else:
                    return {'PASS_THROUGH'}
            
            # 播放逻辑
            if self._is_playing:
                # 检查是否有可播放的帧
                has_frames, frame_status = self.check_buffer_status()
                
                if has_frames:
                    # 有可用帧，正常播放
                    target_frame = self.get_target_frame_by_time(current_time)
                    
                    if target_frame > self._current_playback_frame:
                        old_frame = self._current_playback_frame
                        self._current_playback_frame = target_frame
                        context.scene.frame_current = self._current_playback_frame
                        
                        
                        # 生成后续帧
                        self.smart_generate_frames_ahead(context)
                        
                        # 每25帧检查音频系统状态
                        if self._current_playback_frame % 25 == 0:
                            self.debug_audio_status()
                            
                else:
                    # 无可用帧，等待更多数据
                    self.smart_generate_frames_ahead(context)
        
        elif event.type == 'ESC':
            self.cancel_all_audio()  # 取消所有音频
            self.cancel(context)
            return {'CANCELLED'}
        
        return {'PASS_THROUGH'}

    def debug_audio_status(self):
        """调试音频状态"""
        try:
            current_time = time.time()
            current_frame = bpy.context.scene.frame_current

            # 显示接下来几帧的音频
            upcoming_audio = []
            for frame in range(current_frame, current_frame + 10):
                if frame in self._audio_files:
                    upcoming_audio.append(f"第{frame}帧")
            

        except Exception as e:
            print(f"音频状态错误: {e}")

    def cancel(self, context):
        cancel_time = time.time()
        current_frame = context.scene.frame_current

        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        self._is_playing = False
        
        # 取消所有音频播放
        self.cancel_all_audio()






def register():
    bpy.utils.register_class(OBJECT_OT_content_driven_animation)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_content_driven_animation)


if __name__ == "__main__":
    register()

    bpy.ops.object.content_driven_animation('INVOKE_DEFAULT')
