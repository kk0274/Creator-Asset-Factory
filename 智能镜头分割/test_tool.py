import os
import sys
import requests

print("=== 测试智能镜头分割工具 ===")

# 检查服务状态
print("\n1. 检查服务状态...")
try:
    response = requests.get("http://localhost:8001/api/health", timeout=10)
    if response.status_code == 200:
        print("   ✓ 后端服务运行正常")
    else:
        print("   ✗ 后端服务异常")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 无法连接后端服务: {e}")
    sys.exit(1)

# 创建测试视频
print("\n2. 创建测试视频...")
test_video_path = r"C:\Users\Neko\Desktop\素材拆分与分类\智能镜头分割\test_video.mp4"

if os.path.exists(test_video_path):
    os.remove(test_video_path)

try:
    cmd = [
        "ffmpeg", 
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "color=c=red:duration=2:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "color=c=green:duration=2:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "color=c=blue:duration=2:size=1280x720:rate=30",
        "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=8",
        "-c:v", "libx264", "-c:a", "aac", "-y", test_video_path
    ]
    
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"   ✓ 测试视频创建成功")
        print(f"   文件大小: {os.path.getsize(test_video_path) / 1024:.1f} KB")
    else:
        print(f"   ✗ 创建失败")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    sys.exit(1)

# 上传视频
print("\n3. 上传视频...")
try:
    with open(test_video_path, "rb") as f:
        files = {"files": ("测试达人视频.mp4", f, "video/mp4")}
        response = requests.post("http://localhost:8001/api/upload", files=files, timeout=60)
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   任务ID: {result['task_id']}")
        print(f"   任务名: {result['task_name']}")
        
        task_id = result['task_id']
except Exception as e:
    print(f"   ✗ 上传失败: {e}")
    sys.exit(1)

# 处理视频
print("\n4. 处理视频...")
try:
    response = requests.post(f"http://localhost:8001/api/process/{task_id}", timeout=120)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   生成片段数: {result['scene_count']}")
    print(f"   消息: {result['message']}")
except Exception as e:
    print(f"   ✗ 处理失败: {e}")
    sys.exit(1)

# 查看任务详情
print("\n5. 查看任务详情...")
try:
    response = requests.get(f"http://localhost:8001/api/task/{task_id}", timeout=10)
    task = response.json()
    print(f"   任务状态: {task['status']}")
    print(f"   日志:")
    for log in task['logs'][-5:]:
        print(f"     - {log}")
except Exception as e:
    print(f"   ✗ 获取失败: {e}")

# 查看生成的文件
print("\n6. 查看生成的文件...")
output_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\智能镜头分割\data\输出分类\测试达人视频"
if os.path.exists(output_dir):
    files = os.listdir(output_dir)
    print(f"   输出目录: {output_dir}")
    print(f"   生成的文件:")
    for f in files:
        file_path = os.path.join(output_dir, f)
        file_size = os.path.getsize(file_path) / 1024
        print(f"     - {f} ({file_size:.1f} KB)")
else:
    print("   ✗ 输出目录不存在")

# 清理测试文件
print("\n7. 清理测试文件...")
try:
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print("   ✓ 删除测试视频")
except Exception as e:
    print(f"   ✗ 清理失败: {e}")

print("\n=== 测试完成 ===")
print("\n💡 您可以打开 http://localhost:5174 使用智能镜头分割工具")
