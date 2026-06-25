import os

def create_video_processor():
    content = '''import os
import subprocess
import json
import httpx
from datetime import datetime
import cv2

def detect_scenes(video_path, threshold=30.0):
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    
    scene_list = scene_manager.get_scene_list()
    video_manager.release()
    
    scenes = []
    for i, scene in enumerate(scene_list):
        start_time = scene[0].get_seconds()
        end_time = scene[1].get_seconds()
        scenes.append({
            "index": i + 1,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time
        })
    
    return scenes

def split_video(input_path, output_dir, scenes, creator_name):
    os.makedirs(output_dir, exist_ok=True)
    
    today = datetime.now().strftime("%m%d")
    base_name = creator_name
    
    output_files = []
    
    for scene in scenes:
        scene_num = scene["index"]
        start_time = scene["start_time"]
        end_time = scene["end_time"]
        
        output_filename = f"{today}{base_name}-{scene_num}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-strict", "experimental",
            "-y",
            output_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        output_files.append({
            "scene_number": scene_num,
            "file_path": output_path,
            "duration": scene["duration"]
        })
    
    return output_files

def extract_keyframes(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    keyframe_indices = [
        0,
        total_frames // 2,
        total_frames - 1
    ]
    
    keyframe_paths = []
    
    for idx in keyframe_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            timestamp = idx / fps
            frame_path = os.path.join(output_dir, f"frame_{int(timestamp)}.jpg")
            cv2.imwrite(frame_path, frame)
            keyframe_paths.append(frame_path)
    
    cap.release()
    return keyframe_paths

def encode_image_base64(image_path):
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_with_ai(keyframe_paths):
    images_base64 = [encode_image_base64(fp) for fp in keyframe_paths]
    
    prompt = """分析图片内容，根据视频场景内容生成合适的分类和标签。

输出JSON格式。

格式如下：

{
  "category": "根据内容生成的分类名称",
  "product_category": "产品大类，如猫粮、护肤品、服装等",
  "tags": [
    "标签1",
    "标签2",
    "标签3",
    "标签4",
    "标签5"
  ]
}

要求：
- category为一级分类，根据视频内容动态生成
- product_category为产品大类
- tags生成3-10个，涵盖视频中的关键元素、人物、场景、动作等
- 禁止输出解释文本
- 仅输出JSON
"""
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt}
            ] + [{"type": "image", "image": img} for img in images_base64]
        }
    ]
    
    try:
        response = httpx.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen2.5vl:7b",
                "messages": messages,
                "stream": False
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        
        content = result["message"]["content"]
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "category": "未分类",
                "product_category": "其他",
                "tags": ["未识别"]
            }
    except Exception as e:
        return {
            "category": "未分类",
            "product_category": "其他",
            "tags": ["未识别"]
        }

def get_creator_name(filename):
    name = os.path.splitext(filename)[0]
    if "(" in name:
        name = name.split("(")[0].strip()
    return name

def get_today_date():
    return datetime.now().strftime("%m%d")
'''
    with open(r"C:\Users\Neko\Desktop\素材拆分与分类\backend\utils\video_processor.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("video_processor.py created")

if __name__ == "__main__":
    create_video_processor()
