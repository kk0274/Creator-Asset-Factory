import os
import sys
import requests
import shutil

print("=== 完整视频拆分测试 ===")

# 检查服务状态
print("\n1. 检查服务状态...")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=10)
    if response.status_code == 200:
        print("   ✓ 后端服务运行正常")
    else:
        print("   ✗ 后端服务异常")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 无法连接后端服务: {e}")
    sys.exit(1)

# 创建一个有明显场景变化的测试视频
print("\n2. 创建测试视频（包含3个明显场景）...")
test_video_path = r"C:\Users\Neko\Desktop\素材拆分与分类\测试视频.mp4"

# 删除旧的测试文件
if os.path.exists(test_video_path):
    os.remove(test_video_path)

try:
    # 创建一个包含不同颜色场景的测试视频
    cmd = [
        "ffmpeg", 
        "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=30",  # 彩色测试图案
        "-f", "lavfi", "-i", "color=c=red:duration=2:size=1280x720:rate=30",    # 红色场景
        "-f", "lavfi", "-i", "color=c=green:duration=2:size=1280x720:rate=30",  # 绿色场景
        "-f", "lavfi", "-i", "color=c=blue:duration=2:size=1280x720:rate=30",   # 蓝色场景
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
        print(f"   ✗ 创建失败: {result.stderr[:100]}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    sys.exit(1)

# 上传视频并处理
print("\n3. 上传并拆分视频...")
try:
    with open(test_video_path, "rb") as f:
        files = {"file": ("达人测试视频.mp4", f, "video/mp4")}
        print("   正在上传...")
        response = requests.post("http://localhost:8000/api/upload", files=files, timeout=300)
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 处理成功！拆分出 {data['scenes_count']} 个片段")
except Exception as e:
    print(f"   ✗ 上传失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 查看拆分结果
print("\n4. 查看拆分结果...")
try:
    response = requests.get("http://localhost:8000/api/scenes", timeout=10)
    data = response.json()
    print(f"   场景总数: {data['total']}")
    
    if data['data']:
        # 只显示最新的4个场景
        recent_scenes = data['data'][-4:]
        recent_scenes.reverse()
        
        print("\n   拆分结果列表:")
        for i, scene in enumerate(recent_scenes, 1):
            print(f"\n   [{i}] 文件名: {scene['scene_name']}")
            print(f"      分类: {scene['category']}")
            print(f"      产品分类: {scene['product_category']}")
            print(f"      标签: {scene['tags']}")
            print(f"      时长: {scene['duration']:.2f}秒")
            print(f"      路径: {scene['scene_path']}")
            
            # 检查文件是否存在
            if os.path.exists(scene['scene_path']):
                file_size = os.path.getsize(scene['scene_path']) / 1024
                print(f"      ✓ 文件存在 ({file_size:.1f} KB)")
            else:
                print(f"      ✗ 文件不存在")
                
except Exception as e:
    print(f"   ✗ 获取结果失败: {e}")

# 显示文件结构
print("\n5. 文件目录结构...")
data_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\data\videos"
if os.path.exists(data_dir):
    print(f"   目录: {data_dir}")
    for root, dirs, files in os.walk(data_dir):
        level = root.replace(data_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... (还有 {len(files) - 5} 个文件)")
else:
    print("   ✗ 数据目录不存在")

# 清理测试文件
print("\n6. 清理测试文件...")
try:
    if os.path.exists(test_video_path):
        os.remove(test_video_path)
        print("   ✓ 删除测试视频")
except Exception as e:
    print(f"   ✗ 清理失败: {e}")

print("\n=== 测试完成 ===")
print("\n💡 您可以打开 http://localhost:5173 上传真实视频测试")
