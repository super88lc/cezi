#!/usr/bin/env python3
"""
测试千帆 API 连接
"""
import os
import sys
import requests
import json

# 加载 .env 文件
from pathlib import Path
def load_env():
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

load_env()

QIANFAN_ACCESS_KEY = os.getenv('QIANFAN_ACCESS_KEY', '')
QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY', '')

def get_access_token():
    """获取千帆访问令牌"""
    url = "https://iam.bj.baidubce.com/v1/BCE-BEARER/token"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"bce-v3/ALTAK/{QIANFAN_ACCESS_KEY}/{QIANFAN_SECRET_KEY}"
    }
    data = {
        "durationInSeconds": 86400,
        "acl": [
            {
                "service": "bce:cce",
                "region": "*",
                "effect": "Allow",
                "resource": ["*"],
                "permission": ["*"]
            }
        ]
    }
    
    print(f"请求 URL: {url}")
    print(f"Access Key: {QIANFAN_ACCESS_KEY[:20]}..." if len(QIANFAN_ACCESS_KEY) > 20 else f"Access Key: {QIANFAN_ACCESS_KEY}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"\n响应状态: {response.status_code}")
        print(f"响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('token', '')
            print(f"\n✅ 获取 Token 成功!")
            print(f"Token: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
            return token
        else:
            print(f"\n❌ 获取 Token 失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return None

def test_chat(token):
    """测试聊天 API"""
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "model": "ernie-4.0-8k-latest",
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍自己"}
        ],
        "stream": False
    }
    
    print(f"\n测试聊天 API...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"✅ 聊天测试成功!")
            print(f"回复: {content[:100]}..." if len(content) > 100 else f"回复: {content}")
            return True
        else:
            print(f"❌ 聊天测试失败: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("千帆 API 连接测试")
    print("="*50)
    
    if not QIANFAN_ACCESS_KEY or not QIANFAN_SECRET_KEY:
        print("❌ 错误: 未设置 QIANFAN_ACCESS_KEY 或 QIANFAN_SECRET_KEY")
        sys.exit(1)
    
    # 获取 Token
    token = get_access_token()
    if token:
        # 测试聊天
        test_chat(token)
    else:
        print("\n跳过聊天测试（Token 获取失败）")
