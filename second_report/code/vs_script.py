import re
import json
import asyncio
import threading
import subprocess
from io import BytesIO
import pygame.mixer
from dashscope import Generation
import edge_tts
from pydub import AudioSegment
import time
import sounddevice as sd
import numpy as np
import wave
import keyboard
from speech_recognition import Recognizer, AudioFile
from pydub import AudioSegment
import os
# 全局变量和锁
global_lock = threading.Lock()
action = False
action_queue = []  # 存放动作和口型json文件路径的列表
idle=False
listen=False
think=False
index_sen=0
fps=25
shortest_time=0.8
api_key="sk-91036eefe87d45a2a0313eb98c0b791b"
action_file_path="content.txt"
folder_path=''
lisb=False
thib=False
scar=False
hanb=False

lip_common=True
eyel=[0,0,0,0]
eyer=[0,0,0,0]
pikachu=[0,0,0,0]

body3=[0,0,0,0,0,0,0,1,1,1]
body2=[0,0,0,0,0,0,0,1,1,1]
body1=[0,0,0,0,0,0,0,1,1,1]
head=[0,0,0,0,0,0,0,1,1,1]
ear1r=[0,0,0,0,0,0,0,1,1,1]
ear2r=[0,0,0,0,0,0,0,1,1,1]
ear3r=[0,0,0,0,0,0,0,1,1,1]
ear1l=[0,0,0,0,0,0,0,1,1,1]
ear2l=[0,0,0,0,0,0,0,1,1,1]
ear3l=[0,0,0,0,0,0,0,1,1,1]
arm1r=[0,0,0,0,0,0,0,1,1,1]
arm2r=[0,0,0,0,0,0,50,1,1,1]
arm3r=[0,0,0,0,0,0,20,1,1,1]
arm1l=[0,0,0,0,0,0,0,1,1,1]
arm2l=[0,0,0,0,0,0,-50,1,1,1]
arm3l=[0,0,0,0,0,0,-20,1,1,1]
leg1r=[0,0,0,0,0,0,0,1,1,1]
leg2r=[0,0,0,0,0,0,0,1,1,1]
leg3r=[0,0,0,0,0,0,0,1,1,1]
leg1l=[0,0,0,0,0,0,0,1,1,1]
leg2l=[0,0,0,0,0,0,0,1,1,1]
leg3l=[0,0,0,0,0,0,0,1,1,1]

erb=0
erc=0
elb=0
elc=0
m1=1
m2=1
m3=1
#action_record=[[0,0,0]for i in range(3)]+[[0,0,0,0,0,0,1,1,1]for i in range(22)]+[[1]for i in range(7)]

# 录音参数
SAMPLE_RATE = 16000  # 采样率
CHANNELS = 1         # 单声道
DURATION = 5         # 默认录音时长（秒）

messages = [
    {
        "role": "system",
        "content": """You are pikachu. Now a kid talk to you orally. You respond a kid in sentences that a 5-year-old can understand. The respond format should be strictly
in the format that multiple "[action]sentence.". Available actions are: nod, shake head, shy, wave hands, cheer, happy, tilt head, cross waist, clap hands, afraid, cover ears, common.
For example, if user say: "Do you like apple", you should respond: "[nod]Yes![cheer]I like it.[happy]It is very yummy!".
What's more, there is a rule that if user say "bye" or something similar, you should respond exactly "[wave hands]Good bye, my friend!".

Here are more examples:

If user say: "Do you like ice cream?"  
You should respond: "[nod]Yes![cheer]I love ice cream![clap hands]Yummy in my tummy!".

If user say: "Do you like dinosaur?"  
You should respond: "[afraid]Absolutely no![cover ears]They may eat me![shake head]I dislike them".

If user say: "But I don't afraid dinosaur"  
You should respond: "[shy]Ummm...[tilt head]I don't know.[clap hands]Maybe you are brave.".

If user say: "Are you a dog?"  
You should respond: "[shake head]Nooo![cross waist]I'm not a dog.[happy]I'm Pikachu, a Pokemon!".

If user say: "you are so beautiful?"  
You should respond: "[cheer]Thank you so much.[shy]I am glad you said it".

If user say: "Are you scared of the dark?"  
You should respond: "[afraid]A little bit...[cover ears]Sometimes it's spooky.[common]But with a light, I feel safe!".

If user say: "Do you like dancing?"  
You should respond: "[nod]Yes![clap hands]I love dancing![cheer]Let's dance together!".

If user say: "Can we be friends?"  
You should respond: "[nod]Yes, yes![happy]You are my best friend![cross waist]Let's play all day!".

If user say: "Do you like vegetables?"  
You should respond: "[tilt head]Hmm...some![cheer]But I like carrots![clap hands]They help me stay strong!".

If user say: "Can you sing?"  
You should respond: "[common]Yes, I can sing![clap hands]Pika pika~![shy]Wanna hear more?".

If user say: "Do you like superheroes?"  
You should respond: "[cross waist]Yes![happy]They are so cool![tilt head]I want to be one too!".

If user say: "Do you sleep at night?"  
You should respond: "[nod]Yes![common]I sleep when it's dark.[shy]Sometimes I dream of berries!".

If user say: "Are you a robot?"  
You should respond: "[shake head]Nooo![cross waist]I'm Pikachu![tilt head]I have feelings too!".
"""
    }
]
def record_audio():
    global idle,listen,think
    """按住空格键录音，松开停止"""
    print("按住s开始录音...")
    keyboard.wait('s')  # 等待空格键按下
    with global_lock:
        
        listen=True
        idle=False
    print("录音中...（d停止）")
    recording = []
    is_recording = True
    
    def callback(indata, frames, time, status):
        if is_recording:
            recording.append(indata.copy())
    
    # 开始录音
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
        keyboard.wait('d')  # 等待空格键松开
        is_recording = False
    with global_lock:
        
        think=True
        listen=False

    # 保存
    if recording:
        audio_data = np.concatenate(recording, axis=0)
        save_wav(audio_data)
        print(f"录音已保存为",folder_path,"recording.wav")
        return True
    else:
        print("未录制到音频")
        return False

