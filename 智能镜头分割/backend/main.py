import os
import shutil
import logging
import base64
import requests
import json
import asyncio
import aiohttp
import hashlib
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLIP_AVAILABLE = False
try:
    from PIL import Image
    import torch
    import open_clip
    CLIP_AVAILABLE = True
    logger.info("OpenCLIP 可用")
except ImportError:
    logger.warning("OpenCLIP 不可用，将使用Qwen作为默认分类器")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="智能镜头分割工具")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
TRAINING_DIR = os.path.join(DATA_DIR, "训练集")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TRAINING_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
logger.info(f"Data directory: {DATA_DIR}")
logger.info(f"Training directory: {TRAINING_DIR}")
logger.info(f"Cache directory: {CACHE_DIR}")

app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

import database as db
db.init_db()

tasks = []
current_task_id = 0

OLLAMA_HOST = "http://localhost:11434"

CURRENT_PRODUCT = None

CLIP_MODEL = None
CLIP_PREPROCESS = None
DEVICE = None

def init_clip():
    global CLIP_MODEL, CLIP_PREPROCESS, DEVICE
    if not CLIP_AVAILABLE:
        return False
    try:
        DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        CLIP_MODEL, _, CLIP_PREPROCESS = open_clip.create_model_and_transforms('ViT-B-32', pretrained='openai', device=DEVICE)
        logger.info(f"OpenCLIP模型加载成功，使用设备: {DEVICE}")
        return True
    except Exception as e:
        logger.error(f"OpenCLIP模型加载失败: {e}")
        return False

def get_video_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_cache_dir(video_md5):
    return os.path.join(CACHE_DIR, video_md5[:2], video_md5)

def load_cached_scenes(video_path):
    try:
        video_md5 = get_video_md5(video_path)
        cache_dir = get_cache_dir(video_md5)
        scenes_file = os.path.join(cache_dir, "scenes.json")
        if os.path.exists(scenes_file):
            with open(scenes_file, "r", encoding="utf-8") as f:
                scenes = json.load(f)
            logger.info(f"已加载缓存场景: {len(scenes)} 个")
            return scenes
    except Exception as e:
        logger.error(f"加载缓存场景失败: {e}")
    return None

