import os
import sys
import shutil

print("=== 测试修复后的视频处理流程 ===")

sys.path.insert(0, r"C:\Users\Neko\Desktop\素材拆分与分类\backend")

from utils.video_processor import detect_scenes, extract_keyframes, analyze_with_ai

# 创建测试视频
print("\n1. 创建测试视频...")
test_video_path = r"C:\Users\Neko\Desktop\素材拆分与分类\test_video.mp4"
try:
    cmd = [
        "ffmpeg", 
        "-f", "lavfi", "-i", "testsrc=duration=3:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "color=c=red:duration=3:size=1920x1080:rate=30",
        "-f", "lavfi", "-i", "color=c=blue:duration=4:size=1920x1080:rate=30",
        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
        "-c:v", "libx264", "-c:a", "aac", "-y", test_video_path
    ]
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✓ 测试视频创建成功: {test_video_path}")
        print(f"   文件大小: {os.path.getsize(test_video_path)} bytes")
    else:
        print(f"   ✗ 创建失败")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    sys.exit(1)

# 测试帧提取（使用中文路径）
print("\n2. 测试关键帧提取（中文路径）...")
test_output_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\测试输出"
os.makedirs(test_output_dir, exist_ok=True)
try:
    keyframes = extract_keyframes(test_video_path, test_output_dir)
    print(f"   ✓ 关键帧提取成功")
    print(f"   提取了 {len(keyframes)} 个关键帧")
    for kf in keyframes:
        exists = os.path.exists(kf)
        print(f"     - {kf} (存在: {exists})")
        if exists:
            print(f"       文件大小: {os.path.getsize(kf)} bytes")
except Exception as e:
    print(f"   ✗ 关键帧提取失败: {e}")
    import traceback
    traceback.print_exc()

# 测试上传到API
print("\n3. 测试上传到API...")
try:
    import requests
    with open(test_video_path, "rb") as f:
        files = {"file": ("test_video.mp4", f, "video/mp4")}
        response = requests.post("http://localhost:8000/api/upload", files=files, timeout=300)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"   ✗ 上传失败: {e}")
    import traceback
    traceback.print_exc()

# 清理测试文件
print("\n4. 清理测试文件...")
try:
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print(f"   ✓ 删除测试视频")
    if os.path.exists(test_output_dir):
        shutil.rmtree(test_output_dir)
        print(f"   ✓ 删除输出目录")
except Exception as e:
    print(f"   ✗ 清理失败: {e}")

print("\n=== 测试完成 ===")
