import os
import sys
import httpx
import base64

print("=== 测试Qwen2.5-VL模型图片识别能力 ===")

# 查找已存在的缩略图
print("\n1. 查找测试图片...")
test_images = []
for root, dirs, files in os.walk(r"C:\Users\Neko\Desktop\素材拆分与分类\data\videos"):
    for f in files:
        if f.lower().endswith(".jpg"):
            full_path = os.path.join(root, f)
            if os.path.getsize(full_path) < 10 * 1024 * 1024:
                test_images.append(full_path)
                break
    if test_images:
        break

if test_images:
    print(f"   ✓ 找到测试图片: {os.path.basename(test_images[0])}")
    print(f"   文件大小: {os.path.getsize(test_images[0])} bytes")
else:
    print("   ✗ 未找到测试图片")
    sys.exit(1)

# 测试描述性识别
print("\n2. 测试图片描述...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    img_data_url = f"data:image/jpeg;base64,{img_base64}"
    
    messages = [{
        "role": "user", 
        "content": f"请详细描述这张图片的内容：{img_data_url}"
    }]
    
    response = httpx.post(
        "http://localhost:11434/api/chat",
        json={"model": "qwen2.5vl:7b", "messages": messages, "stream": False},
        timeout=120
    )
    
    if response.status_code == 200:
        result = response.json()
        content = result["message"]["content"]
        print(f"   ✓ 成功！")
        print(f"   模型回复: {content}")
    else:
        print(f"   ✗ 失败: {response.status_code}")
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n=== 测试完成 ===")
