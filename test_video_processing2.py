import os
import sys
import shutil

print("=== 测试修复后的视频处理流程 ===")

sys.path.insert(0, r"C:\Users\Neko\Desktop\素材拆分与分类\backend")

from utils.video_processor import detect_scenes, extract_keyframes, analyze_with_ai, get_creator_name, get_today_date

# 创建测试视频（带有场景变化）
print("\n1. 创建测试视频...")
test_video_path = r"C:\Users\Neko\Desktop\素材拆分与分类\test_video.mp4"
try:
    # 创建带有场景变化的测试视频
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
        print(f"   ✗ 创建失败: {result.stderr[:100]}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ 创建失败: {e}")
    sys.exit(1)

# 测试场景检测
print("\n2. 测试场景检测...")
try:
    scenes = detect_scenes(test_video_path)
    print(f"   ✓ 场景检测成功")
    print(f"   检测到 {len(scenes)} 个场景")
    for scene in scenes:
        print(f"     - 场景 {scene['index']}: {scene['start_time']:.2f}s - {scene['end_time']:.2f}s (时长: {scene['duration']:.2f}s)")
except Exception as e:
    print(f"   ✗ 场景检测失败: {e}")
    import traceback
    traceback.print_exc()

# 测试帧提取
print("\n3. 测试关键帧提取...")
test_output_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\test_output"
os.makedirs(test_output_dir, exist_ok=True)
try:
    keyframes = extract_keyframes(test_video_path, test_output_dir)
    print(f"   ✓ 关键帧提取成功")
    print(f"   提取了 {len(keyframes)} 个关键帧")
    for kf in keyframes:
        print(f"     - {kf} (存在: {os.path.exists(kf)})")
except Exception as e:
    print(f"   ✗ 关键帧提取失败: {e}")
    import traceback
    traceback.print_exc()

# 测试AI分析
print("\n4. 测试AI分析...")
try:
    ai_result = analyze_with_ai(keyframes)
    print(f"   ✓ AI分析成功")
    print(f"   结果: {ai_result}")
except Exception as e:
    print(f"   ✗ AI分析失败: {e}")
    import traceback
    traceback.print_exc()

# 测试上传到API
print("\n5. 测试上传到API...")
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
print("\n6. 清理测试文件...")
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
