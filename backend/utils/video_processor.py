import os
import subprocess
import json
import httpx
from datetime import datetime
import cv2
import numpy as np

def detect_scenes(video_path, threshold=27.0):
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    
    try:
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()
    finally:
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
    
    if not scenes:
        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            scenes = [{
                "index": 1,
                "start_time": 0,
                "end_time": duration,
                "duration": duration
            }]
        cap.release()
    
    return scenes

def cv2_imwrite(filename, img):
    try:
        import os
        if isinstance(filename, str):
            filename = filename.encode('utf-8').decode('utf-8')
        result, data = cv2.imencode('.jpg', img)
        if result:
            with open(filename, 'wb') as f:
                f.write(data)
            return os.path.exists(filename)
        return False
    except Exception as e:
        return False

def extract_keyframes(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames < 3:
        keyframe_indices = [0]
    else:
        keyframe_indices = [0, total_frames // 2, total_frames - 1]
    
    keyframe_paths = []
    frame_counter = 0
    
    for idx in keyframe_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_dir, f"frame_{frame_counter}.jpg")
            success = cv2_imwrite(frame_path, frame)
            if success and os.path.exists(frame_path):
                keyframe_paths.append(frame_path)
                frame_counter += 1
    
    cap.release()
    return keyframe_paths

def encode_image_base64(image_path):
    import base64
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def analyze_with_ai(keyframe_paths):
    if not keyframe_paths:
        return {"category": "uncategorized", "product_category": "other", "tags": ["unrecognized"]}
    
    try:
        # 构建包含所有图片的提示
        prompt_parts = []
        
        for fp in keyframe_paths:
            if os.path.exists(fp):
                img_base64 = encode_image_base64(fp)
                img_data_url = f"data:image/jpeg;base64,{img_base64}"
                prompt_parts.append(img_data_url)
        
        if not prompt_parts:
            return {"category": "uncategorized", "product_category": "other", "tags": ["unrecognized"]}
        
        prompt_text = """请分析这些视频帧图片的内容，并以JSON格式输出：
{"category": "...", "product_category": "...", "tags": ["..."]}

category选项：product_showcase, lifestyle, cooking, beauty, fitness, uncategorized
product_category选项：cosmetics, food, electronics, clothing, other
tags：描述性标签列表（用中文）"""
        
        # 组合图片和提示
        full_content = prompt_text + "\n\n" + "\n".join(prompt_parts)
        
        messages = [{
            "role": "user", 
            "content": full_content
        }]
        
        response = httpx.post(
            "http://localhost:11434/api/chat",
            json={"model": "qwen2.5vl:7b", "messages": messages, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        content = result["message"]["content"]
        
        try:
            return json.loads(content)
        except:
            return {"category": "uncategorized", "product_category": "other", "tags": ["unrecognized"]}
    
    except Exception as e:
        return {"category": "uncategorized", "product_category": "other", "tags": ["unrecognized"]}

def get_creator_name(filename):
    name = os.path.splitext(filename)[0]
    if "(" in name:
        name = name.split("(")[0].strip()
    return name

def get_today_date():
    return datetime.now().strftime("%m%d")