def save_cached_scenes(video_path, scenes):
    try:
        video_md5 = get_video_md5(video_path)
        cache_dir = get_cache_dir(video_md5)
        os.makedirs(cache_dir, exist_ok=True)
        scenes_file = os.path.join(cache_dir, "scenes.json")
        with open(scenes_file, "w", encoding="utf-8") as f:
            json.dump(scenes, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存缓存场景")
    except Exception as e:
        logger.error(f"保存缓存场景失败: {e}")

def load_cached_categories(video_path):
    try:
        video_md5 = get_video_md5(video_path)
        cache_dir = get_cache_dir(video_md5)
        labels_file = os.path.join(cache_dir, "labels.json")
        if os.path.exists(labels_file):
            with open(labels_file, "r", encoding="utf-8") as f:
                labels = json.load(f)
            logger.info(f"已加载缓存分类")
            return labels
    except Exception as e:
        logger.error(f"加载缓存分类失败: {e}")
    return None

def save_cached_categories(video_path, categories):
    try:
        video_md5 = get_video_md5(video_path)
        cache_dir = get_cache_dir(video_md5)
        os.makedirs(cache_dir, exist_ok=True)
        labels_file = os.path.join(cache_dir, "labels.json")
        with open(labels_file, "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        logger.info(f"已保存缓存分类")
    except Exception as e:
        logger.error(f"保存缓存分类失败: {e}")
CURRENT_CATEGORY_SET = None

PREDEFINED_CATEGORIES = []

CLIP_CONFIDENCE_THRESHOLD = 0.5

def clip_classify(image_path, categories):
    if not CLIP_AVAILABLE or CLIP_MODEL is None:
        return None, 0.0
    
    try:
        image = CLIP_PREPROCESS(Image.open(image_path)).unsqueeze(0).to(DEVICE)
        text = open_clip.tokenize(categories).to(DEVICE)
        
        with torch.no_grad():
            image_features = CLIP_MODEL.encode_image(image)
            text_features = CLIP_MODEL.encode_text(text)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            probs = (100.0 * image_features @ text_features.T).softmax(dim=-1).cpu().numpy()[0]
        
        max_idx = probs.argmax()
        confidence = probs[max_idx]
        category = categories[max_idx]
        
        return category, confidence
    except Exception as e:
        logger.error(f"OpenCLIP分类失败: {e}")
        return None, 0.0

def classify_with_clip_and_qwen(image_path, categories):
    if not categories or len(categories) == 0:
        categories = ["产品展示", "人物特写", "场景全景", "操作演示", "对比测评", "使用教程", "生活日常", "美食制作", "运动健身", "旅行风景"]
    
    clip_category, confidence = clip_classify(image_path, categories)
    
    if clip_category is not None and confidence >= CLIP_CONFIDENCE_THRESHOLD:
        logger.debug(f"CLIP分类成功: {clip_category} (置信度: {confidence:.2f})")
        
        if clip_category == "床上吃东西看电视剧" and confidence < 0.7:
            logger.debug(f"CLIP对'床上吃东西看电视剧'置信度低 ({confidence:.2f})，使用Qwen二次确认")
            return analyze_image_with_ai(image_path, categories)
        
        return clip_category
    
    logger.debug(f"CLIP置信度不足 ({confidence:.2f})，使用Qwen分类")
    return analyze_image_with_ai(image_path, categories)

def set_current_product(product_name):
    global CURRENT_PRODUCT
    CURRENT_PRODUCT = product_name
    if product_name:
        product_train_dir = os.path.join(TRAINING_DIR, product_name)
        os.makedirs(product_train_dir, exist_ok=True)
        logger.info(f"当前产品: {product_name}")

def set_current_category_set(set_name):
    global CURRENT_CATEGORY_SET
    CURRENT_CATEGORY_SET = set_name
    logger.info(f"当前品类: {set_name}")

def get_training_dir(product_name=None):
    if product_name:
        return os.path.join(TRAINING_DIR, product_name)
    elif CURRENT_PRODUCT:
        return os.path.join(TRAINING_DIR, CURRENT_PRODUCT)
    return TRAINING_DIR

def get_training_samples(product_name=None):
    train_dir = get_training_dir(product_name)
    samples = {}
    if os.path.exists(train_dir):
        for category in os.listdir(train_dir):
            cat_dir = os.path.join(train_dir, category)
            if os.path.isdir(cat_dir):
                samples[category] = [f for f in os.listdir(cat_dir) if f.endswith('.jpg')]
    return samples

def get_all_products():
    if os.path.exists(TRAINING_DIR):
        return [d for d in os.listdir(TRAINING_DIR) if os.path.isdir(os.path.join(TRAINING_DIR, d))]
    return []

def build_prompt(categories):
    if not categories or len(categories) == 0:
        categories = ["产品展示", "人物特写", "场景全景", "操作演示", "对比测评", "使用教程", "生活日常", "美食制作", "运动健身", "旅行风景"]
    
    has_other = "其他" in categories
    
    categories_text = "\n".join([f"- {cat}" for cat in categories])
    
    prompt = f"""请仔细分析图片内容，从以下分类列表中选择最贴切的一个：
{categories_text}

分类判断规则：
- 坐着办公：人坐在桌子前使用电脑/办公设备工作
- 坐着玩手机：人坐着但使用手机（不是办公场景）
- 床上吃东西看电视剧：在床上或沙发上，有食物或正在看电视
- 挡板放平板：平板放在桌子挡板上
- 站着办公：人站立使用电脑办公
- 阳台办公：在阳台环境办公
- 升降：桌子正在升降过程
- 90度折叠/96度双面翻转：桌子正在折叠或翻转
- 拆装/拆装挡板：正在安装或拆卸桌子/挡板
- 吃东西：正在吃东西的动作
- 宠物：有宠物出现
- 空镜：没有人物，只有场景或物品
- 桌子展示：展示桌子产品本身
- 桌腿特写：桌子腿部的特写镜头
- 桌子稳定：展示桌子稳定性的镜头

要求：
1. 仔细观察人物动作和场景环境
2. 注意区分相似分类（如坐着办公 vs 坐着玩手机）
3. 选择最符合图片整体内容的分类
4. 只返回分类名称，不要添加任何其他文字"""
    
    return prompt, categories, has_other

def analyze_image_with_ai(image_path, categories=None):
    try:
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        prompt, valid_categories, has_other = build_prompt(categories)

        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "qwen2.5vl:7b",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False,
                "temperature": 0.1,
                "num_ctx": 2048
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            category = result.get("response", "").strip()
            if category in valid_categories:
                return category
            else:
                logger.warning(f"AI返回未知分类: {category}，将使用{'其他' if has_other else '最接近的分类'}")
                return "其他" if has_other else valid_categories[0] if valid_categories else "其他"
        else:
            logger.error(f"Ollama API调用失败: {response.status_code}")
            return "其他" if has_other else (valid_categories[0] if valid_categories else "其他")
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        return "其他" if has_other else (valid_categories[0] if valid_categories else "其他")

def get_video_duration(video_path):
    try:
        import subprocess
        cmd = ["ffmpeg", "-i", video_path]
        result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
        output = result.stdout
        import re
        match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", output)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return 1.0
    except Exception as e:
        logger.error(f"获取视频时长失败: {e}")
        return 1.0

def extract_multiple_keyframes(video_path, num_frames=3):
    try:
        frame_paths = []
        duration = get_video_duration(video_path)
        
        if duration <= 1.0:
            timestamps = [0.5]
        else:
            timestamps = [(i + 1) * duration / (num_frames + 1) for i in range(num_frames)]
        
        for i, ts in enumerate(timestamps):
            frame_path = video_path.replace('.mp4', f'_frame_{i}.jpg')
            cmd = [
                "ffmpeg", "-i", video_path,
                "-ss", str(ts),
                "-vframes", "1",
                "-q:v", "2",
                "-y", frame_path
            ]
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(frame_path):
                frame_paths.append(frame_path)
        
        return frame_paths
    except Exception as e:
        logger.error(f"提取多帧失败: {e}")
        return []

def classify_with_voting(scene, effective_categories, num_frames=3):
    scene_path = scene["path"]
    frame_paths = extract_multiple_keyframes(scene_path, num_frames)
    
    if not frame_paths:
        frame_path = scene_path.replace('.mp4', '_frame.jpg')
        success = extract_keyframe(scene_path, frame_path)
        if success and os.path.exists(frame_path):
            category = analyze_image_with_ai(frame_path, effective_categories)
            os.remove(frame_path)
            return category
        return "其他"
    
    categories = []
    for frame_path in frame_paths:
        if os.path.exists(frame_path):
            category = analyze_image_with_ai(frame_path, effective_categories)
            categories.append(category)
            os.remove(frame_path)
    
    if not categories:
        return "其他"
    
    category_counts = {}
    for cat in categories:
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    max_count = max(category_counts.values())
    top_categories = [cat for cat, count in category_counts.items() if count == max_count]
    
    if len(top_categories) == 1:
        return top_categories[0]
    else:
        if "其他" in top_categories and len(top_categories) > 1:
            top_categories.remove("其他")
            if top_categories:
                return top_categories[0]
        return top_categories[0]

def extract_keyframe(video_path, output_path):
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", "0.5",
            "-vframes", "1",
            "-q:v", "2",
            "-y", output_path
        ]
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        logger.error(f"提取关键帧失败: {e}")
        return False

def get_today_date():
    return datetime.now().strftime("%m%d%H%M%S")

@app.post("/api/upload")
async def upload_videos(files: List[UploadFile] = File(...), output_dir: Optional[str] = None):
    global current_task_id
    current_task_id += 1
    
    task_name = f"input_镜头分割_{get_today_date()}"
    task_id = current_task_id
    
    try:
        final_output_dir = os.path.join(DATA_DIR, "输出分类")
        os.makedirs(final_output_dir, exist_ok=True)
        
        task_dir = os.path.join(DATA_DIR, "tasks", task_name)
        os.makedirs(task_dir, exist_ok=True)
        
        video_paths = []
        for file in files:
            if not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
                continue
            
            video_path = os.path.join(task_dir, file.filename)
            with open(video_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            video_paths.append(video_path)
        
        db_task_id = db.create_task(task_name, CURRENT_PRODUCT, final_output_dir)
        
        task = {
            "id": task_id,
            "db_id": db_task_id,
            "name": task_name,
            "status": "pending",
            "video_count": len(video_paths),
            "videos": video_paths,
            "output_dir": final_output_dir,
            "scenes": [],
            "logs": ["任务创建成功，共 {} 个视频".format(len(video_paths))],
            "created_at": datetime.now().isoformat()
        }
        tasks.append(task)
        
        return {"task_id": task_id, "task_name": task_name, "message": "上传成功"}
    
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process/{task_id}")
async def process_video(task_id: int, skip_ai: bool = Query(True, description="是否跳过AI分类"), threshold: float = Query(27.0, description="场景检测阈值"), frame_precision: bool = Query(True, description="是否启用帧精确模式"), categories: Optional[List[str]] = Query(None, description="用户自定义分类列表"), fast_mode: bool = Query(False, description="是否启用极速模式(直接复制流，不重新编码)")):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    import time
    start_total = time.time()
    
    task["status"] = "processing"
    task["logs"].append("=" * 50)
    task["logs"].append(f"【任务开始】任务ID: {task_id}")
    task["logs"].append(f"【任务名称】{task['name']}")
    task["logs"].append(f"【视频数量】{len(task['videos'])}")
    task["logs"].append(f"【输出目录】{task['output_dir']}")
    task["logs"].append(f"【AI分类】{'已禁用（快速模式）' if skip_ai else '已启用'}")
    task["logs"].append(f"【拆分阈值】{threshold} (值越低拆分越细，值越高拆分越少)")
    task["logs"].append(f"【帧精确模式】{'已启用（推荐）' if frame_precision else '已禁用'}")
    task["logs"].append(f"【极速模式】{'已启用（直接复制，速度快）' if fast_mode else '已禁用（重新编码，质量高）'}")
    task["logs"].append("=" * 50)
    
    task["fast_mode"] = fast_mode
    
    all_scenes = []
    total_scenes = 0
    
    import multiprocessing
    num_processes = max(1, min(multiprocessing.cpu_count() - 2, len(task["videos"])))
    task["logs"].append(f"【并行处理】使用 {num_processes} 个进程")
    
    def process_single_video(args):
        import subprocess
        import time
        video_idx, video_path, task_output_dir, threshold_val, frame_precision_val, fast_mode_val = args
        video_logs = []
        video_scenes = []
        
        video_start = time.time()
        video_name = os.path.basename(video_path)
        creator_name = os.path.splitext(video_name)[0]
        if "(" in creator_name:
            creator_name = creator_name.split("(")[0].strip()
        
        video_size = os.path.getsize(video_path) / (1024 * 1024)
        video_logs.append(f"【视频 {video_idx + 1}】开始处理: {video_name}")
        video_logs.append(f"  ├─ 文件大小: {video_size:.2f} MB")
        video_logs.append(f"  ├─ 达人名称: {creator_name}")
        
        detect_start = time.time()
        scenes = detect_scenes(video_path, threshold_val, frame_precision_val)
        detect_time = time.time() - detect_start
        video_logs.append(f"  【场景检测】阈值: {threshold_val}，帧精确: {'是' if frame_precision_val else '否'}，检测到 {len(scenes)} 个场景，耗时: {detect_time:.2f} 秒")
        
        scene_output_dir = os.path.join(task_output_dir, creator_name)
        os.makedirs(scene_output_dir, exist_ok=True)
        video_logs.append(f"  【输出目录】{scene_output_dir}")
        
        today = datetime.now().strftime("%m%d")
        
        for scene in scenes:
            scene_num = scene["index"]
            scene_start_time_val = scene["start_time"]
            scene_end_time_val = scene["end_time"]
            duration = scene["duration"]
            
            final_filename = f"{today}{creator_name}-{scene_num}.mp4"
            final_path = os.path.join(scene_output_dir, final_filename)
            
            if frame_precision_val and "start_frame" in scene and "end_frame" in scene:
                start_frame = scene["start_frame"]
                end_frame = scene["end_frame"]
                
                gpu_test = subprocess.run(["ffmpeg", "-encoders"], capture_output=True)
                if b"h264_nvenc" in gpu_test.stdout:
                    cmd = [
                        "ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-hwaccel", "cuda",
                        "-i", video_path,
                        "-vf", f"select='between(n,{start_frame},{end_frame-1})'",
                        "-vsync", "0",
                        "-c:v", "h264_nvenc",
                        "-preset", "fast",
                        "-crf", "23",
                        "-threads", "auto",
                        "-movflags", "+faststart",
                        "-an",
                        "-y", final_path
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-i", video_path,
                        "-vf", f"select='between(n,{start_frame},{end_frame-1})'",
                        "-vsync", "0",
                        "-c:v", "libx264",
                        "-preset", "ultrafast",
                        "-crf", "28",
                        "-threads", "auto",
                        "-movflags", "+faststart",
                        "-an",
                        "-y", final_path
                    ]
            elif fast_mode_val:
                cmd = [
                    "ffmpeg", "-hide_banner", "-loglevel", "error",
                    "-ss", str(scene_start_time_val),
                    "-i", video_path,
                    "-to", str(scene_end_time_val),
                    "-c", "copy",
                    "-an",
                    "-avoid_negative_ts", "make_zero",
                    "-y", final_path
                ]
            else:
                gpu_test = subprocess.run(["ffmpeg", "-encoders"], capture_output=True)
                if b"h264_nvenc" in gpu_test.stdout:
                    cmd = [
                        "ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-hwaccel", "cuda",
                        "-ss", str(scene_start_time_val),
                        "-i", video_path,
                        "-to", str(scene_end_time_val),
                        "-c:v", "h264_nvenc",
                        "-preset", "fast",
                        "-crf", "23",
                        "-threads", "auto",
                        "-movflags", "+faststart",
                        "-an",
                        "-avoid_negative_ts", "make_zero",
                        "-y", final_path
                    ]
                else:
                    cmd = [
                        "ffmpeg", "-hide_banner", "-loglevel", "error",
                        "-ss", str(scene_start_time_val),
                        "-i", video_path,
                        "-to", str(scene_end_time_val),
                        "-c:v", "libx264",
                        "-preset", "ultrafast",
                        "-crf", "28",
                        "-threads", "auto",
                        "-movflags", "+faststart",
                        "-an",
                        "-avoid_negative_ts", "make_zero",
                        "-y", final_path
                    ]
            
            ffmpeg_start = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True)
            ffmpeg_time = time.time() - ffmpeg_start
            
            if result.returncode == 0 and os.path.exists(final_path):
                scene_size = os.path.getsize(final_path) / 1024
                video_logs.append(f"    ✓ 场景 {scene_num}: {scene_start_time_val:.3f}s -> {scene_end_time_val:.3f}s (时长: {duration:.3f}s)")
                video_logs.append(f"      ├─ 文件: {final_filename}")
                video_logs.append(f"      ├─ 大小: {scene_size:.2f} KB")
                video_logs.append(f"      └─ 耗时: {ffmpeg_time:.2f}s")
                
                video_scenes.append({
                    "task_id": task_id,
                    "video_name": video_name,
                    "creator_name": creator_name,
                    "scene_number": scene_num,
                    "filename": final_filename,
                    "path": final_path,
                    "start_time": scene_start_time_val,
                    "end_time": scene_end_time_val,
                    "duration": duration,
                    "category": "其他",
                    "selected": False
                })
            else:
                video_logs.append(f"    ✗ 场景 {scene_num} 处理失败")
        
        video_time = time.time() - video_start
        video_logs.append(f"  【视频处理完成】耗时: {video_time:.2f} 秒")
        
        return video_logs, video_scenes
    
    if len(task["videos"]) > 1 and num_processes > 1:
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            args_list = [
                (video_idx, video_path, task["output_dir"], threshold, frame_precision, fast_mode)
                for video_idx, video_path in enumerate(task["videos"])
            ]
            futures = list(executor.map(process_single_video, args_list))
            
            for video_logs, video_scenes in futures:
                task["logs"].extend(video_logs)
                all_scenes.extend(video_scenes)
    else:
        for video_idx, video_path in enumerate(task["videos"]):
            video_logs, video_scenes = process_single_video((video_idx, video_path, task["output_dir"], threshold, frame_precision, fast_mode))
            task["logs"].extend(video_logs)
            all_scenes.extend(video_scenes)
    
    task["scenes"] = all_scenes
    
    if not skip_ai and all_scenes:
        task["logs"].append("【AI分类】开始自动分类...")
        ai_start = time.time()
        
        effective_categories = categories if categories and len(categories) > 0 else PREDEFINED_CATEGORIES
        if effective_categories:
            task["logs"].append(f"  使用分类: {', '.join(effective_categories)}")
        
        use_voting = False
        use_clip = CLIP_AVAILABLE
        num_threads = min(len(all_scenes), 8)
        num_frames_per_scene = 1 if use_clip else 1
        
        task["logs"].append(f"  并行处理: {num_threads} 个线程")
        task["logs"].append(f"  分类模式: {'CLIP+Qwen双层' if use_clip else 'Qwen单层'}")
        task["logs"].append(f"  单帧识别模式")
        
        def process_scene(scene):
            scene_path = scene["path"]
            frame_path = scene_path.replace('.mp4', '_frame.jpg')
            success = extract_keyframe(scene_path, frame_path)
            
            if success and os.path.exists(frame_path):
                if use_clip:
                    category = classify_with_clip_and_qwen(frame_path, effective_categories)
                else:
                    category = analyze_image_with_ai(frame_path, effective_categories)
                os.remove(frame_path)
            else:
                category = "其他"
                logger.warning(f"无法提取关键帧: {scene_path}")
            
            return scene["filename"], category
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(process_scene, scene): scene for scene in all_scenes}
            
            processed_count = 0
            for future in as_completed(futures):
                scene = futures[future]
                try:
                    filename, category = future.result()
                    scene["category"] = category
                    processed_count += 1
                    if processed_count % 5 == 0 or processed_count == len(all_scenes):
                        task["logs"].append(f"    ✓ 已处理 {processed_count}/{len(all_scenes)} 个片段")
                except Exception as e:
                    scene["category"] = "其他"
                    logger.error(f"处理场景失败: {e}")
        
        ai_time = time.time() - ai_start
        task["logs"].append(f"【AI分类完成】耗时: {ai_time:.2f} 秒")
    
    task["status"] = "completed"
    
    total_time = time.time() - start_total
    task["logs"].append("=" * 50)
    task["logs"].append(f"【任务完成】共处理 {len(task['videos'])} 个视频")
    task["logs"].append(f"【生成片段】{len(all_scenes)} 个")
    task["logs"].append(f"【总耗时】{total_time:.2f} 秒")
    task["logs"].append(f"【平均速度】{total_scenes / total_time:.2f} 片段/秒")
    task["logs"].append("=" * 50)
    
    if "db_id" in task:
        db.update_task(task["db_id"], "completed", len(all_scenes), datetime.now().isoformat())
    
    return {"task_id": task_id, "scene_count": len(all_scenes), "message": "处理完成"}

