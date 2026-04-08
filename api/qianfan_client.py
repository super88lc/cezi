#!/usr/bin/env python3
"""
千帆(Qianfan) API 客户端
支持 ERNIE 系列模型
"""

import os
import requests
import json
from datetime import datetime


class QianfanClient:
    """千帆 API 客户端"""
    
    # API 端点
    AUTH_URL = "https://iam.bj.baidubce.com/v1/BCE-BEARER/token"
    CHAT_URL = "https://qianfan.baidubce.com/v2/chat/completions"
    
    # 支持的模型
    MODELS = {
        "ERNIE-4.0-8K": "ernie-4.0-8k-latest",
        "ERNIE-4.0-Turbo-8K": "ernie-4.0-turbo-8k",
        "ERNIE-3.5-8K": "ernie-3.5-8k",
        "ERNIE-Speed-8K": "ernie-speed-8k",
        "ERNIE-Lite-8K": "ernie-lite-8k"
    }
    
    def __init__(self, access_key=None, secret_key=None):
        """
        初始化客户端
        
        Args:
            access_key: 百度智能云 Access Key
            secret_key: 百度智能云 Secret Key
        """
        self.access_key = access_key or os.getenv('QIANFAN_ACCESS_KEY')
        self.secret_key = secret_key or os.getenv('QIANFAN_SECRET_KEY')
        self.model_name = os.getenv('QIANFAN_MODEL_NAME', 'ERNIE-4.0-8K')
        self._access_token = None
        self._token_expire_time = None
    
    def _get_access_token(self):
        """获取 Access Token（带缓存）"""
        # 检查缓存的 token 是否有效
        if self._access_token and self._token_expire_time:
            if datetime.now() < self._token_expire_time:
                return self._access_token
        
        # 请求新 token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bce-v1/{self.access_key}/{self.secret_key}"
        }
        
        try:
            response = requests.post(
                self.AUTH_URL,
                headers=headers,
                json={"durationInSeconds": 86400},  # 24小时
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get('token')
                # 设置过期时间（提前5分钟过期）
                expires_in = data.get('expireInSeconds', 86400)
                from datetime import timedelta
                self._token_expire_time = datetime.now() + timedelta(seconds=expires_in - 300)
                return self._access_token
            else:
                print(f"获取千帆 Token 失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"获取千帆 Token 出错: {e}")
            return None
    
    def chat(self, messages, max_tokens=1024, temperature=0.7):
        """
        调用千帆聊天接口
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成 token 数
            temperature: 温度参数
            
        Returns:
            (生成的文本, 原始响应)
        """
        token = self._get_access_token()
        if not token:
            return None, "Failed to get access token"
        
        # 获取模型 ID
        model_id = self.MODELS.get(self.model_name, self.model_name)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                self.CHAT_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            raw_response = response.text
            
            if response.status_code == 200:
                data = response.json()
                # 千帆返回格式与 OpenAI 兼容
                if 'choices' in data and len(data['choices']) > 0:
                    content = data['choices'][0].get('message', {}).get('content', '')
                    return content, raw_response
                return None, raw_response
            else:
                print(f"千帆 API 调用失败: {response.status_code} - {raw_response}")
                return None, raw_response
                
        except Exception as e:
            print(f"千帆 API 调用出错: {e}")
            return None, str(e)
    
    def get_model_list(self):
        """获取支持的模型列表"""
        return list(self.MODELS.keys())


def get_qianfan_deep_analysis(char, question, direction, time_info, analysis_data, meihua_data=None, client=None):
    """
    使用千帆模型进行深度分析
    
    Args:
        client: 可选，传入自定义 QianfanClient 实例（用于使用 Admin 配置的密钥）
    
    Returns:
        (分析结果, prompt, 原始响应)
    """
    if client is None:
        client = QianfanClient()
    
    # 判断问题类型
    question_type = "综合运势"
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
    
    # 梅花易数信息
    meihua_info = ""
    if meihua_data:
        gua = meihua_data.get('gua', '')
        meihua_info = f"""
梅花易数卦象：本卦{gua}（上卦{gua[0] if gua else '?'} + 下卦{gua[1] if len(gua) > 1 else '?'}）
动爻分析：{meihua_data.get('dongyao', '待定')}"""
    
    # 构建 Prompt
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
- 语气温和但有自信
- 结论明确，不要模棱两可"""
    
    messages = [{"role": "user", "content": prompt}]
    result, raw_response = client.chat(messages, max_tokens=600, temperature=0.7)
    
    return result, prompt, raw_response


# 测试代码
if __name__ == "__main__":
    # 测试
    client = QianfanClient()
    print("支持的模型:", client.get_model_list())
    
    # 测试对话
    messages = [{"role": "user", "content": "你好，请介绍一下千帆大模型"}]
    result, raw = client.chat(messages)
    if result:
        print("测试结果:", result[:100], "...")
    else:
        print("测试失败:", raw)