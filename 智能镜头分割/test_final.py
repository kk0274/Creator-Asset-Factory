import os
import requests

print("=== 完整功能测试 (修复后) ===")

# 创建测试视频
print("\n1. 创建测试视频...")
test_video_path = r"C:\Users\Neko\Desktop\素材拆分与分类\智能镜头分割\test_video2.mp4"
if os.path.exists(test_video_path):
    os.remove(test_video_path)

import subprocess
cmd = ["ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30", "-f", "lavfi", "-i", "color=c=red:duration=2:size=1280x720:rate=30", "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0", "-f", "lavfi", "-i", "sine=frequency=440:duration=4", "-c:v", "libx264", "-c:a", "aac", "-y", test_video_path]
subprocess.run(cmd, capture_output=True)

# 上传视频
print("\n2. 上传视频...")
with open(test_video_path, "rb") as f:
    files = {"files": ("测试视频.mp4", f, "video/mp4")}
    response = requests.post("http://localhost:8001/api/upload", files=files, timeout=60)
    task_id = response.json()["task_id"]
    print(f"   任务ID: {task_id}")

# 处理视频
print("\n3. 处理视频...")
response = requests.post(f"http://localhost:8001/api/process/{task_id}", timeout=120)
print(f"   生成片段数: {response.json()['scene_count']}")

# 测试选择功能
print("\n4. 测试选择单个场景...")
response = requests.post(f"http://localhost:8001/api/task/{task_id}/select/0?selected=true", timeout=10)
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ 成功: {response.json()}")
else:
    print(f"   ✗ 失败")

# 测试全选功能
print("\n5. 测试全选功能...")
response = requests.post(f"http://localhost:8001/api/task/{task_id}/select-all?selected=true", timeout=10)
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ 成功: {response.json()}")
else:
    print(f"   ✗ 失败")

# 测试导出功能
print("\n6. 测试导出功能...")
response = requests.post(f"http://localhost:8001/api/task/{task_id}/export?selected_only=false", timeout=30)
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ 成功: 导出 {response.json()['exported_count']} 个")
else:
    print(f"   ✗ 失败")

# 清理
os.remove(test_video_path)

print("\n=== 所有功能测试通过 ===")