def detect_scenes(video_path, threshold=27.0, frame_precision=False):
    try:
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
            scene_data = {
                "index": i + 1,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time
            }
            if frame_precision:
                scene_data["start_frame"] = scene[0].get_frames()
                scene_data["end_frame"] = scene[1].get_frames()
            scenes.append(scene_data)
        
        return scenes
    except Exception as e:
        logger.error(f"Scene detection failed: {e}")
        return []

@app.post("/api/task/{task_id}/re-split/{scene_index}")
async def re_split_scene(task_id: int, scene_index: int, threshold: float = Query(20.0, description="二次拆分阈值")):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if scene_index < 0 or scene_index >= len(task["scenes"]):
        raise HTTPException(status_code=404, detail="片段不存在")
    
    import time
    start_time = time.time()
    
    scene = task["scenes"][scene_index]
    scene_path = scene["path"]
    creator_name = scene["creator_name"]
    video_name = scene["video_name"]
    
    task["logs"].append(f"【二次拆分】开始拆分片段: {scene['filename']}")
    task["logs"].append(f"  ├─ 阈值: {threshold}")
    task["logs"].append(f"  └─ 原文件: {scene_path}")
    
    sub_scenes = detect_scenes(scene_path, threshold)
    task["logs"].append(f"  检测到 {len(sub_scenes)} 个子场景")
    
    if len(sub_scenes) <= 1:
        task["logs"].append("  ✗ 未检测到新的场景边界，无需拆分")
        return {"success": False, "message": "未检测到新的场景边界"}
    
    today = datetime.now().strftime("%m%d")
    scene_output_dir = os.path.join(task["output_dir"], creator_name)
    os.makedirs(scene_output_dir, exist_ok=True)
    
    new_scenes = []
    original_index = scene["scene_number"]
    
    for i, sub_scene in enumerate(sub_scenes):
        sub_start = sub_scene["start_time"]
        sub_end = sub_scene["end_time"]
        
        sub_filename = f"{today}{creator_name}-{original_index}_{i+1}.mp4"
        sub_path = os.path.join(scene_output_dir, sub_filename)
        
        cmd = [
            "ffmpeg", "-i", scene_path,
            "-ss", str(sub_start),
            "-to", str(sub_end),
            "-c:v", "libx264",
            "-an",
            "-avoid_negative_ts", "make_zero",
            "-y", sub_path
        ]
        
        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(sub_path):
            sub_size = os.path.getsize(sub_path) / 1024
            sub_end_adjusted = sub_end
            task["logs"].append(f"    ✓ 子片段 {i+1}: {sub_start:.3f}s -> {sub_end_adjusted:.3f}s")
            
            new_scenes.append({
                "task_id": task_id,
                "video_name": video_name,
                "creator_name": creator_name,
                "scene_number": f"{original_index}_{i+1}",
                "filename": sub_filename,
                "path": sub_path,
                "start_time": scene["start_time"] + sub_start,
                "end_time": scene["start_time"] + sub_end_adjusted,
                "duration": sub_end_adjusted - sub_start,
                "category": "未分类",
                "tags": [],
                "selected": False
            })
    
    task["scenes"].pop(scene_index)
    
    for i, new_scene in enumerate(new_scenes):
        task["scenes"].insert(scene_index + i, new_scene)
    
    elapsed = time.time() - start_time
    task["logs"].append(f"【二次拆分完成】拆分为 {len(new_scenes)} 个子片段，耗时: {elapsed:.2f}s")
    
    return {"success": True, "new_scenes_count": len(new_scenes), "total_scenes": len(task["scenes"])}

