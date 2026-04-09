#!/usr/bin/env python3
"""
千帆(Qianfan) API 客户端
用于测字算事的AI深度分析
"""

import os
import json
import requests
from datetime import datetime

class QianfanClient:
    """千帆API客户端"""
    
    def __init__(self, access_key=None, secret_key=None):
        self.access_key = access_key or os.getenv('QIANFAN_ACCESS_KEY', '')
        self.secret_key = secret_key or os.getenv('QIANFAN_SECRET_KEY', '')
        self.model_name = 'ERNIE-4.0-8K'
        self.endpoint = 'https://qianfan.baidubce.com/v2'
        self.access_token = None
        
    def get_access_token(self):
        """获取百度千帆access_token"""
        if self.access_token:
            return self.access_token
            
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.access_key}&client_secret={self.secret_key}"
        
        try:
            response = requests.post(url, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get('access_token')
                return self.access_token
        except Exception as e:
            print(f"获取千帆token失败: {e}")
        
        return None
    
    def chat(self, messages, max_tokens=600, temperature=0.7):
        """调用千帆对话API"""
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
- 语气温和但有自信
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
    # 测试客户端初始化
    client = QianfanClient()
    print(f"Access Key: {client.access_key[:10] if client.access_key else '未设置'}...")
    print(f"Model: {client.model_name}")
