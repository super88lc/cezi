#!/usr/bin/env python3
"""测试修复后的API功能"""

import requests
import json

BASE_URL = "http://localhost:3000"

def test_api(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        return r.status_code, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return -1, str(e)

print("="*60)
print("测字算事 - Admin API 功能测试")
print("="*60)

# 测试Prompt列表
print("\n1. 测试 /api/admin/prompt/list")
status, data = test_api("/api/admin/prompt/list")
print(f"   状态: {status}")
print(f"   结果: {'✅ 成功' if status == 200 else '❌ 失败'}")

# 测试模型列表
print("\n2. 测试 /api/admin/models/list")
status, data = test_api("/api/admin/models/list")
print(f"   状态: {status}")
if status == 200 and isinstance(data, list):
    print(f"   结果: ✅ 成功，找到 {len(data)} 个模型")
    if data:
        key_display = data[0].get('api_key', '')
        print(f"   API Key显示: {key_display} {'✅ 已隐藏' if '*' in key_display else '❌ 未隐藏'}")
else:
    print(f"   结果: ❌ 失败")

# 测试获取单个模型
print("\n3. 测试 /api/admin/models/1")
status, data = test_api("/api/admin/models/1")
print(f"   状态: {status}")
print(f"   结果: {'✅ 成功' if status == 200 else '❌ 失败'}")

# 测试历史记录
print("\n4. 测试 /api/admin/history/list")
status, data = test_api("/api/admin/history/list?page=1&limit=10")
print(f"   状态: {status}")
if status == 200:
    print(f"   结果: ✅ 成功")
else:
    print(f"   结果: ❌ 失败")

# 测试Prompt删除
print("\n5. 测试 /api/admin/prompt/delete")
status, data = test_api("/api/admin/prompt/delete", "POST", {"id": 999})
print(f"   状态: {status}")
print(f"   结果: {'✅ 端点存在' if status != 404 else '❌ 端点不存在'}")

# 测试历史删除
print("\n6. 测试 /api/admin/history/delete")
status, data = test_api("/api/admin/history/delete", "POST", {"id": 999})
print(f"   状态: {status}")
print(f"   结果: {'✅ 端点存在' if status != 404 else '❌ 端点不存在'}")

# 测试模型删除
print("\n7. 测试 /api/admin/models/delete")
status, data = test_api("/api/admin/models/delete", "POST", {"id": 999})
print(f"   状态: {status}")
print(f"   结果: {'✅ 端点存在' if status != 404 else '❌ 端点不存在'}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