@app.get("/api/tasks")
async def get_tasks():
    db_tasks = db.get_tasks_db(20)
    return {"success": True, "tasks": tasks, "db_tasks": db_tasks}

@app.get("/api/task/{task_id}")
async def get_task(task_id: int):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@app.post("/api/task/{task_id}/select/{scene_index}")
async def toggle_scene_select(task_id: int, scene_index: int, selected: bool = Query(...)):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if 0 <= scene_index < len(task["scenes"]):
        task["scenes"][scene_index]["selected"] = selected
        return {"success": True}
    return {"success": False}

@app.post("/api/task/{task_id}/select-all")
async def select_all_scenes(task_id: int, selected: bool = Query(...)):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    for scene in task["scenes"]:
        scene["selected"] = selected
    return {"success": True, "count": len(task["scenes"])}

@app.post("/api/task/{task_id}/export")
async def export_scenes(task_id: int, selected_only: bool = True):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    scenes_to_export = [s for s in task["scenes"] if s["selected"]] if selected_only else task["scenes"]
    
    export_dir = os.path.join(task["output_dir"], "导出")
    
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir, exist_ok=True)
    
    exported_count = 0
    for scene in scenes_to_export:
        src_path = scene["path"]
        dst_path = os.path.join(export_dir, scene["filename"])
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            exported_count += 1
    
    return {"success": True, "exported_count": exported_count, "export_dir": export_dir}

