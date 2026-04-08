#!/usr/bin/env python3
"""
测字算事 - 全链路测试脚本
"""
import requests
import json
import time
import sys
import subprocess
import threading

API_BASE = "http://localhost:5003"

def start_server():
    """启动本地服务器"""
    print("🚀 启动本地服务器...")
    
    # 后台启动服务器
    proc = subprocess.Popen(
        [sys.executable, "-c", """
from api.cezi import app
app.run(port=5003, debug=False, use_reloader=False, threaded=True)
"""],
        cwd="/Users/apple/.openclaw/workspace/zi-cesuan",
        env={"PATH": "/opt/homebrew/bin:/usr/local/bin:" + subprocess.os.environ.get("PATH", "")},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 等待服务器启动
    for i in range(10):
        try:
            requests.get(f"{API_BASE}/api/status", timeout=2)
            print("   ✅ 服务器已就绪")
            return proc
        except:
            time.sleep(1)
    
    print("   ❌ 服务器启动失败")
    return None

def test_api(endpoint, method="POST", data=None, expected_status=200):
    """测试单个API"""
    url = f"{API_BASE}{endpoint}"
    print(f"\n🧪 测试: {method} {endpoint}")
    print(f"   请求数据: {data}")
    
    try:
        if method == "POST":
            resp = requests.post(url, json=data, timeout=30)
        else:
            resp = requests.get(url, timeout=10)
        
        print(f"   状态码: {resp.status_code}")
        
        if resp.status_code == expected_status:
            print("   ✅ 通过")
            try:
                return resp.json()
            except:
                return resp.text
        else:
            print(f"   ❌ 失败 - 期望 {expected_status}, 实际 {resp.status_code}")
            print(f"   响应: {resp.text[:500]}")
            return None
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return None

def test_full_flow():
    """完整流程测试"""
    print("=" * 60)
    print("🔮 测字算事 - 全链路测试")
    print("=" * 60)
    
    # 启动服务器
    server_proc = start_server()
    if not server_proc:
        return
    
    try:
        # 1. 测试首页
        print("\n📄 1. 测试首页")
        resp = requests.get(f"{API_BASE}/", timeout=10)
        print(f"   状态: {resp.status_code}")
        if resp.status_code == 200 and "测字" in resp.text:
            print("   ✅ 首页正常 (包含测字内容)")
        else:
            print("   ❌ 首页失败或内容异常")
        
        # 2. 测试状态接口
        print("\n📊 2. 测试状态接口")
        result = test_api("/api/status", method="GET")
        if result:
            print(f"   版本: {result.get('version')}")
        
        # 3. 测试测字接口 - 完整流程
        print("\n🔮 3. 测试测字接口")
        
        test_cases = [
            {"char": "测", "question": "事业发展"},
            {"char": "运", "question": "财运如何"},
            {"char": "测", "question": "综合运势"},
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n   --- 测试用例 {i}: {case['char']} - {case['question']} ---")
            result = test_api("/api/cezi", data=case)
            
            if result and result.get('success'):
                print(f"   ✅ 成功")
                print(f"   字: {result.get('data', {}).get('char')}")
                print(f"   笔画: {result.get('data', {}).get('analysis', {}).get('strokes')}")
                print(f"   五行: {result.get('data', {}).get('analysis', {}).get('wuxing')}")
                print(f"   吉凶: {result.get('data', {}).get('analysis', {}).get('jixiong')}")
                print(f"   剩余次数: {result.get('remaining')}")
            else:
                print(f"   ❌ 失败: {result}")
        
        # 4. 测试OCR接口
        print("\n📷 4. 测试OCR接口")
        test_api("/api/ocr", data={"image": "test"})
        
        # 5. 测试用户接口
        print("\n👤 5. 测试用户接口")
        test_api("/api/user/login", data={"code": "test123"})
        
        print("\n" + "=" * 60)
        print("✅ 测试完成")
        print("=" * 60)
        
    finally:
        # 关闭服务器
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    test_full_flow()