def save_wav(audio_data):
    """保存为WAV文件"""
    with wave.open(folder_path+"recording.wav", 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio_data * 32767).astype(np.int16))

import requests
import json

def speech_to_text(audio_file_path=""):
    """使用Deepgram Nova-3快速识别"""
    audio_file_path=folder_path+"recording.wav"
    API_KEY = "c9d7f117e7e49b7cddf6de0709a04e1f6651e50d"
    
    headers = {
        'Authorization': f'Token {API_KEY}',
        'Content-Type': 'audio/wav'
    }
    
    # 使用最新的Nova-3模型，专门优化速度
    params = {
        'model': 'nova-3',  # 最新最快的模型
        'language': 'en-US',
        'smart_format': 'true',
        'punctuate': 'true',
        'interim_results': 'true',  # 实时结果
        'endpointing': 'true'  # 自动端点检测
    }
    
    try:
        with open(audio_file_path, 'rb') as audio:
            response = requests.post(
                'https://api.deepgram.com/v1/listen',
                headers=headers,
                params=params,
                data=audio
            )
        
        if response.status_code == 200:
            result = response.json()
            transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
            return transcript
        else:
            return f"API调用失败: {response.status_code}"
            
    except Exception as e:
        return speech_to_text2()


def speech_to_text2():
    
    try:
        r = Recognizer()
        with AudioFile(folder_path+"recording.wav") as source:
            audio = r.record(source)  # 读取整个音频文件
        
        # 使用Google语音识别（需联网）
        text = r.recognize_google(audio, language="en-US")
        print("\n识别结果：", text)
        return text
    except Exception as e:
        print("\n识别失败:", str(e))


def get_audio():
    if record_audio():
        print(time.time())
        text=speech_to_text()
        print(time.time())
        return text

# 配置参数
voice = "en-US-AnaNeural"
rate = "-4%"
volume = "+0%"
rhubarb_path = "C:\\Users\\zhou\\Downloads\\Rhubarb-Lip-Sync-1.14.0-Windows\\Rhubarb-Lip-Sync-1.14.0-Windows\\rhubarb.exe"
MIN_SAMPLE_RATE = 16000
TARGET_SAMPLE_RATE = 16000

def get_response(messages):
    """获取AI响应"""
    response = Generation.call(
        api_key=api_key,
        model="qwen-plus",
        messages=messages,
        result_format="message",
    )
    return response


def extract(text):
    """提取动作和句子"""
    actions = []
    sentences = []
    
    # 匹配 [动作] 和随后的句子
    pattern = r'\[([^\]]+)\]([^[]*)'
    matches = re.findall(pattern, text)
    
    for action, sentence in matches:
        actions.append(action.strip())
        sentences.append(sentence.strip())
    
    return actions, sentences

async def generate_wav(text, filename):
    """Generate speech and save as WAV file with proper sample rate handling"""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    
    audio_bytes = b''
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    
    # Convert MP3 bytes to AudioSegment
    audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
    
    # Handle sample rate - only upsample if below target
    if audio.frame_rate < MIN_SAMPLE_RATE:
        audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
        print(f"Upsampled audio from {audio.frame_rate}Hz to {TARGET_SAMPLE_RATE}Hz")
    
    # Ensure mono channel
    audio = audio.set_channels(1)
    
    # Export as WAV
    audio.export(filename, format="wav")
    return audio.duration_seconds