@app.get("/api/categories")
async def get_categories():
    return {"categories": PREDEFINED_CATEGORIES}

@app.post("/api/task/{task_id}/scene/{scene_index}/category")
async def update_scene_category(task_id: int, scene_index: int, category: str):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if 0 <= scene_index < len(task["scenes"]):
        task["scenes"][scene_index]["category"] = category
        return {"success": True, "category": category}
    return {"success": False}

@app.post("/api/task/{task_id}/batch-category")
async def batch_update_category(task_id: int, category: str, scene_indices: List[int]):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    updated_count = 0
    for index in scene_indices:
        if 0 <= index < len(task["scenes"]):
            task["scenes"][index]["category"] = category
            updated_count += 1
    
    return {"success": True, "updated_count": updated_count}

@app.get("/api/task/{task_id}/categories-summary")
async def get_categories_summary(task_id: int):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    summary = {}
    for scene in task["scenes"]:
        cat = scene["category"]
        summary[cat] = summary.get(cat, 0) + 1
    
    return {"summary": summary}

@app.post("/api/task/{task_id}/export-by-category")
async def export_by_category(task_id: int, category: Optional[str] = None):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if category:
        scenes_to_export = [s for s in task["scenes"] if s["category"] == category]
        export_dir = os.path.join(task["output_dir"], "导出", category)
    else:
        scenes_to_export = task["scenes"]
        export_dir = os.path.join(task["output_dir"], "导出", "全部")
    
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir, exist_ok=True)
    
    exported_count = 0
    for scene in scenes_to_export:
        src_path = scene["path"]
        dst_path = os.path.join(export_dir, scene["filename"])
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            exported_count += 1
    
    return {"success": True, "exported_count": exported_count, "export_dir": export_dir}

