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
            if os.path.getsize(full_path) < 10 * 1024 * 1024:  # 小于10MB
                test_images.append(full_path)
                if len(test_images) >= 2:
                    break
    if len(test_images) >= 2:
        break

if test_images:
    print(f"   ✓ 找到 {len(test_images)} 张测试图片")
    for img in test_images:
        print(f"     - {os.path.basename(img)}")
else:
    print("   ✗ 未找到测试图片，创建一个简单的测试")
    
    # 创建一个简单的测试图片文件（PBM格式）
    test_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\test_image"
    os.makedirs(test_dir, exist_ok=True)
    test_images = []
    
    # 创建一个简单的PBM格式图片（ASCII格式）
    pbm_content = "P1\n100 100\n" + "0 " * 50 + "1 " * 50 + "\n" * 99 + "0 " * 100
    test_img_path = os.path.join(test_dir, "test.pbm")
    with open(test_img_path, "w") as f:
        f.write(pbm_content)
    test_images.append(test_img_path)
    print(f"     - 创建了测试图片: {test_img_path}")

# 使用第一张图片测试
print("\n2. 测试单图片识别...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    prompt_text = "请描述这张图片的内容，用中文回答。"
    messages = [{
        "role": "user", 
        "content": [
            {"type": "text", "text": prompt_text},
            {"type": "image", "image": img_base64}
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
        print(f"   ✓ 模型调用成功")
        print(f"   模型回复: {content[:200]}")
    else:
        print(f"   ✗ 模型调用失败: {response.status_code}")
        print(f"   响应: {response.text}")
        
except Exception as e:
    print(f"   ✗ 调用失败: {e}")
    import traceback
    traceback.print_exc()

# 检查Ollama支持的模型
print("\n3. 检查Ollama可用模型...")
try:
    response = httpx.get("http://localhost:11434/api/tags", timeout=10)
    if response.status_code == 200:
        data = response.json()
        models = [m["name"] for m in data.get("models", [])]
        print(f"   ✓ Ollama服务运行正常")
        print(f"   可用模型: {models}")
        
        # 检查是否有视觉模型
        has_vl_model = any("vl" in m.lower() or "vision" in m.lower() for m in models)
        print(f"   是否有视觉模型: {'是' if has_vl_model else '否'}")
        
    else:
        print(f"   ✗ 获取模型列表失败: {response.status_code}")
        
except Exception as e:
    print(f"   ✗ 检查失败: {e}")

# 测试JSON格式输出
print("\n4. 测试JSON格式输出...")
try:
    with open(test_images[0], "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    prompt_text = """分析图片内容并输出JSON格式：{"category": "...", "product_category": "...", "tags": ["..."]}
category选项：product_showcase, lifestyle, cooking, beauty, fitness, uncategorized
product_category选项：cosmetics, food, electronics, clothing, other
tags：描述性标签列表"""
    
    messages = [{
        "role": "user", 
        "content": [
            {"type": "text", "text": prompt_text},
            {"type": "image", "image": img_base64}
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
        print(f"   ✓ JSON格式测试成功")
        print(f"   原始响应: {content[:300]}")
        
        # 尝试解析JSON
        import json
        try:
            json_result = json.loads(content)
            print(f"   ✓ JSON解析成功")
            print(f"   category: {json_result.get('category')}")
            print(f"   product_category: {json_result.get('product_category')}")
            print(f"   tags: {json_result.get('tags')}")
        except:
            print(f"   ✗ JSON解析失败")
            
except Exception as e:
    print(f"   ✗ 调用失败: {e}")

# 清理临时文件
print("\n5. 清理临时文件...")
test_dir = r"C:\Users\Neko\Desktop\素材拆分与分类\test_image"
if os.path.exists(test_dir):
    import shutil
    shutil.rmtree(test_dir)
    print(f"   ✓ 清理完成")

print("\n=== 测试完成 ===")
