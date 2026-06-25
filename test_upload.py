import requests
import os
import sys

print("=== 测试视频上传功能 ===")

# 测试健康检查
print("\n1. 测试健康检查接口...")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=10)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"   失败: {e}")

# 测试获取场景列表
print("\n2. 测试获取场景列表...")
try:
    response = requests.get("http://localhost:8000/api/scenes", timeout=10)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text[:200]}...")
except Exception as e:
    print(f"   失败: {e}")

# 测试获取视频列表
print("\n3. 测试获取视频列表...")
try:
    response = requests.get("http://localhost:8000/api/videos", timeout=10)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"   失败: {e}")

# 检查是否有测试视频文件
print("\n4. 检查测试文件...")
test_files = []
for root, dirs, files in os.walk(r"C:\Users\Neko\Desktop\素材拆分与分类"):
    for f in files:
        if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
            test_files.append(os.path.join(root, f))

if test_files:
    print(f"   找到 {len(test_files)} 个视频文件:")
    for f in test_files[:3]:
        print(f"     - {f}")
else:
    print("   未找到视频文件")

# 如果有测试文件，尝试上传
if test_files:
    test_file = test_files[0]
    print(f"\n5. 测试上传视频: {os.path.basename(test_file)}")
    try:
        file_size = os.path.getsize(test_file)
        print(f"   文件大小: {file_size} bytes")
        
        with open(test_file, "rb") as f:
            files = {"file": (os.path.basename(test_file), f, "video/mp4")}
            print("   正在上传...")
            response = requests.post("http://localhost:8000/api/upload", files=files, timeout=300)
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   上传失败: {e}")
        import traceback
        traceback.print_exc()
