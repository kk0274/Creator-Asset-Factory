import cv2
import os

print("=== 测试OpenCV写入 ===")

# 创建测试图片
test_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\test_opencv"
os.makedirs(test_dir, exist_ok=True)

# 创建一个简单的测试帧
frame = cv2.imread(r"C:\Users\Neko\Desktop\素材拆分与分类\test_output\frame_0.jpg")
if frame is None:
    print("创建测试帧...")
    frame = cv2.imread(r"C:\Users\Neko\Desktop\素材拆分与分类\test_output\frame_5.jpg")

if frame is None:
    # 创建一个简单的彩色帧
    frame = cv2.imread(r"C:\Users\Neko\Desktop\素材拆分与分类\test_output\frame_9.jpg")

if frame is None:
    import numpy as np
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
    frame[:] = (255, 0, 0)  # 红色
    print("使用创建的红色帧")

print(f"帧形状: {frame.shape}")

# 测试写入
test_path = os.path.join(test_dir, "test.jpg")
print(f"尝试写入: {test_path}")
success = cv2.imwrite(test_path, frame)
print(f"写入成功: {success}")
print(f"文件存在: {os.path.exists(test_path)}")
if os.path.exists(test_path):
    print(f"文件大小: {os.path.getsize(test_path)} bytes")

# 测试不同路径
test_path2 = r"C:\Users\Neko\Desktop\素材拆分与分类\test_direct.jpg"
print(f"\n尝试写入直接路径: {test_path2}")
success2 = cv2.imwrite(test_path2, frame)
print(f"写入成功: {success2}")
print(f"文件存在: {os.path.exists(test_path2)}")

# 检查权限
import stat
if os.path.exists(test_dir):
    print(f"\n目录权限: {oct(os.stat(test_dir).st_mode)[-3:]}")

# 测试视频读取
print("\n=== 测试视频读取 ===")
test_video = r"C:\Users\Neko\Desktop\素材拆分与分类\test_video.mp4"
if os.path.exists(test_video):
    cap = cv2.VideoCapture(test_video)
    print(f"视频打开成功: {cap.isOpened()}")
    if cap.isOpened():
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"总帧数: {total_frames}, FPS: {fps}")
        
        ret, test_frame = cap.read()
        print(f"读取帧成功: {ret}")
        if ret:
            print(f"帧形状: {test_frame.shape}")
            test_write_path = r"C:\Users\Neko\Desktop\素材拆分与分类\test_frame.jpg"
            success3 = cv2.imwrite(test_write_path, test_frame)
            print(f"写入帧成功: {success3}")
            print(f"文件存在: {os.path.exists(test_write_path)}")
            if os.path.exists(test_write_path):
                print(f"文件大小: {os.path.getsize(test_write_path)} bytes")
        cap.release()
