
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = 'sqlite:///./sql_app.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True, index=True)
    video_name = Column(String, index=True)
    upload_time = Column(DateTime, default=datetime.now)
    video_path = Column(String)
    status = Column(String, default='pending')
    creator_name = Column(String)
    
    scenes = relationship('Scene', back_populates='video')

class Scene(Base):
    __tablename__ = 'scenes'
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey('videos.id'))
    scene_name = Column(String, index=True)
    scene_path = Column(String)
    thumbnail_path = Column(String)
    duration = Column(Float)
    category = Column(String, index=True)
    product_category = Column(String, index=True)
    created_time = Column(DateTime, default=datetime.now)
    scene_number = Column(Integer)
    
    video = relationship('Video', back_populates='scenes')
    scene_tags = relationship('SceneTag', back_populates='scene')

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True, index=True)
    tag_name = Column(String, unique=True, index=True)
    
    scene_tags = relationship('SceneTag', back_populates='tag')

class SceneTag(Base):
    __tablename__ = 'scene_tags'
    
    scene_id = Column(Integer, ForeignKey('scenes.id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id'), primary_key=True)
    
    scene = relationship('Scene', back_populates='scene_tags')
    tag = relationship('Tag', back_populates='scene_tags')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
