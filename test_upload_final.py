import os
import sys
import shutil
import requests

print("=== 测试上传功能 ===")

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
        print(f"   ✓ 测试视频创建成功")
    else:
        print(f"   ✗ 创建失败")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    sys.exit(1)

# 测试上传到API
print("\n2. 测试上传到API...")
try:
    with open(test_video_path, "rb") as f:
        files = {"file": ("test_video.mp4", f, "video/mp4")}
        print("   正在上传...")
        response = requests.post("http://localhost:8000/api/upload", files=files, timeout=300)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"   ✗ 上传失败: {e}")
    import traceback
    traceback.print_exc()

# 检查场景列表
print("\n3. 检查场景列表...")
try:
    response = requests.get("http://localhost:8000/api/scenes", timeout=10)
    data = response.json()
    print(f"   状态码: {response.status_code}")
    print(f"   场景总数: {data['total']}")
    if data['data']:
        for scene in data['data'][:3]:
            print(f"   - {scene['scene_name']} (分类: {scene['category']})")
except Exception as e:
    print(f"   ✗ 获取失败: {e}")

# 清理测试文件
print("\n4. 清理测试文件...")
try:
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print(f"   ✓ 删除测试视频")
except Exception as e:
    print(f"   ✗ 清理失败: {e}")

print("\n=== 测试完成 ===")
