import os
import shutil
import logging
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.requests import Request
from sqlalchemy.orm import Session
from models.database import Video, Scene, Tag, SceneTag, get_db, init_db
from utils.video_processor import detect_scenes, extract_keyframes, analyze_with_ai, get_creator_name, get_today_date
from datetime import datetime
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Creator Asset Manager")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")
init_db()

@app.post("/api/upload")
async def upload_video(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info(f"Received upload request from {request.client.host}")
    logger.info(f"File: {file.filename}, Size: {file.size} bytes, Content-Type: {file.content_type}")
    
    if not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file type. Only MP4, MOV, AVI, MKV are supported")
    
    video_path = os.path.join(DATA_DIR, "temp", file.filename)
    video_path = os.path.abspath(video_path)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)
    logger.info(f"Video path: {video_path}")
    
    try:
        logger.info(f"Saving file to: {video_path}")
        with open(video_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"File saved successfully")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    creator_name = get_creator_name(file.filename)
    today = get_today_date()
    
    video = Video(video_name=file.filename, video_path=video_path, status="processing", creator_name=creator_name, upload_time=datetime.now())
    db.add(video)
    db.commit()
    db.refresh(video)
    
    try:
        logger.info("Starting scene detection...")
        scenes = detect_scenes(video_path)
        logger.info(f"Detected {len(scenes)} scenes")
        
        if len(scenes) == 0:
            logger.warning("No scenes detected in video")
            video.status = "completed"
            db.commit()
            return {"message": "Video processed but no scenes detected", "video_id": video.id, "scenes_count": 0}
        
        product_categories = {}
        all_scene_results = []
        
        for scene in scenes:
            scene_num = scene["index"]
            logger.info(f"Processing scene {scene_num}: start={scene['start_time']}, end={scene['end_time']}")
            
            scene_output_dir = os.path.join(DATA_DIR, "temp", f"scene_{scene_num}")
            scene_output_dir = os.path.abspath(scene_output_dir)
            os.makedirs(scene_output_dir, exist_ok=True)
            logger.info(f"Scene output dir: {scene_output_dir}")
            
            temp_scene_path = os.path.join(scene_output_dir, "temp.mp4")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-ss", str(scene["start_time"]),
                "-to", str(scene["end_time"]),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-y", temp_scene_path
            ]
            
            logger.info(f"Executing ffmpeg command")
            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg failed for scene {scene_num}: {result.stderr[:100]}")
                continue
            
            if not os.path.exists(temp_scene_path):
                logger.error(f"FFmpeg did not produce output file: {temp_scene_path}")
                continue
            
            logger.info(f"Scene {scene_num} saved to: {temp_scene_path}")
            
            keyframes = extract_keyframes(temp_scene_path, scene_output_dir)
            logger.info(f"Extracted {len(keyframes)} keyframes for scene {scene_num}")
            
            if keyframes:
                for kf in keyframes:
                    exists = os.path.exists(kf)
                    logger.info(f"  Keyframe: {kf} (exists: {exists})")
            
            if not keyframes:
                logger.warning(f"No keyframes extracted for scene {scene_num}, skipping AI analysis")
                ai_result = {"category": "uncategorized", "product_category": "other", "tags": ["unrecognized"]}
            else:
                ai_result = analyze_with_ai(keyframes)
                logger.info(f"AI analysis result for scene {scene_num}: {ai_result}")
            
            category = ai_result.get("category", "uncategorized")
            product_category = ai_result.get("product_category", "other")
            tags = ai_result.get("tags", ["unrecognized"])
            
            product_categories[product_category] = True
            all_scene_results.append({
                "scene": scene, 
                "category": category, 
                "product_category": product_category, 
                "tags": tags, 
                "temp_path": temp_scene_path
            })
        
        if not all_scene_results:
            logger.warning("No scenes were successfully processed")
            video.status = "completed"
            db.commit()
            return {"message": "No scenes could be processed", "video_id": video.id, "scenes_count": 0}
        
        logger.info(f"Organizing {len(all_scene_results)} processed scenes into folders")
        
        for product_category in product_categories:
            creator_dir = os.path.join(DATA_DIR, "videos", product_category, creator_name)
            creator_dir = os.path.abspath(creator_dir)
            os.makedirs(creator_dir, exist_ok=True)
            logger.info(f"Created product category directory: {creator_dir}")
            
            for scene_result in all_scene_results:
                if scene_result["product_category"] == product_category:
                    scene_num = scene_result["scene"]["index"]
                    category_name = scene_result["category"]
                    folder_name = f"{today}{creator_name}({category_name})"
                    folder_path = os.path.join(creator_dir, folder_name)
                    folder_path = os.path.abspath(folder_path)
                    os.makedirs(folder_path, exist_ok=True)
                    
                    final_filename = f"{today}{creator_name}-{scene_num}.mp4"
                    final_path = os.path.join(folder_path, final_filename)
                    shutil.copy(scene_result["temp_path"], final_path)
                    logger.info(f"Copied scene {scene_num} to: {final_path}")
                    
                    thumbnail_path = os.path.join(folder_path, f"{today}{creator_name}-{scene_num}.jpg")
                    keyframe_path = os.path.join(scene_output_dir, "frame_0.jpg")
                    if os.path.exists(keyframe_path):
                        shutil.copy(keyframe_path, thumbnail_path)
                        logger.info(f"Copied thumbnail for scene {scene_num}")
                    
                    scene_db = Scene(
                        video_id=video.id,
                        scene_name=final_filename,
                        scene_path=final_path,
                        thumbnail_path=thumbnail_path,
                        duration=scene_result["scene"]["duration"],
                        category=category_name,
                        product_category=product_category,
                        scene_number=scene_num
                    )
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
        logger.info(f"Video processing completed successfully: {video.id}, scenes: {len(all_scene_results)}")
        return {"message": "Video processed successfully", "video_id": video.id, "scenes_count": len(all_scene_results)}
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}", exc_info=True)
        video.status = "failed"
        db.commit()
        shutil.rmtree(os.path.join(DATA_DIR, "temp"), ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenes")
def get_scenes(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), 
               category: Optional[str] = None, tag: Optional[str] = None, 
               keyword: Optional[str] = None, db: Session = Depends(get_db)):
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
        results.append({
            "id": scene.id,
            "scene_name": scene.scene_name,
            "scene_path": scene.scene_path,
            "thumbnail_path": scene.thumbnail_path,
            "duration": scene.duration,
            "category": scene.category,
            "product_category": scene.product_category,
            "scene_number": scene.scene_number,
            "created_time": scene.created_time,
            "tags": tags,
            "video_name": scene.video.video_name,
            "creator_name": scene.video.creator_name
        })
    
    return {"total": total, "data": results}

@app.get("/api/scenes/{scene_id}")
def get_scene(scene_id: int, db: Session = Depends(get_db)):
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    tags = [st.tag.tag_name for st in scene.scene_tags]
    return {
        "id": scene.id,
        "scene_name": scene.scene_name,
        "scene_path": scene.scene_path,
        "thumbnail_path": scene.thumbnail_path,
        "duration": scene.duration,
        "category": scene.category,
        "product_category": scene.product_category,
        "scene_number": scene.scene_number,
        "created_time": scene.created_time,
        "tags": tags,
        "video_name": scene.video.video_name,
        "creator_name": scene.video.creator_name
    }

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
    return [{
        "id": v.id,
        "video_name": v.video_name,
        "upload_time": v.upload_time,
        "status": v.status,
        "creator_name": v.creator_name
    } for v in videos]

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Service is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=300)
