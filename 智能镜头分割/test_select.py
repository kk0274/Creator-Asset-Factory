import requests

print("=== 测试修复后的选择功能 ===")

# 测试选择单个场景
print("\n1. 测试选择单个场景...")
response = requests.post("http://localhost:8001/api/task/1/select/0?selected=true", timeout=10)
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   结果: {response.json()}")
else:
    print(f"   失败: {response.text}")

# 测试全选功能
print("\n2. 测试全选功能...")
response = requests.post("http://localhost:8001/api/task/1/select-all?selected=true", timeout=10)
print(f"   状态码: {response.status_code}")
if response.status_code == 200:
    print(f"   结果: {response.json()}")
else:
    print(f"   失败: {response.text}")

# 验证场景状态
print("\n3. 验证场景选择状态...")
response = requests.get("http://localhost:8001/api/task/1", timeout=10)
if response.status_code == 200:
    task = response.json()
    print(f"   场景总数: {len(task['scenes'])}")
    for i, scene in enumerate(task['scenes']):
        print(f"   场景 {i}: selected = {scene['selected']}")

print("\n=== 测试完成 ===")
