import requests

print("=== 测试Ollama服务 ===")

try:
    response = requests.get("http://localhost:11434/api/tags", timeout=10)
    if response.status_code == 200:
        result = response.json()
        models = [m["name"] for m in result.get("models", [])]
        print(f"✓ Ollama服务正常")
        print(f"  可用模型: {models}")
        if "qwen2.5-vl" in str(models):
            print("  ✓ qwen2.5-vl 模型已安装")
        else:
            print("  ✗ 需要安装 qwen2.5-vl 模型")
    else:
        print(f"✗ Ollama服务异常: {response.status_code}")
except Exception as e:
    print(f"✗ 无法连接Ollama: {e}")
    print("  请确保Ollama已启动: ollama serve")