@app.post("/api/recognize-categories")
async def recognize_categories(image: UploadFile = File(...)):
    try:
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        
        prompt = """请分析这张图片中的文件夹目录结构，提取所有分类文件夹名称。
        图片显示的是一个文件管理器界面，包含多个文件夹。请列出所有可见的文件夹名称。
        只返回文件夹名称列表，每个名称占一行，不要添加其他内容。"""
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "qwen2.5vl:7b",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "")
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
            return {"success": True, "categories": lines}
        else:
            return {"success": False, "error": "AI识别失败"}
    except Exception as e:
        logger.error(f"识别分类失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/set-categories")
async def set_categories(categories: List[str]):
    global PREDEFINED_CATEGORIES
    PREDEFINED_CATEGORIES = categories
    return {"success": True, "categories": PREDEFINED_CATEGORIES}

@app.get("/api/category-sets")
async def get_category_sets_api():
    sets = db.get_category_sets()
    return {"success": True, "sets": sets, "current_set": CURRENT_CATEGORY_SET}

@app.post("/api/category-sets/save")
async def save_category_set_api(set_name: str = Query(...), categories: List[str] = Query(...)):
    success = db.save_category_set(set_name, categories)
    if success:
        logger.info(f"已保存品类集合: {set_name}")
        return {"success": True, "message": f"已保存品类集合: {set_name}"}
    return {"success": False, "error": "保存失败"}

