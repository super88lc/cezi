#!/usr/bin/env python3
"""
测字算事小程序 - 完整版后端
整合测字算法 + OCR + 微信支付
"""


MINIMAX_API_KEY = "sk-cp-Tmj3A5rpV32ER1gQvhW4jaC5rQ66nFglQfabG8CtLITQpPSjsmj50Ct6jh6i_G9fGugGyAYV744LhdVJ9irPGmgRgOrIGa6y--HBGAhWyGGVJTSmrpiPTro"

def get_minimax_deep_analysis(char, question, direction, time_info, analysis_data, meihua_data=None):
    """调用MiniMax进行深度个性化分析"""
    
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


from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
import time
import random
import string
import hashlib
import requests
from cezi_core_v3 import generate_enhanced_result, format_verbose

app = Flask(__name__, template_folder='templates')
CORS(app)

# ========== 配置 ==========
# 百度OCR
BAIDU_API_KEY = "yDxNzWrNG1maoB9Ky7nUjqdc"
BAIDU_SECRET_KEY = "qoMLfNvLpaG8YhhMvm7HzezBDH5VyG1I"

# 微信支付
WECHAT_MCH_ID = os.environ.get("WECHAT_MCH_ID", "")
WECHAT_API_KEY = os.environ.get("WECHAT_API_KEY", "")
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")

# 会员套餐
PLANS = {
    "monthly": {"name": "月卡会员", "price": 30, "days": 30},
    "quarterly": {"name": "季卡会员", "price": 80, "days": 90},
    "yearly": {"name": "年卡会员", "price": 298, "days": 365}
}

# 内存存储（生产用数据库）
users = {}
orders = {}

# ========== 工具函数 ==========

def get_user(openid):
    if openid not in users:
        users[openid] = {
            "level": "free",
            "daily_count": 0,
            "last_date": "",
            "history": []
        }
    return users[openid]

def check_limit(openid):
    user = get_user(openid)
    today = time.strftime("%Y-%m-%d")
    
    if user["last_date"] != today:
        user["daily_count"] = 0
        user["last_date"] = today
    
    if user["level"] != "free":
        return True
    
    return user["daily_count"] < 3  # 免费用户每天3次

def increment_count(openid):
    user = get_user(openid)
    today = time.strftime("%Y-%m-%d")
    
    if user["last_date"] != today:
        user["daily_count"] = 0
        user["last_date"] = today
    
    user["daily_count"] += 1

def generate_nonce():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

# ========== 页面路由 ==========

@app.route("/")
def index():
    return render_template("index.html")

# ========== 测字API ==========

@app.route("/api/cezi", methods=["POST"])
def cezi():
    """测字接口"""
    data = request.json
    char = data.get("char", "").strip()
    question = data.get("question", "")
    openid = data.get("openid", "anonymous")
    
    if not char:
        return jsonify({"error": "请输入要测的字"}), 400
    
    char = char[0]  # 只测第一个字
    
    # 检查次数
    if not check_limit(openid):
        return jsonify({
            "error": "今日免费次数已用完",
            "upgrade": True,
            "message": "开通会员享受无限次测字"
        }), 403
    
    # 生成结果 - 使用V3增强版
    result = generate_enhanced_result(char, question, data.get("direction", "南"))
    
    # 调用MiniMax进行深度分析（传入完整数据）
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
    
    increment_count(openid)
    
    # 保存历史
    user = get_user(openid)
    user["history"].append({
        "char": char,
        "time": time.time(),
        "brief": f"{char}字，{result['analysis']['jixiong']}"
    })
    
    # 格式化输出
    verbose_text = format_verbose(result)
    
    return jsonify({
        "success": True,
        "data": result,
        "verbose": verbose_text,
        "remaining": PLANS["monthly"]["days"] - user["daily_count"] if user["level"] == "free" else "无限"
    })

# ========== OCR API ==========

def get_baidu_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    resp = requests.post(url, params=params, timeout=10)
    return resp.json().get("access_token")

