#!/usr/bin/env python3
"""
测试千帆 API - OpenAI 兼容接口
"""
import os
import sys
import requests
import json
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

QIANFAN_API_KEY = os.getenv('QIANFAN_API_KEY', '')

def test_chat_direct():
    """直接测试聊天 API - OpenAI 兼容接口"""
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {QIANFAN_API_KEY}"
    }
    data = {
        "model": "ernie-4.0-8k-latest",
        "messages": [
            {"role": "user", "content": "你好，请用一句话介绍自己"}
        ],
        "stream": False
    }
    
    print(f"请求 URL: {url}")
    print(f"API Key: {QIANFAN_API_KEY[:30]}..." if len(QIANFAN_API_KEY) > 30 else f"API Key: {QIANFAN_API_KEY}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        print(f"\n响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"✅ 测试成功!")
            print(f"回复: {content[:100]}..." if len(content) > 100 else f"回复: {content}")
            return True
        else:
            print(f"❌ 测试失败: {response.status_code}")
            print(f"响应: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("千帆 API 测试 - OpenAI 兼容接口")
    print("="*50)
    
    if not QIANFAN_API_KEY:
        print("❌ 错误: 未设置 QIANFAN_API_KEY")
        sys.exit(1)
    
    test_chat_direct()