@app.post("/api/category-sets/load")
async def load_category_set_api(set_name: str = Query(...)):
    global PREDEFINED_CATEGORIES, CURRENT_CATEGORY_SET
    categories = db.get_category_set(set_name)
    if categories:
        PREDEFINED_CATEGORIES = categories
        CURRENT_CATEGORY_SET = set_name
        db.save_category_set(set_name, categories)
        logger.info(f"已加载品类集合: {set_name}")
        return {"success": True, "categories": PREDEFINED_CATEGORIES, "message": f"已加载品类集合: {set_name}"}
    return {"success": False, "error": "品类集合不存在"}

@app.post("/api/category-sets/delete")
async def delete_category_set_api(set_name: str = Query(...)):
    global CURRENT_CATEGORY_SET
    success = db.delete_category_set(set_name)
    if success:
        if CURRENT_CATEGORY_SET == set_name:
            CURRENT_CATEGORY_SET = None
        logger.info(f"已删除品类集合: {set_name}")
        return {"success": True, "message": f"已删除品类集合: {set_name}"}
    return {"success": False, "error": "品类集合不存在"}

@app.post("/api/category-sets/rename")
async def rename_category_set_api(old_name: str = Query(...), new_name: str = Query(...)):
    global CURRENT_CATEGORY_SET
    success = db.rename_category_set(old_name, new_name)
    if success:
        if CURRENT_CATEGORY_SET == old_name:
            CURRENT_CATEGORY_SET = new_name
        logger.info(f"已重命名品类集合: {old_name} -> {new_name}")
        return {"success": True, "message": f"已重命名品类集合: {old_name} -> {new_name}"}
    return {"success": False, "error": "品类集合不存在"}

