import os
import sys
import httpx
import base64

print("=== 测试Qwen2.5-VL模型图片识别能力 ===")

# 查找已存在的测试图片
print("\n1. 查找测试图片...")
test_images = []
for root, dirs, files in os.walk(r"C:\Users\Neko\Desktop\素材拆分与分类"):
    for f in files:
        if f.lower().endswith((".jpg", ".png")):
            full_path = os.path.join(root, f)
            if os.path.getsize(full_path) < 10 * 1024 * 1024:
                test_images.append(full_path)
                break
    if test_images:
        break

if test_images:
    print(f"   ✓ 找到测试图片: {os.path.basename(test_images[0])}")
else:
    print("   ✗ 未找到测试图片")
    sys.exit(1)

# 测试不同的API格式
print("\n2. 测试不同的API格式...")

# 格式1: 使用URL格式（Ollama推荐格式）
print("\n   格式1: 使用data URL...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # 使用data URL格式
    img_data_url = f"data:image/jpeg;base64,{img_base64}"
    
    messages = [{
        "role": "user", 
        "content": f"请描述这张图片的内容：{img_data_url}"
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
        print(f"   回复: {content[:200]}")
    else:
        print(f"   ✗ 失败: {response.status_code}")
        
except Exception as e:
    print(f"   ✗ 失败: {e}")

# 格式2: 使用tools格式
print("\n   格式2: 使用tools格式...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    messages = [{
        "role": "user", 
        "content": [
            {"type": "text", "text": "请描述图片内容"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
        ]
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
        print(f"   回复: {content[:200]}")
    else:
        print(f"   ✗ 失败: {response.status_code}")
        
except Exception as e:
    print(f"   ✗ 失败: {e}")

# 格式3: 直接在content中嵌入base64
print("\n   格式3: 直接嵌入base64...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    messages = [{
        "role": "user", 
        "content": f"![image](data:image/jpeg;base64,{img_base64})\n请描述这张图片"
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
        print(f"   回复: {content[:200]}")
    else:
        print(f"   ✗ 失败: {response.status_code}")
        
except Exception as e:
    print(f"   ✗ 失败: {e}")

print("\n=== 测试完成 ===")
