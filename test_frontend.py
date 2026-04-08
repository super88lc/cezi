#!/usr/bin/env python3
"""
前端模拟测试 - 模拟浏览器调用API
"""
import requests
import json
import time

# 使用Vercel生产环境
API_BASE = "https://zi-cesuan.vercel.app"

def test_frontend_flow():
    """模拟前端完整流程"""
    print("=" * 60)
    print("🌐 前端模拟测试 - 模拟浏览器调用")
    print("=" * 60)
    
    # 1. 模拟前端获取首页
    print("\n📄 1. 模拟获取首页")
    resp = requests.get(API_BASE + "/", timeout=30)
    print(f"   状态: {resp.status_code}")
    print(f"   内容长度: {len(resp.text)} 字符")
    if "测字" in resp.text:
        print("   ✅ 首页包含测字内容")
    else:
        print("   ⚠️ 首页内容异常")
    
    # 2. 模拟前端发送测字请求
    print("\n🔮 2. 模拟前端POST /api/cezi")
    
    payload = {
        "char": "测",
        "question": "事业发展",
        "openid": "guest_" + str(int(time.time()))
    }
    
    print(f"   请求体: {json.dumps(payload, ensure_ascii=False)}")
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        resp = requests.post(
            API_BASE + "/api/cezi",
            json=payload,
            headers=headers,
            timeout=45
        )
        print(f"   状态码: {resp.status_code}")
        print(f"   响应头: {dict(resp.headers)}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✅ 成功")
            print(f"   响应: {json.dumps(data, ensure_ascii=False)[:300]}...")
        else:
            print(f"   ❌ 失败: {resp.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时 (45秒)")
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ 连接错误: {e}")
    except Exception as e:
        print(f"   ❌ 异常: {e}")
    
    # 3. 检查CORS头
    print("\n🔍 3. 检查CORS配置")
    resp = requests.options(API_BASE + "/api/cezi", timeout=10)
    print(f"   OPTIONS状态: {resp.status_code}")
    print(f"   Access-Control-Allow-Origin: {resp.headers.get('Access-Control-Allow-Origin', '未设置')}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_frontend_flow()