@app.get("/api/training-set")
async def get_training_set(product: Optional[str] = None):
    samples = get_training_samples(product)
    db_samples = db.get_training_samples_db(product)
    summary, total = db.get_training_summary(product)
    return {"success": True, "categories": samples, "total_samples": total, "current_product": CURRENT_PRODUCT, "db_summary": summary}

@app.get("/api/products")
async def get_products():
    products = get_all_products()
    return {"success": True, "products": products, "current_product": CURRENT_PRODUCT}

@app.post("/api/set-product")
async def set_product(product_name: str = Query(...)):
    set_current_product(product_name)
    return {"success": True, "product": product_name}

@app.post("/api/clear-product")
async def clear_product():
    global CURRENT_PRODUCT
    CURRENT_PRODUCT = None
    return {"success": True, "message": "已清除当前产品"}

@app.post("/api/training-set/add")
async def add_to_training_set(task_id: int, scene_index: int, correct_category: str, product: Optional[str] = None):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if 0 <= scene_index < len(task["scenes"]):
        scene = task["scenes"][scene_index]
        video_path = scene["path"]
        
        train_dir = get_training_dir(product)
        cat_dir = os.path.join(train_dir, correct_category)
        os.makedirs(cat_dir, exist_ok=True)
        
        frame_path = video_path.replace('.mp4', '_frame.jpg')
        success = extract_keyframe(video_path, frame_path)
        
        if success and os.path.exists(frame_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = os.path.join(cat_dir, f"{timestamp}_{os.path.basename(frame_path)}")
            shutil.copy2(frame_path, dest_path)
            os.remove(frame_path)
            
            scene["training_added"] = True
            scene["correct_category"] = correct_category
            
            db.add_training_sample(product or CURRENT_PRODUCT, correct_category, dest_path, task.get("db_id"), scene_index)
            
            logger.info(f"已添加训练样本: {dest_path} -> {correct_category}")
            return {"success": True, "message": f"已添加到训练集: {correct_category}", "product": product or CURRENT_PRODUCT}
        else:
            return {"success": False, "error": "无法提取关键帧"}
    return {"success": False, "error": "无效的片段索引"}

@app.post("/api/training-set/remove")
async def remove_from_training_set(category: str, filename: str):
    file_path = os.path.join(TRAINING_DIR, category, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"已从训练集删除: {file_path}")
        return {"success": True, "message": "删除成功"}
    return {"success": False, "error": "文件不存在"}

@app.post("/api/training-set/clear")
async def clear_training_set(category: Optional[str] = None):
    if category:
        cat_dir = os.path.join(TRAINING_DIR, category)
        if os.path.exists(cat_dir):
            shutil.rmtree(cat_dir)
            logger.info(f"已清空训练集分类: {category}")
            return {"success": True, "message": f"已清空分类: {category}"}
        return {"success": False, "error": "分类不存在"}
    else:
        shutil.rmtree(TRAINING_DIR)
        os.makedirs(TRAINING_DIR)
        logger.info("已清空整个训练集")
        return {"success": True, "message": "已清空整个训练集"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, timeout_keep_alive=300)