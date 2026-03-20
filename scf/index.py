# -*- coding: utf-8 -*-
"""
腾讯云函数 - 测字应用
部署到 SCF 后，通过 API Gateway 触发
"""

import json
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入核心模块
from cezi_core_v3 import generate_enhanced_result

# MiniMax API Key
MINIMAX_API_KEY = "sk-cp-Tmj3A5rpV32ER1gQvhW4jaC5rQ66nFglQfabG8CtLITQpPSjsmj50Ct6jh6i_G9fGugGyAYV744LhdVJ9irPGmgRgOrIGa6y--HBGAhWyGGVJTSmrpiPTro"

def get_minimax_deep_analysis(char, question, direction, time_info, analysis_data, meihua_data=None):
    """调用MiniMax进行深度个性化分析"""
    import requests
    
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
    
    meihua_info = ""
    if meihua_data:
        gua = meihua_data.get('gua', '')
        meihua_info = f"\n梅花易数卦象：本卦{gua}（上卦{gua[0] if gua else '?'} + 下卦{gua[1] if len(gua) > 1 else '?'}）"
    
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
        response = requests.post(
            "https://api.minimaxi.com/anthropic/v1/messages",
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "MiniMax-M2.5",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'content' in result:
                for item in result['content']:
                    if item.get('type') == 'text':
                        return item.get('text', '')
        return None
    except Exception as e:
        print(f"MiniMax API error: {e}")
        return None


def main_handler(event, context):
    """云函数入口"""
    # 处理不同的请求类型
    if event.get('httpMethod'):
        # API Gateway 请求
        return handle_http(event)
    else:
        # 测试事件
        return {'statusCode': 200, 'body': json.dumps({'message': '测字服务运行中'})}


def handle_http(event):
    """处理HTTP请求"""
    method = event.get('httpMethod')
    path = event.get('path', '')
    
    # 设置CORS
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
    }
    
    # 处理OPTIONS请求
    if method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    # 测字API
    if path == '/api/cezi' and method == 'POST':
        return handle_cezi(event, headers)
    
    # OCR API (需要额外配置)
    if path == '/api/ocr' and method == 'POST':
        return handle_ocr(event, headers)
    
    # 默认返回
    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'error': 'Not found'})
    }


def handle_cezi(event, headers):
    """处理测字请求"""
    try:
        # 解析请求体
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        char = body.get('char', '')
        question = body.get('question', '综合运势')
        direction = body.get('direction', '南')
        
        if not char:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '缺少char参数'})
            }
        
        # 生成结果
        result = generate_enhanced_result(char, question, direction)
        result['char'] = char
        result['question'] = question
        
        # 调用MiniMax深度分析
        try:
            deep_analysis = get_minimax_deep_analysis(
                char, 
                question, 
                result.get('meihua', {}).get('direction', '南'),
                result.get('meihua', {}).get('time', {}),
                result.get('analysis', {}),
                result.get('meihua', {})
            )
            if deep_analysis:
                result['deep_analysis'] = deep_analysis
        except Exception as e:
            print(f"Deep analysis error: {e}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'data': result}, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


def handle_ocr(event, headers):
    """处理OCR请求（需要配置OCR服务）"""
    return {
        'statusCode': 501,
        'headers': headers,
        'body': json.dumps({'error': 'OCR服务暂未开通，请使用手动输入'})
    }


if __name__ == '__main__':
    # 本地测试
    test_event = {
        'httpMethod': 'POST',
        'path': '/api/cezi',
        'body': json.dumps({'char': '好', 'question': '事业'})
    }
    result = main_handler(test_event, None)
    print(result)
