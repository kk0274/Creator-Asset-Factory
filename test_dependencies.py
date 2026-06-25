import subprocess
import sys

print("=== 检查依赖 ===")

# 检查 FFmpeg
print("\n1. 检查FFmpeg...")
try:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ FFmpeg 已安装")
        print(f"   版本: {result.stdout[:50]}")
    else:
        print("   ✗ FFmpeg 未安装或不在PATH中")
except Exception as e:
    print(f"   ✗ 检查失败: {e}")

# 检查 PySceneDetect
print("\n2. 检查PySceneDetect...")
try:
    from scenedetect import VideoManager, SceneManager
    from scenedetect.detectors import ContentDetector
    print("   ✓ PySceneDetect 已安装")
except ImportError as e:
    print(f"   ✗ PySceneDetect 未安装: {e}")

# 检查 OpenCV
print("\n3. 检查OpenCV...")
try:
    import cv2
    print(f"   ✓ OpenCV 已安装，版本: {cv2.__version__}")
except ImportError as e:
    print(f"   ✗ OpenCV 未安装: {e}")

# 检查 Ollama
print("\n4. 检查Ollama...")
try:
    import httpx
    response = httpx.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]
        print("   ✓ Ollama 服务运行正常")
        print(f"   可用模型: {models}")
    else:
        print(f"   ✗ Ollama 服务响应异常: {response.status_code}")
except Exception as e:
    print(f"   ✗ Ollama 服务未运行或不可达: {e}")