@app.route("/api/ocr", methods=["POST"])
def ocr():
    """OCR识别"""
    data = request.json
    image = data.get("image", "")
    provider = data.get("provider", "baidu")
    
    if not image:
        return jsonify({"error": "请上传图片"}), 400
    
    # 去除前缀
    if "," in image:
        image = image.split(",")[1]
    
    if not BAIDU_API_KEY:
        return jsonify({
            "success": True,
            "char": None,
            "message": "OCR服务配置中，请先输入文字"
        })
    
    try:
        token = get_baidu_token()
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token={token}"
        
        resp = requests.post(url, data={"image": image}, timeout=10)
        result = resp.json()
        
        if "words_result" in result and result["words_result"]:
            words = result["words_result"]
            if words:
                first_char = words[0].get("words", "")[0] if words[0].get("words") else ""
                return jsonify({
                    "success": True,
                    "char": first_char,
                    "all_chars": [w.get("words", "") for w in words],
                    "confidence": words[0].get("probability", {}).get("average", 0)
                })
        
        return jsonify({"success": False, "error": "未识别到文字"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/ocr/status", methods=["GET"])
def ocr_status():
    return jsonify({"configured": bool(BAIDU_API_KEY)})

# ========== 微信支付 ==========

@app.route("/api/payment/create", methods=["POST"])
def create_payment():
    """创建支付订单"""
    data = request.json
    plan = data.get("plan", "monthly")
    openid = data.get("openid", "")
    
    if plan not in PLANS:
        return jsonify({"error": "无效套餐"}), 400
    
    if not openid:
        return jsonify({"error": "需要登录"}), 400
    
    plan_info = PLANS[plan]
    order_id = f"CEZI{int(time.time())}{random.randint(1000,9999)}"
    
    # 保存订单
    orders[order_id] = {
        "plan": plan,
        "openid": openid,
        "price": plan_info["price"],
        "status": "pending",
        "time": time.time()
    }
    
    # TODO: 实际调用微信支付API
    # 返回模拟支付参数
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "plan": plan,
        "price": plan_info["price"],
        "message": "微信支付配置中，请联系管理员"
    })

@app.route("/api/payment/plans", methods=["GET"])
def get_plans():
    """获取套餐列表"""
    return jsonify({
        "success": True,
        "plans": [
            {"id": k, "name": v["name"], "price": v["price"], "days": v["days"]}
            for k, v in PLANS.items()
        ]
    })

# ========== 用户系统 ==========

@app.route("/api/user/login", methods=["POST"])
def login():
    """模拟登录"""
    data = request.json
    code = data.get("code", "")
    
    # TODO: 真实微信登录
    openid = f"user_{code[:8]}" if code else "anonymous"
    user = get_user(openid)
    
    return jsonify({
        "success": True,
        "openid": openid,
        "level": user["level"],
        "daily_count": user["daily_count"]
    })

@app.route("/api/user/info", methods=["GET"])
def user_info():
    """获取用户信息"""
    openid = request.args.get("openid", "anonymous")
    user = get_user(openid)
    
    return jsonify({
        "success": True,
        "level": user["level"],
        "daily_count": user["daily_count"],
        "history_count": len(user["history"])
    })

@app.route("/api/user/history", methods=["GET"])
def user_history():
    """历史记录"""
    openid = request.args.get("openid", "anonymous")
    user = get_user(openid)
    
    return jsonify({
        "success": True,
        "history": user["history"][-20:]
    })

# ========== 状态 ==========

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "version": "1.0.0",
        "ocr": {"baidu": bool(BAIDU_API_KEY)},
        "payment": {"wechat": bool(WECHAT_MCH_ID)},
        "features": {
            "cezi": True,
            "ocr": True,
            "membership": True,
            "history": True
        }
    })

# ========== 启动 ==========

if __name__ == "__main__":
    print("=" * 50)
    print("🔮 测字算事小程序后端")
    print("=" * 50)
    print(f"📍 地址: http://localhost:5000")
    print(f"🔑 OCR: {'✅ 已配置' if BAIDU_API_KEY else '❌ 未配置'}")
    print(f"💰 支付: {'✅ 已配置' if WECHAT_MCH_ID else '❌ 未配置'}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: (status, headers))
