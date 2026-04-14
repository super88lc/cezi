#!/usr/bin/env python3
"""
千帆(Qianfan) API 客户端
用于测字算事的AI深度分析

支持两种认证方式:
1. OAuth 2.0 (Access Key + Secret Key) - 传统方式
2. Bearer Token (API Key) - 新版 ERNIE API，直接使用
"""

import os
import json
import requests
from datetime import datetime

class QianfanClient:
    """千帆API客户端"""
    
    def __init__(self, access_key=None, secret_key=None, api_key=None):
        # 支持两种方式初始化
        self.access_key = access_key or os.getenv('QIANFAN_ACCESS_KEY', '')
        self.secret_key = secret_key or os.getenv('QIANFAN_SECRET_KEY', '')
        
        # 新版 ERNIE API Key (Bearer Token 方式)
        self.api_key = api_key or os.getenv('ERNIE_API_KEY', '') or os.getenv('QIANFAN_API_KEY', '')
        
        self.model_name = os.getenv('QIANFAN_MODEL_NAME', 'ERNIE-4.0-8K')
        self.access_token = None
        
        # 判断使用哪种认证方式
        self.use_bearer = bool(self.api_key)
        if self.use_bearer:
            print(f"[QianfanClient] 使用 Bearer Token 认证 (API Key)")
        elif self.access_key and self.secret_key:
            print(f"[QianfanClient] 使用 OAuth 2.0 认证 (Access Key + Secret Key)")
        else:
            print(f"[QianfanClient] ⚠️ 未配置任何认证方式")
        
    def get_access_token(self):
        """获取百度千帆access_token (OAuth方式)"""
        if self.access_token:
            return self.access_token
            
        if not self.access_key or not self.secret_key:
            return None
            
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.access_key}&client_secret={self.secret_key}"
        
        try:
            response = requests.post(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                return self.access_token
            else:
                print(f"[QianfanClient] 获取token失败: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"[QianfanClient] 获取token异常: {e}")
        
        return None
    
    def chat(self, messages, max_tokens=600, temperature=0.7):
        """调用千帆对话API"""
        
        # 使用 Bearer Token 方式 (新版 ERNIE API)
        if self.use_bearer:
            return self._chat_bearer(messages, max_tokens, temperature)
        
        # 使用 OAuth 2.0 方式 (传统方式)
        return self._chat_oauth(messages, max_tokens, temperature)
    
    def _chat_bearer(self, messages, max_tokens=600, temperature=0.7):
        """使用 Bearer Token 调用 ERNIE API (OpenAI兼容格式)"""
        
        base_url = "https://qianfan.baidubce.com/v2"
        url = f"{base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # OpenAI 兼容格式
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            print(f"[QianfanClient] 发送 Bearer Token 请求到 {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            raw_response = response.text
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content, raw_response
                return None, f"API响应格式错误: {raw_response[:200]}"
            else:
                error_msg = f"HTTP错误 {response.status_code}: {raw_response[:200]}"
                print(f"[QianfanClient] {error_msg}")
                return None, error_msg
                
        except Exception as e:
            error_msg = f"请求异常: {e}"
            print(f"[QianfanClient] {error_msg}")
            return None, error_msg
    
    def _chat_oauth(self, messages, max_tokens=600, temperature=0.7):
        """使用 OAuth 2.0 调用千帆 API (传统方式)"""
        
        token = self.get_access_token()
        if not token:
            return None, "无法获取access_token"
        
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.model_name}?access_token={token}"
        
        payload = {
            "messages": messages,
            "max_output_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(url, json=payload, timeout=45)
            raw_response = response.text
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result'], raw_response
                elif 'error_code' in result:
                    return None, f"API错误: {result.get('error_msg', '未知错误')}"
            else:
                return None, f"HTTP错误: {response.status_code}"
                
        except Exception as e:
            return None, str(e)
        
        return None, "未知错误"


def get_qianfan_deep_analysis(char, question, direction, time_info, analysis_data, meihua_data=None, client=None):
    """调用千帆进行深度个性化分析，返回(结果, prompt, 原始响应)"""
    
    # 根据问题类型提供更具体的分析方向
    question_type = ""
    if "考试" in question:
        question_type = "考试学业"
    elif "事业" in question or "工作" in question:
        question_type = "事业发展"
    elif "财运" in question or "钱" in question:
        question_type = "财富运势"
    elif "感情" in question or "婚姻" in question:
        question_type = "感情婚姻"
    elif "健康" in question:
        question_type = "健康状况"
    elif "出行" in question or "旅行" in question:
        question_type = "出行平安"
    else:
        question_type = "综合运势"
    
    # 梅花易数信息
    meihua_info = ""
    if meihua_data:
        gua = meihua_data.get('gua', '')
        meihua_info = f"""
梅花易数卦象：本卦{gua}（上卦{gua[0] if gua else '?'} + 下卦{gua[1] if len(gua) > 1 else '?'}）
动爻分析：{meihua_data.get('dongyao', '待定')}"""
    
    prompt = f"""你是一位德高望重的测字先生，用文言文为客人进行深度个性化分析。

【基本信息】
- 测字：{char}
- 提问：{question}（{question_type}）
- 方位：{direction}
- 时辰：{time_info.get('shichen', '未知')}（{time_info.get('day_gan', '')}日）
- 笔画：{analysis_data.get('strokes', 0)}画
- 五行：{analysis_data.get('wuxing', '未知')}行
- 结构：{analysis_data.get('structure', '未知')}
- 吉凶：{analysis_data.get('jixiong', '未知')}{meihua_info}

【分析要求】

1. **字形解字**（50字左右）
   - 分析「{char}」字的象形含义
   - 解读左右/上下/包围结构的象征意义

2. **五行分析**（30字左右）
   - {analysis_data.get('wuxing', '')}行与笔画数的关系
   - 五行平衡与否的运势影响

3. **{question_type}详解**（80字左右）
   - 针对「{question}」给出具体、可操作的建议
   - 结合时辰方位给出趋吉避凶的方法

4. **开运指引**（40字左右）
   - 适合的颜色、方位、数字
   - 今日宜忌

【风格要求】
- 文言文为主，夹杂白话解释
- 如古代算命先生语气
- 语温和但有自信
- 结论明确，不要模棱两可"""

    try:
        # 使用传入的client或创建新client
        if client is None:
            client = QianfanClient()
        
        messages = [{"role": "user", "content": prompt}]
        result, raw_response = client.chat(messages, max_tokens=600)
        
        if result:
            return result, prompt, raw_response
        return None, prompt, raw_response
        
    except Exception as e:
        print(f"千帆API错误: {e}")
        return None, prompt, str(e)


# 测试代码
if __name__ == "__main__":
    print("千帆客户端模块加载成功")
    
    # 检查认证方式
    api_key = os.getenv('ERNIE_API_KEY', '') or os.getenv('QIANFAN_API_KEY', '')
    access_key = os.getenv('QIANFAN_ACCESS_KEY', '')
    secret_key = os.getenv('QIANFAN_SECRET_KEY', '')
    
    if api_key:
        print(f"✅ 使用 Bearer Token 方式 (API Key: {api_key[:20]}...)")
        client = QianfanClient(api_key=api_key)
        # 测试调用
        messages = [{"role": "user", "content": "你好，请简单介绍一下自己"}]
        result, raw = client.chat(messages)
        if result:
            print(f"✅ 测试成功: {result[:100]}...")
        else:
            print(f"❌ 测试失败: {raw}")
    elif access_key and secret_key:
        print(f"✅ 使用 OAuth 2.0 方式 (Access Key: {access_key[:20]}...)")
    else:
        print("⚠️ 未配置任何 API Key")
        print("请设置以下环境变量之一:")
        print("  - ERNIE_API_KEY (推荐，Bearer Token方式)")
        print("  - QIANFAN_API_KEY")
        print("  - QIANFAN_ACCESS_KEY + QIANFAN_SECRET_KEY")
