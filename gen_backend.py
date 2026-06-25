from make_files import w

w(r"C:\Users\Neko\Desktop\素材拆分与分类\backend\main.py", '''
import os
import shutil
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from models.database import Video, Scene, Tag, SceneTag, get_db, init_db
from utils.video_processor import detect_scenes, extract_keyframes, analyze_with_ai, get_creator_name, get_today_date
from datetime import datetime
from typing import List, Optional

app = FastAPI(title="Creator Asset Manager")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
init_db()

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith((".mp4", ".mov", ".avi", ".mkv")):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    video_path = os.path.join(DATA_DIR, "temp", file.filename)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    creator_name = get_creator_name(file.filename)
    today = get_today_date()
    
    video = Video(video_name=file.filename, video_path=video_path, status="processing", creator_name=creator_name, upload_time=datetime.now())
    db.add(video)
    db.commit()
    db.refresh(video)
    
    try:
        scenes = detect_scenes(video_path)
        product_categories = {}
        all_scene_results = []
        
        for scene in scenes:
            scene_output_dir = os.path.join(DATA_DIR, "temp", "scene_" + str(scene["index"]))
            os.makedirs(scene_output_dir, exist_ok=True)
            
            temp_scene_path = os.path.join(scene_output_dir, "temp.mp4")
            cmd = ["ffmpeg", "-i", video_path, "-ss", str(scene["start_time"]), "-to", str(scene["end_time"]), "-c:v", "libx264", "-c:a", "aac", "-y", temp_scene_path]
            import subprocess
            subprocess.run(cmd, check=True, capture_output=True)
            
            keyframes = extract_keyframes(temp_scene_path, scene_output_dir)
            ai_result = analyze_with_ai(keyframes)
            
            category = ai_result.get("category", "uncategorized")
            product_category = ai_result.get("product_category", "other")
            tags = ai_result.get("tags", ["unrecognized"])
            
            product_categories[product_category] = True
            all_scene_results.append({"scene": scene, "category": category, "product_category": product_category, "tags": tags, "temp_path": temp_scene_path})
        
        for product_category in product_categories:
            creator_dir = os.path.join(DATA_DIR, "videos", product_category, creator_name)
            os.makedirs(creator_dir, exist_ok=True)
            
            for scene_result in all_scene_results:
                if scene_result["product_category"] == product_category:
                    scene_num = scene_result["scene"]["index"]
                    category_name = scene_result["category"]
                    folder_name = today + creator_name + "(" + category_name + ")"
                    folder_path = os.path.join(creator_dir, folder_name)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    final_filename = today + creator_name + "-" + str(scene_num) + ".mp4"
                    final_path = os.path.join(folder_path, final_filename)
                    shutil.copy(scene_result["temp_path"], final_path)
                    
                    thumbnail_path = os.path.join(folder_path, today + creator_name + "-" + str(scene_num) + ".jpg")
                    keyframe_path = os.path.join(DATA_DIR, "temp", "scene_" + str(scene_num), "frame_0.jpg")
                    if os.path.exists(keyframe_path):
                        shutil.copy(keyframe_path, thumbnail_path)
                    
                    scene_db = Scene(video_id=video.id, scene_name=final_filename, scene_path=final_path, thumbnail_path=thumbnail_path, duration=scene_result["scene"]["duration"], category=category_name, product_category=product_category, scene_number=scene_num)
                    db.add(scene_db)
                    db.commit()
                    db.refresh(scene_db)
                    
                    for tag_name in scene_result["tags"]:
                        tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()
                        if not tag:
                            tag = Tag(tag_name=tag_name)
                            db.add(tag)
                            db.commit()
                            db.refresh(tag)
                        scene_tag = SceneTag(scene_id=scene_db.id, tag_id=tag.id)
                        db.add(scene_tag)
                    db.commit()
        
        shutil.rmtree(os.path.join(DATA_DIR, "temp"), ignore_errors=True)
        video.status = "completed"
        db.commit()
        return {"message": "Video processed successfully", "video_id": video.id}
    
    except Exception as e:
        video.status = "failed"
        db.commit()
        shutil.rmtree(os.path.join(DATA_DIR, "temp"), ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenes")
def get_scenes(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), category: Optional[str] = None, tag: Optional[str] = None, keyword: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Scene)
    if category:
        query = query.filter(Scene.category == category)
    if tag:
        query = query.join(SceneTag).join(Tag).filter(Tag.tag_name == tag)
    if keyword:
        query = query.filter(Scene.scene_name.contains(keyword) | Scene.category.contains(keyword) | Scene.product_category.contains(keyword))
    
    total = query.count()
    scenes = query.offset((page - 1) * page_size).limit(page_size).all()
    
    results = []
    for scene in scenes:
        tags = [st.tag.tag_name for st in scene.scene_tags]
        results.append({"id": scene.id, "scene_name": scene.scene_name, "scene_path": scene.scene_path, "thumbnail_path": scene.thumbnail_path, "duration": scene.duration, "category": scene.category, "product_category": scene.product_category, "scene_number": scene.scene_number, "created_time": scene.created_time, "tags": tags, "video_name": scene.video.video_name, "creator_name": scene.video.creator_name})
    
    return {"total": total, "data": results}

@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: int, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    tags = [st.tag.tag_name for st in scene.scene_tags]
    return {"id": scene.id, "scene_name": scene.scene_name, "scene_path": scene.scene_path, "thumbnail_path": scene.thumbnail_path, "duration": scene.duration, "category": scene.category, "product_category": scene.product_category, "scene_number": scene.scene_number, "created_time": scene.created_time, "tags": tags, "video_name": scene.video.video_name, "creator_name": scene.video.creator_name}

@app.put("/api/scenes/{scene_id}")
def update_scene(scene_id: int, category: Optional[str] = None, tags: Optional[List[str]] = None, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if category:
        scene.category = category
    if tags:
        db.query(SceneTag).filter(SceneTag.scene_id == scene_id).delete()
        for tag_name in tags:
            tag = db.query(Tag).filter(Tag.tag_name == tag_name).first()
            if not tag:
                tag = Tag(tag_name=tag_name)
                db.add(tag)
                db.commit()
                db.refresh(tag)
            scene_tag = SceneTag(scene_id=scene.id, tag_id=tag.id)
            db.add(scene_tag)
    db.commit()
    return {"message": "Scene updated successfully"}

@app.delete("/api/scenes/{scene_id}")
def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if os.path.exists(scene.scene_path):
        os.remove(scene.scene_path)
    if os.path.exists(scene.thumbnail_path):
        os.remove(scene.thumbnail_path)
    
    db.query(SceneTag).filter(SceneTag.scene_id == scene_id).delete()
    db.delete(scene)
    db.commit()
    return {"message": "Scene deleted successfully"}

@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Scene.category).distinct().all()
    return [cat[0] for cat in categories]

@app.get("/api/tags")
def get_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return [tag.tag_name for tag in tags]

@app.get("/api/videos")
def get_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).all()
    return [{"id": v.id, "video_name": v.video_name, "upload_time": v.upload_time, "status": v.status, "creator_name": v.creator_name} for v in videos]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''')

w(r"C:\Users\Neko\Desktop\素材拆分与分类\backend\utils\video_processor.py", '''
import os
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
        scenes.append({"index": i + 1, "start_time": start_time, "end_time": end_time, "duration": end_time - start_time})
    
    return scenes

def extract_keyframes(video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    keyframe_indices = [0, total_frames // 2, total_frames - 1]
    keyframe_paths = []
    
    for idx in keyframe_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            timestamp = idx / fps
            frame_path = os.path.join(output_dir, "frame_" + str(int(timestamp)) + ".jpg")
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
    
    prompt_text = "Analyze image content and generate category and tags. Output JSON format: {\"category\":\"category_name\",\"product_category\":\"product_category\",\"tags\":[\"tag1\",\"tag2\",\"tag3\"]}"
    
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt_text}] + [{"type": "image", "image": img} for img in images_base64]}]
    
    try:
        response = httpx.post("http://localhost:11434/api/chat", json={"model": "qwen2.5vl:7b", "messages": messages, "stream": False}, timeout=120)
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
''')

print("Backend files created successfully!")