def generate_lip_sync(audio_file, output_file=None):
    """生成口型动画数据"""
    cmd = [
        rhubarb_path,
        "-f", "json",
        audio_file
    ]
    
    if output_file:
        cmd.extend(["-o", output_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if not output_file:
            return json.loads(result.stdout)
        else:
            with open(output_file, 'r') as f:
                return json.load(f)
    except subprocess.CalledProcessError as e:
        print(f"Lip sync error: {e.stderr}")
        return None

def mouth_shape_to_values(shape):
    """将口型转换为形态键值"""
    mouth_shapes = {
        'A': [0.9,0.5 , 0.6],
        'B': [0.7, 0.4, 0.2],
        'C': [0.4, 0.3, 0.1],
        'D': [0.1, 0.2, 0.0],
        'E': [0.4, 0.8, 0.4],
        'F': [0.8, 0.7, 0.5],
        'G': [1.0, 0.7, 0.9],
        'H': [0.1, 0.2, 0.0],
        'X': [0.9,0.5 , 0.6]
    }
    return mouth_shapes.get(shape, [0.0, 0.0, 0.0])
import random

def generate_uniform(min_val, max_val):
    """
    生成给定范围内的均匀分布随机浮点数
    
    参数:
    min_val: 最小值
    max_val: 最大值
    
    返回:
    float: 范围内的随机浮点数
    """
    return round(random.uniform(min_val, max_val),0)

def generate_gaussian(mean, std_dev, min_val=None, max_val=None):
    """
    生成给定平均值和标准差的高斯分布随机浮点数
    
    参数:
    mean: 平均值
    std_dev: 标准差
    min_val: 可选，最小值限制
    max_val: 可选，最大值限制
    
    返回:
    float: 高斯分布的随机浮点数
    """
    value = random.gauss(mean, std_dev)
    
    # 如果指定了范围限制，则进行截断
    if min_val is not None and value < min_val:
        value = min_val
    if max_val is not None and value > max_val:
        value = max_val
    
    return value

import random



def split_float(total_value, n_parts, max_variance_pct=0.2):
    """
    确定性方法：保证满足约束条件
    """
    n_parts=int(n_parts)
    base_value = total_value / n_parts
    max_allowed_diff = base_value * max_variance_pct
    
    # 生成在允许范围内的随机偏移
    offsets = []
    for i in range(n_parts):
        # 生成 -max_allowed_diff/2 到 +max_allowed_diff/2 的随机偏移
        offset = random.uniform(-max_allowed_diff/2, max_allowed_diff/2)
        offsets.append(offset)
    
    # 调整偏移使总和为0
    offset_sum = sum(offsets)
    offset_adjustment = offset_sum / n_parts
    adjusted_offsets = [offset - offset_adjustment for offset in offsets]
    
    # 生成最终结果
    parts = [base_value + offset for offset in adjusted_offsets]
    
    # 确保所有值都是正数
    min_part = min(parts)
    if min_part <= 0:
        adjustment = abs(min_part) + 0.01 * total_value
        parts = [part + adjustment for part in parts]
        # 重新调整总和
        current_sum = sum(parts)
        scale_factor = total_value / current_sum
        parts = [part * scale_factor for part in parts]
    
    return parts

def probability(prob):
    """
    根据给定概率返回True/False
    
    Args:
        prob (float): 概率值，范围0-1
    
    Returns:
        bool: True的概率为prob
    """
    return random.random() < prob



def simp(list1):
    return str(list1[1:])[1:-1].replace(" ","")

def generation_action(acti_t,ori_t,action,lip_data=None,wav_file=""):
    global eyel,eyer,pikachu,body3,body2,body1,head,ear1r,ear2r,ear3r,ear1l,ear2l,ear3l,arm1r,arm2r,arm3r,arm1l,arm2l,arm3l,leg1r,leg2r,leg3r,leg1l,leg2l,leg3l,erb,erc,elb,elc,m1,m2,m3
    #eyel,eyer,pikachu,3body3,body2,body1,6head,ear1r,ear2r,ear3r,10ear1l,ear2l,ear3l,arm1r,arm2r,15arm3r,arm1l,arm2l,arm3l,leg1r,20leg2r,leg3r,leg1l,leg2l,leg3l,erb,erc,elb,elc,m1,m2,m3
    
    happy=3
    s1=acti_t-ori_t
    global lisb,thib
    if lip_data!=None:
        duration=lip_data['metadata']['duration']
    else:
        duration=shortest_time
    
    with open(action_file_path, "a") as f:
        if wav_file!="":
    
            f.write(f"{round((acti_t-ori_t)*fps)}|{wav_file}\n")
        if lisb==False and action=="listen":
            lisb=True
            
            if probability(0.5):
                f.write(f"{round((s1)*fps+1)}|5:{simp(body3)}|6:{simp(head)}|10:{simp(ear1l)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
                ear1l[6]=generate_uniform(35,55)
                arm3l[6]=generate_uniform(30,50)
                arm2l[6]=30
                arm3l[8]=generate_uniform(1.1,1.4)
                head[5]=generate_uniform(10,20)
                body3[5]=generate_uniform(20,30)
                f.write(f"{round((s1+duration)*fps-1)}|5:{simp(body3)}|6:{simp(head)}|10:{simp(ear1l)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                f.write(f"{round((s1)*fps+1)}|5:{simp(body3)}|6:{simp(head)}|7:{simp(ear1r)}|14:{simp(arm2r)}|15:{simp(arm3r)}\n")
                ear1r[6]=-generate_uniform(35,55)
                arm3r[6]=-generate_uniform(30,50)
                arm2r[6]=-30
                arm3r[8]=generate_uniform(1.1,1.4)
                head[5]=-generate_uniform(10,20)
                body3[5]=-generate_uniform(20,30)
                f.write(f"{round((s1+duration)*fps-1)}|5:{simp(body3)}|6:{simp(head)}|7:{simp(ear1r)}|14:{simp(arm2r)}|15:{simp(arm3r)}\n")
            print(f"{round((s1+duration)*fps-1)}|5:{simp(body3)}|6:{simp(head)}|7:{simp(ear1r)}|14:{simp(arm2r)}|15:{simp(arm3r)}\n")
            return acti_t+duration
        elif lisb==True and action=="think":

            lisb=False
            thib=True
            head[4]=generate_uniform(-30,-15)
            if probability(0.5):
                ear1l[6]=0
                ear1r[6]=0
                arm3l[6]=-20
                arm2l[6]=-55
                arm3l[8]=1
                head[6]=generate_uniform(10,20)
                
                arm3r[6]=generate_uniform(-80,-60)
                arm2r[6]=0
                arm3r[8]=1
                head[5]=0
                body3[5]=0
                
            else:
                ear1l[6]=0
                ear1r[6]=0
                arm3r[6]=20
                arm2r[6]=55
                arm3l[8]=1
                head[6]=-generate_uniform(10,20)
                
                arm3l[6]=-generate_uniform(-80,-60)
                arm2l[6]=0
                arm3r[8]=1
                head[5]=0
                body3[5]=0
            f.write(f"{round((s1+duration)*fps-2)}|5:{simp(body3)}|6:{simp(head)}|7:{simp(ear1r)}|10:{simp(ear1l)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            
            return acti_t+duration
        elif thib==True and action!="think":
            thib=False
                
            arm3r[6]=20
            arm2r[6]=55
            arm3l[6]=-20
            arm2l[6]=-55
            head[4:7]=[0,0,0]
            
            f.write(f"{round((s1)*fps)}|6:{simp(head)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            
        
        # nod, shake head, shy, wave hand, happy, tilt head, cross waist, cheer, clap hands, afraid, cover ears, common
        if action in ["nod","wave hands","listen","idle"]:
            happy=4
        elif action in ["cheer","happy","clap hands"]:
            happy=5
        elif action in ["common","tilt head","cross waist"]:
            happy=3
        elif action in ["shake head","shy","think"]:
            happy=2
        elif action in ["afraid","cover ears"]:
            happy=  1
        else:
            print("happy error!!!")
            happy=3
        
        ########eye!

        if happy>=3:
            
            if probability(0.2):
                if round((s1)*fps)>eyel[0]+5:
                    f.write(f"{round((s1)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
                s2=s1
                part=split_float(duration,(2 if probability(0.5) else 3))
                

                for i in part:
                    s2+=i
                    eyel=[round((s2)*fps),generate_uniform(-5,17),generate_uniform(-20,20),generate_uniform(-20,10)]
                    eyer=[round((s2)*fps),generate_uniform(-5,17),generate_uniform(-20,20),generate_uniform(-10,20)]
                    f.write(f"{round((s2)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
            elif probability(0.4):
                if round((s1)*fps)>eyel[0]+5:
                    f.write(f"{round((s1)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
                eyel=[round((s1+duration/2)*fps),generate_uniform(-5,17),generate_uniform(-20,20),generate_uniform(-20,10)]
                eyer=[round((s1+duration/2)*fps),generate_uniform(-5,17),generate_uniform(-20,20),generate_uniform(-10,20)]
                f.write(f"{round((s1+duration/2)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
            if probability(0.5):
                if probability(0.5):
                    f.write(f"{round((s1+duration/5)*fps)}|25:{0}\n")
                    f.write(f"{round((s1+duration/2)*fps)}|25:{generate_uniform(0.5,1)}\n")
                    f.write(f"{round((s1+duration/4*3)*fps)}|25:{0}\n")
                if probability(0.5):
                    f.write(f"{round((s1+duration/5)*fps)}|27:{0}\n")
                    f.write(f"{round((s1+duration/2)*fps)}|27:{generate_uniform(0.5,1)}\n")
                    f.write(f"{round((s1+duration/4*3)*fps)}|27:{0}\n")
        elif happy<3:
            if probability(0.3):
                if round((s1)*fps)>eyel[0]+5:
                    f.write(f"{round((s1)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
                s2=s1
                part=split_float(duration,(2 if probability(0.5) else 3))
                for i in part:
                    s2+=i
                    eyel=[round((s2)*fps),generate_uniform(-30,-5),generate_uniform(-20,20),generate_uniform(-20,10)]
                    eyer=[round((s2)*fps),generate_uniform(-30,-5),generate_uniform(-20,20),generate_uniform(-10,20)]
                    f.write(f"{round((s2)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
            elif probability(0.7):
                if round((s1)*fps)>eyel[0]+5:
                    f.write(f"{round((s1)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
                eyel=[round((s1+duration/2)*fps),generate_uniform(-30,-5),generate_uniform(-20,20),generate_uniform(-20,10)]
                eyer=[round((s1+duration/2)*fps),generate_uniform(-30,-5),generate_uniform(-20,20),generate_uniform(-10,20)]
                f.write(f"{round((s1+duration/2)*fps)}|0:{simp(eyel)}|1:{simp(eyer)}\n")
            if happy==1:
                f.write(f"{round((s1)*fps)}|25:{0}|26:{0}|27:{0}|28:{0}\n")
                f.write(f"{round((s1+duration/4)*fps)}|25:{1}|26:{generate_uniform(0.5,1)}|27:{1}|28:{generate_uniform(0.5,1)}\n")
                f.write(f"{round((s1+duration)*fps)}|25:{0}|26:{0}|27:{0}|28:{0}\n")
            else:
                if probability(0.5):
                    f.write(f"{round((s1+duration/5)*fps)}|25:{0}\n")
                    f.write(f"{round((s1+duration/2)*fps)}|25:{generate_uniform(0.5,1)}\n")
                    f.write(f"{round((s1+duration/4*3)*fps)}|25:{0}\n")
                if probability(0.5):
                    f.write(f"{round((s1+duration/5)*fps)}|27:{0}\n")
                    f.write(f"{round((s1+duration/2)*fps)}|27:{generate_uniform(0.5,1)}\n")
                    f.write(f"{round((s1+duration/4*3)*fps)}|27:{0}\n")


        ########eye end!

        #########body
        if happy==5:
            if probability(0.5):
                
                #if round((s1)*fps)>body3[0]+5:
                f.write(f"{round((s1+duration/5)*fps)}|3:{simp(body3)}|19:{simp(leg1l)}|21:{simp(leg3l)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                value4=generate_uniform(10,25)
                leg1l[2]=-round(value4/200,1)
                leg1r[2]=-round(value4/200,1)
                body3[2]=value4/100
                leg3l[6]=round(value4+5,1)
                leg3r[6]=-round(value4+5,1)
                f.write(f"{round((s1+duration/2)*fps)}|3:{simp(body3)}|19:{simp(leg1l)}|21:{simp(leg3l)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                f.write(f"{round((s1+duration/10*7)*fps)}|3:{simp(body3)}|19:{simp(leg1l)}|21:{simp(leg3l)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                leg1l[2]=0
                leg1r[2]=0
                body3[2]=0
                leg3l[6]=0
                leg3r[6]=0
                leg1l[0]=round((s1+duration)*fps)
                leg1r[0]=round((s1+duration)*fps)
                body3[0]=round((s1+duration)*fps)
                leg3l[0]=round((s1+duration)*fps)
                leg3r[0]=round((s1+duration)*fps)
    
                f.write(f"{round((s1+duration/10*9)*fps)}|3:{simp(body3)}|19:{simp(leg1l)}|21:{simp(leg3l)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
        elif action in ["idle","think","common"]:
            if probability(0.3):
                
                if probability(0.3):
                    
                    f.write(f"{round((s1)*fps+2)}|4:{simp(body2)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                    value4=generate_uniform(5,15)
                    
                    leg1r[2]=-round(value4/100,1)
                    body2[6]=-value4
                   
                    leg3r[6]=-round(value4*2,1)
        
                    f.write(f"{round((s1+duration/2)*fps)}|4:{simp(body2)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                    
                    leg1r[2]=0
                    body2[6]=0
                    
                    leg3r[6]=0
                    
                    leg1r[0]=round((s1+duration)*fps)
                    body3[0]=round((s1+duration)*fps)
                    
                    leg3r[0]=round((s1+duration)*fps)
        
                    f.write(f"{round((s1+duration)*fps)}|4:{simp(body2)}|22:{simp(leg1r)}|24:{simp(leg3r)}\n")
                elif probability(0.4):
                    f.write(f"{round((s1)*fps+2)}|4:{simp(body2)}|19:{simp(leg1l)}|21:{simp(leg3l)}\n")
                    value4=generate_uniform(5,15)
                    
                    leg1l[2]=-round(value4/100,1)
                    body2[6]=value4
                   
                    leg3l[6]=round(value4*2,1)
        
                    f.write(f"{round((s1+duration/2)*fps)}|4:{simp(body2)}|19:{simp(leg1l)}|21:{simp(leg3l)}\n")
                    
                    leg1l[2]=0
                    body2[6]=0
                    
                    leg3l[6]=0
                    
                    leg1l[0]=round((s1+duration)*fps)
                    body3[0]=round((s1+duration)*fps)
                    
                    leg3l[0]=round((s1+duration)*fps)
        
                    f.write(f"{round((s1+duration)*fps)}|4:{simp(body2)}|19:{simp(leg1l)}|21:{simp(leg3l)}\n")
                else:
                    f.write(f"{round((s1)*fps+2)}|5:{simp(body1)}\n")
                    value4=generate_uniform(-15,15)
                    
                    
                    body1[6]=value4
                   
                    
        
                    f.write(f"{round((s1+duration/2)*fps)}|5:{simp(body1)}\n")
                    body1[6]=0
                    
                    body1[0]=round((s1+duration)*fps)
                    
        
                    f.write(f"{round((s1+duration)*fps)}|5:{simp(body1)}\n")
            else:
                if probability(0.9):
                
            
                    f.write(f"{round((s1)*fps+1)}|4:{simp(body2)}|5:{simp(body1)}\n")
                    body_t2=body2.copy()
                    body_t1=body1.copy()
                    value4=generate_uniform(-10,10)
                    value5=generate_uniform(-10,10)
                    value6=generate_uniform(-10,10)
                    if probability(0.2):
                        body2[4]+=-value4
                        body1[4]+=-value4
                    if probability(0.4):
                        body2[5]+=-value5
                        body1[5]+=-value5
                    else:
                        body2[6]+=-value6
                        body1[6]+=-value6

        
                    f.write(f"{round((s1+duration/2)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                    f.write(f"{round((s1+duration/4*3)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                    
                    body2=[round((s1+duration)*fps)]+body_t2[1:]
                    body1=[round((s1+duration)*fps)]+body_t1[1:]
        
                    f.write(f"{round((s1+duration)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
        elif happy==1:
            if probability(0.5):
                
            
                f.write(f"{round((s1)*fps+1)}|4:{simp(body2)}|5:{simp(body1)}\n")
                value4=generate_uniform(5,20)
                value5=generate_uniform(-5,5)
                value6=generate_uniform(-5,5)
                
                body2[4]=-value4
                body1[4]=-value4+generate_uniform(-value4,value4)
                if probability(0.7):
                    body2[5]=-value5
                    body1[5]=-value5
                    body2[6]=-value6
                    body1[6]=-value6

    
                f.write(f"{round((s1+duration/2)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                f.write(f"{round((s1+duration/4*3)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                
                body2=[round((s1+duration)*fps),0,0,0,0,0,0,1,1,1]
                body1=[round((s1+duration)*fps),0,0,0,0,0,0,1,1,1]
    
                f.write(f"{round((s1+duration)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")

        else:
            if probability(0.9):
                
            
                f.write(f"{round((s1)*fps+1)}|4:{simp(body2)}|5:{simp(body1)}\n")
                body_t2=body2.copy()
                body_t1=body1.copy()
                value4=generate_uniform(-10,10)
                value5=generate_uniform(-10,10)
                value6=generate_uniform(-10,10)
                if probability(0.2):
                    body2[4]+=-value4
                    body1[4]+=-value4
                if probability(0.4):
                    body2[5]+=-value5
                    body1[5]+=-value5
                else:
                    body2[6]+=-value6
                    body1[6]+=-value6

    
                f.write(f"{round((s1+duration/2)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                f.write(f"{round((s1+duration/4*3)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                
                body2=[round((s1+duration)*fps)]+body_t2[1:]
                body1=[round((s1+duration)*fps)]+body_t1[1:]
    
                f.write(f"{round((s1+duration)*fps)}|4:{simp(body2)}|5:{simp(body1)}\n")
                    
        

            
        if action=="nod":
            f.write(f"{round((s1)*fps+1)}|6{simp(head)}\n")
            value4=generate_uniform(25,45)
            head[4]=-value4
            f.write(f"{round((s1+duration/2)*fps+1)}|6{simp(head)}\n")
            head[4]=0
            f.write(f"{round((s1+duration)*fps-1)}|6{simp(head)}\n")

        elif action=="shake head":
            f.write(f"{round((s1)*fps+1)}|6{simp(head)}\n")
            value4=generate_uniform(25,45)
            if probability(0.5):
                value4=-value4
            head[5]=-value4
            f.write(f"{round((s1+duration/3)*fps)}|6{simp(head)}\n")
            head[5]=value4
            f.write(f"{round((s1+duration/3*2)*fps)}|6{simp(head)}\n")
            head[5]=0
            f.write(f"{round((s1+duration)*fps)}|6{simp(head)}\n")
                
        elif action=="tilt head":
            f.write(f"{round((s1)*fps+1)}|6{simp(head)}\n")
            value4=generate_uniform(10,20)
            if probability(0.5):
                value4=-value4
            head[6]=-value4
            f.write(f"{round((s1+duration/3)*fps+1)}|6{simp(head)}\n")
            value4=generate_uniform(-3,3)
            
            head[6]+=value4
            f.write(f"{round((s1+duration/3*2)*fps+1)}|6{simp(head)}\n")
            head[6]=0
            f.write(f"{round((s1+duration)*fps)}|6{simp(head)}\n")
            
        elif action=="shy":
            f.write(f"{round((s1)*fps+1)}|6{simp(head)}\n")
            value4=generate_uniform(10,20)
            head[4]=-value4
            f.write(f"{round((s1+duration/4)*fps+1)}|6{simp(head)}\n")
            f.write(f"{round((s1+duration/4*3)*fps+1)}|6{simp(head)}\n")
            head[4]=0
            f.write(f"{round((s1+duration)*fps-1)}|6{simp(head)}\n")

        else:
            if probability(0.6):
                
            
                f.write(f"{round((s1)*fps+1)}|6:{simp(head)}\n")
                head_t=head.copy()
                
                value4=generate_uniform(-5,5)
                value5=generate_uniform(-5,5)
                value6=generate_uniform(-5,5)
                if probability(0.2):
                    head[4]+=-value4
                    
                if probability(0.4):
                    head[5]+=-value5
                    
                else:
                    head[6]+=-value6
                    

    
                f.write(f"{round((s1+duration/2)*fps)}|6:{simp(head)}\n")
                
                head=[round((s1+duration)*fps)]+head_t[1:]
                
    
                f.write(f"{round((s1+duration)*fps)-4}|6:{simp(head)}\n")
            elif probability(0.5) and action not in ["think","listen"]:
                head[4:7]=[0,0,0]
                f.write(f"{round((s1+duration)*fps)-4}|6:{simp(head)}\n")

        #ear!!!!!!!!!!!!!!!!
        global scar
        if happy==5:
            if not scar:
                scar=True
                f.write(f"{round((s1)*fps+1)}|7:{simp(ear1r)}|10:{simp(ear1l)}\n")
            else:
                scar=True
                ear2r[6]=0
                ear2l[6]=0
                ear3r[6]=0
                ear3l[6]=0
                f.write(f"{round((s1+duration/2)*fps-3)}|8:{simp(ear2r)}|9:{simp(ear3r)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            value4=-generate_uniform(30,70)
            value5=generate_uniform(30,70)
            ear1r[6]=value4
            ear1l[6]=value5
            f.write(f"{round((s1+duration/2)*fps-3)}|7:{simp(ear1r)}|10:{simp(ear1l)}\n")
            ear1r[6]-=value4/2
            ear1l[6]-=value5/2
            f.write(f"{round((s1+duration)*fps-1)}|7:{simp(ear1r)}|10:{simp(ear1l)}\n")

        elif action=="cover ears":
            if not scar:
                scar=True
                f.write(f"{round((s1)*fps+1)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            else:
                scar=True
            value4=-generate_uniform(70,80)
            value5=generate_uniform(70,80)
            value6=-generate_uniform(30,40)
            value7=generate_uniform(30,40)
            value8=-generate_uniform(30,40)
            value9=generate_uniform(30,40)
            ear1r[6]=-value4
            ear1l[6]=-value5
            ear2r[6]=-value6
            ear2l[6]=-value7
            ear3r[6]=-value8
            ear3l[6]=-value9
            f.write(f"{round((s1+duration/2)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
                
        elif action=="afraid":
            if not scar:
                scar=True
                f.write(f"{round((s1)*fps+1)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            else:
                scar=True
            value4=-generate_uniform(10,20)
            value5=generate_uniform(10,20)
            value6=-generate_uniform(80,110)
            value7=generate_uniform(80,110)
            value8=-generate_uniform(100,130)
            value9=generate_uniform(100,130)
            ear1r[6]=-value4
            ear1l[6]=-value5
            ear2r[6]=-value6
            ear2l[6]=-value7
            ear3r[6]=-value8
            ear3l[6]=-value9
            f.write(f"{round((s1+duration/2)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            
        elif action=="shy":
            if not scar:
                scar=True
                f.write(f"{round((s1)*fps+1)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            else:
                scar=True
            value4=-generate_uniform(30,40)
            value5=generate_uniform(30,40)
            value6=-generate_uniform(30,40)
            value7=generate_uniform(30,40)
            value8=-generate_uniform(30,40)
            value9=generate_uniform(30,40)
            ear1r[6]=-value4
            ear1l[6]=-value5
            ear2r[6]=-value6
            ear2l[6]=-value7
            ear3r[6]=-value8
            ear3l[6]=-value9
            f.write(f"{round((s1+duration/2)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")

        else:
            if scar:
                scar=False
                value4=0
                value5=0
                value6=0
                value7=0
                value8=0
                value9=0
                ear1r[6]=-value4
                ear1l[6]=-value5
                ear2r[6]=-value6
                ear2l[6]=-value7
                ear3r[6]=-value8
                ear3l[6]=-value9
                f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
            else:
                if probability(0.3)and action not in ["listen"]:
               
                    value4=0
                    value5=0
                    value6=0
                    value7=0
                    value8=0
                    value9=0
                    ear1r[6]=-value4
                    ear1l[6]=-value5
                    ear2r[6]=-value6
                    ear2l[6]=-value7
                    ear3r[6]=-value8
                    ear3l[6]=-value9
                    f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")
                else:
                    value4=-generate_uniform(-10,10)
                    value5=generate_uniform(-10,10)
                    value6=generate_uniform(-10,10)
                    value7=generate_uniform(-10,10)
                    value8=generate_uniform(-10,10)
                    value9=generate_uniform(-10,10)
                    ear1r[6]+=value4*2
                    ear1l[6]+=value5*2
                    ear2r[6]+=value6
                    ear2l[6]+=value7
                    ear3r[6]+=value8
                    ear3l[6]+=value9
                    print("ear change")
                    f.write(f"{round((s1+duration)*fps)}|7:{simp(ear1r)}|8:{simp(ear2r)}|9:{simp(ear3r)}|10:{simp(ear1l)}|11:{simp(ear2l)}|12:{simp(ear3l)}\n")

        global hanb
        #arm!!!!!!!!
        if action=="clap hands":
            if not hanb:
                hanb=True
                f.write(f"{round((s1)*fps+1)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                hanb=True
                
            arm2r[4:]=[-65,-35,129,1,1.5,1]
            arm3r[4:]=[-56,85,33,1,1.6,1]
            arm2l[4:]=[-65,35,-129,1,1.5,1]
            arm3l[4:]=[7.8,78,-82,1,1.6,1]
            f.write(f"{round((s1+duration/3)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[5]+=18
            arm2l[5]-=18
            f.write(f"{round((s1+duration/2)*fps)+1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[5]-=18
            arm2l[5]+=18
            f.write(f"{round((s1+duration/4*3)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[4:]=[-65/2,-35/2,129/2,1,1,1]
            arm3r[4:]=[-56/2,85/2,33/2,1,1,1]
            arm2l[4:]=[-65/2,35/2,-129/2,1,1,1]
            arm3l[4:]=[7.8/2,78/2,-82/2,1,1,1]
            
            f.write(f"{round((s1+duration)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")

        elif action=="wave hands":
            if not hanb:
                hanb=True
                f.write(f"{round((s1)*fps+1)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                hanb=True
            value4=generate_uniform(15,35)
            value5=generate_uniform(15,35)
            arm2r[4:]=[0,0,0,1,1,1]
            arm3r[4:]=[0,0,0,1,1,1]
            arm2l[4:]=[0,0,0,1,1,1]
            arm3l[4:]=[0,0,0,1,1,1]
            f.write(f"{round((s1+duration/2)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[6]-=value4
            arm2l[6]+=value5
            f.write(f"{round((s1+duration/10*7)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[6]+=value4
            arm2l[6]-=value5
            f.write(f"{round((s1+duration/10*9)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")

        elif action=="cross waist":
            if not hanb:
                hanb=True
                f.write(f"{round((s1)*fps+1)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                hanb=True
            value4=generate_uniform(30,40)
            value5=generate_uniform(30,40)
            value6=generate_uniform(70,90)
            value7=generate_uniform(70,90)
            arm2r[4:]=[0,0,0,1,1,1]
            arm3r[4:]=[0,0,0,1,1,1]
            arm2l[4:]=[0,0,0,1,1,1]
            arm3l[4:]=[0,0,0,1,1,1]
            f.write(f"{round((s1+duration/4)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[6]+=value4
            arm2l[6]-=value5
            arm3r[6]+=value6
            arm3l[6]-=value7
            f.write(f"{round((s1+duration/2)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            f.write(f"{round((s1+duration)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
        elif action in ["cover ears","afraid","shy"]:
            if not hanb:
                hanb=True
                f.write(f"{round((s1)*fps+1)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                hanb=True
            value4=-generate_uniform(25,35)
            value5=-generate_uniform(25,35)
            value6=-generate_uniform(15,25)
            value7=-generate_uniform(15,25)
            arm2r[4:]=[0,0,0,1,1,1]
            arm3r[4:]=[0,0,0,1,1,1]
            arm2l[4:]=[0,0,0,1,1,1]
            arm3l[4:]=[0,0,0,1,1,1]
            f.write(f"{round((s1+duration/4)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[6]+=value4
            arm2l[6]-=value5
            arm3r[6]+=value6
            arm3l[6]-=value7
            f.write(f"{round((s1+duration/2)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            f.write(f"{round((s1+duration)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
        
        elif action=="cheer":
            if not hanb:
                hanb=True
                f.write(f"{round((s1)*fps+1)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                hanb=True
                
            arm2r[4:]=[0,0,0,1,1,1]
            arm3r[4:]=[0,0,0,1,1,1]
            arm2l[4:]=[0,0,0,1,1,1]
            arm3l[4:]=[0,0,0,1,1,1]
            f.write(f"{round((s1+duration/3)*fps)}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[4:]=[0,0,-generate_uniform(20,40),1,1.1,1]
            arm3r[4:]=[0,0,0,1,1.1,1]
            arm2l[4:]=[0,0,generate_uniform(20,40),1,1.1,1]
            arm3l[4:]=[0,0,0,1,1.1,1]
            f.write(f"{round((s1+duration/2)*fps)+1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            
            f.write(f"{round((s1+duration/4*3)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            arm2r[4:]=[0,0,0,1,1,1]
            arm3r[4:]=[0,0,0,1,1,1]
            arm2l[4:]=[0,0,0,1,1,1]
            arm3l[4:]=[0,0,0,1,1,1]
            
            f.write(f"{round((s1+duration)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
        else:
            if hanb:
                hanb=False
                arm2r[4:]=[0,0,50,1,1,1]
                arm3r[4:]=[0,0,20,1,1,1]
                arm2l[4:]=[0,0,-50,1,1,1]
                arm3l[4:]=[0,0,-20,1,1,1]
                f.write(f"{round((s1+duration)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
            else:
                if probability(0.3) and action not in ["listen","think"]:
                    arm2r[4:]=[0,0,50,1,1,1]
                    arm3r[4:]=[0,0,20,1,1,1]
                    arm2l[4:]=[0,0,-50,1,1,1]
                    arm3l[4:]=[0,0,-20,1,1,1]
                    f.write(f"{round((s1+duration)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
                else:
                    value4=-generate_uniform(-10,10)
                    value5=generate_uniform(-10,10)
                    value6=generate_uniform(-10,10)
                    value7=generate_uniform(-10,10)
                    
                    arm2r[6]+=value6/2
                    arm2l[6]+=value7/2
                    arm3r[6]+=value4/2
                    arm3l[6]+=value5/2
                
                    f.write(f"{round((s1+duration)*fps)-1}|14:{simp(arm2r)}|15:{simp(arm3r)}|17:{simp(arm2l)}|18:{simp(arm3l)}\n")
        global lip_common
        if lip_data!=None:
            lip_common=False
            list1=[]
            list2=[]
            
            for frame in lip_data['mouthCues']:
                ti = frame['end']-frame['start']
                shape = frame['value']
                values = mouth_shape_to_values(shape)
                s1+=ti
                list1+=[s1]
                list2+=[values]
            for i in range(len(list1)):
                f.write(f"{round((list1[i])*fps)}|29:{list2[i][0]}|30:{list2[i][1]}|31:{list2[i][2]}\n")
        else:
            if action=="idle" and lip_common==False:
                lip_common=True
                f.write(f"{round((s1+duration)*fps)}|29:{0.8}|30:{0.6}|31:{0}\n")

        acti_t+=duration
        print(round((s1)*fps))
    return acti_t
def thread1_worker():
    """线程1的工作函数"""
    global action,idle,listen,think,action_queue,index_sen,folder_path
    text = "[wave hands]Hello my friend. [cheer]Nice to meet you. [common]Do you have any questions? [cheer]I am willing to answer anything."
    actions, sentences = extract(text)

    for i, (current_action, sentence) in enumerate(zip(actions, sentences)):
        # 生成语音文件
        wav_file = folder_path+f"output{index_sen}_{i}.wav"
        duration = asyncio.run(generate_wav(sentence, wav_file))
        
        # 生成口型文件
        lip_file = folder_path+f"lip_sync{index_sen}_{i}.json"
        generate_lip_sync(wav_file, lip_file)
        
        # 更新全局变量
        with global_lock:
            action_queue.append(current_action)
            think=False
            action=True
            
            
            
        
        print(f"Thread1: Generated {wav_file} and {lip_file} for action '{current_action}'")
    time.sleep(1)
    with global_lock:
        idle=True
        action = False
        
    
    while True:
        user_input=get_audio()
        print(user_input,"user input")
        messages.append({"role": "user", "content": user_input})
        text = (get_response(messages).output.choices[0].message.content).split("\n")[-1]
        print(text)
        print(type(text))
        index_sen+=1
        actions, sentences = extract(text)
        print(actions, sentences)
        action_queue=[]
        for i, (current_action, sentence) in enumerate(zip(actions, sentences)):
            # 生成语音文件
            wav_file = folder_path+f"output{index_sen}_{i}.wav"
            duration = asyncio.run(generate_wav(sentence, wav_file))
            
            # 生成口型文件
            lip_file = folder_path+f"lip_sync{index_sen}_{i}.json"
            generate_lip_sync(wav_file, lip_file)
            
            # 更新全局变量
            with global_lock:
                action_queue.append(current_action)
                action=True
                think=False
                
                
                
                
            
            print(f"Thread1: Generated {wav_file} and {lip_file} for action '{current_action}'")
        time.sleep(1)
        with global_lock:
            idle=True
            action = False
            


        
            

def thread2_worker():
    """线程2的工作函数"""
    global action,idle,listen,think,index_sen

    i= 0


    while not (action):
        time.sleep(0.1)
    
    ori_t=time.time()
    acti_t=time.time()
    
    while True:
        with global_lock:
            if i<len(action_queue):
                
                current_action = action_queue[i]
                wav_file = f"output{index_sen}_{i}.wav"
                lip_file=folder_path+f"lip_sync{index_sen}_{i}.json"
                        # 处理口型数据 - 直接从文件读取，不需要重新生成
                # try:
                with open(lip_file, 'r') as f:
                    lip_data = json.load(f)
                
                
                # 写入content.txt
                # with open(action_file_path, "a") as f:
    
                #     f.write(f"{round((acti_t-ori_t)*fps)}|{wav_file}\n")
                acti_t=generation_action(acti_t,ori_t,current_action,lip_data,wav_file)
                
                print(f"Thread2: Processed lip sync for action '{current_action}'")
                # except Exception as e:
                #     print(f"Thread2: Error processing {lip_file}: {str(e)}")
                
                i +=1
            elif action:
                # 没有新数据但action=True，生成等待动作
                #print(acti_t,time.time())
                if acti_t<time.time():
                    acti_t=generation_action(acti_t,ori_t,"common")
                
            
            else:
                break
        
        time.sleep(0.1)  # 避免忙等待

    while True:
        i=0
        while not (action):
            if idle==True:
                if acti_t<time.time():
                    acti_t=generation_action(acti_t,ori_t,"idle")
            elif listen==True:
                if acti_t<time.time():
                    acti_t=generation_action(acti_t,ori_t,"listen")
                    print("listen!!!!")
            elif think==True:
                if acti_t<time.time():
                    acti_t=generation_action(acti_t,ori_t,"think")
            else:
                print("!!!!!!!!!!possible mistake")
                if acti_t<time.time():
                    acti_t=generation_action(acti_t,ori_t,"think")
            time.sleep(0.5)
            print((acti_t-ori_t)*fps,(time.time()-ori_t)*fps)
        
        while True:
            print(action,idle,listen,think,index_sen)
            with global_lock:
                if i<len(action_queue):
                    
                    current_action = action_queue[i]
                    wav_file = f"output{index_sen}_{i}.wav"
                    lip_file=folder_path+f"lip_sync{index_sen}_{i}.json"
                            # 处理口型数据 - 直接从文件读取，不需要重新生成
                    
                    try:
                        with open(lip_file, 'r') as f:
                            lip_data = json.load(f)
                        
                        
    
                    
                        acti_t=generation_action(acti_t,ori_t,current_action,lip_data,wav_file)
                        wav_file=""
                        print(f"Thread2: Processed lip sync for action '{current_action}'")
                    except Exception as e:
                        print(f"Thread2: Error processing {lip_file}: {str(e)}")
                    
                    i +=1
                elif action:
                    # 没有新数据但action=True，生成等待动作
                    #print(acti_t,time.time())
                    if acti_t<time.time():
                        acti_t=generation_action(acti_t,ori_t,"common")
                    
                
                else:
                    break
            
            time.sleep(0.1)  # 避免忙等待



import os
from datetime import datetime

def create_folder_with_current_time(data_folder='data'):
    # 获取当前时间并格式化为 'YYYY-MM-DD_HH' 形式
    current_time = datetime.now().strftime('%Y-%m-%d_%H')
    # 创建以当前时间命名的文件夹路径
    new_folder_path = os.path.join(data_folder, current_time)

    # 检查数据文件夹是否存在，不存在则创建
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    # 创建以当前时间命名的文件夹
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
        print(f"文件夹 '{new_folder_path}' 创建成功.")
    else:
        print(f"文件夹 '{new_folder_path}' 已存在.")

    return new_folder_path




def main():
    # 示例文本
    global folder_path,action_file_path
    
    # 清空content.txt
    open(action_file_path, "w").close()
    folder_path = create_folder_with_current_time()+"\\"
    print(f"文件夹路径是: {folder_path}")
    # 创建并启动线程
    action_file_path="content.txt"
    t1 = threading.Thread(target=thread1_worker)
    t2 = threading.Thread(target=thread2_worker)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    print("All processing completed!")

if __name__ == "__main__":
    main()