#!/usr/bin/env python3
"""
测字算事小程序 - 完整版后端
整合测字算法 + OCR + 微信支付
支持 MiniMax / 千帆(Qianfan) / OpenAI 等多模型
"""

import os
import sys

# 添加父目录到路径以导入本地模块（必须在其他导入之前）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API Keys 从环境变量读取
MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY', '')
QIANFAN_ACCESS_KEY = os.getenv('QIANFAN_ACCESS_KEY', '')
QIANFAN_SECRET_KEY = os.getenv('QIANFAN_SECRET_KEY', '')

# 导入千帆客户端
try:
    from qianfan_client import QianfanClient, get_qianfan_deep_analysis
    QIANFAN_AVAILABLE = True
except ImportError as e:
    QIANFAN_AVAILABLE = False
    print(f"⚠️ 千帆客户端不可用: {e}")

def get_minimax_deep_analysis(char, question, direction, time_info, analysis_data, meihua_data=None):
    """调用MiniMax进行深度个性化分析，返回(结果, prompt, 原始响应)"""
    
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
        
        raw_response = response.text  # 保存原始响应
        if response.status_code == 200:
            result = response.json()
            if 'content' in result:
                for item in result['content']:
                    if item.get('type') == 'text':
                        return item.get('text', ''), prompt, raw_response
        return None, prompt, raw_response
    except Exception as e:
        print(f"MiniMax API error: {e}")
        return None, prompt, str(e)


from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import time
import random
import string
import hashlib
import requests

# 导入本地模块（sys.path已在文件顶部设置）
from cezi_core_v3 import generate_enhanced_result, format_verbose

app = Flask(__name__, template_folder='templates')
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}}, supports_credentials=True)

# ========== Admin后台管理 ==========
try:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    print("✅ Admin routes registered")
except ImportError as e:
    print(f"⚠️ Admin routes not available: {e}")

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

import os

@app.route("/")
def index():
    # 直接读取静态HTML文件
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'index.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/admin")
def admin_page():
    # 读取管理后台HTML
    admin_path = os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html')
    try:
        with open(admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 如果是重定向页面，直接返回内嵌的管理界面
            if 'Redirecting' in content:
                from admin.app import admin_html
                return admin_html, 200, {'Content-Type': 'text/html'}
            return content, 200, {'Content-Type': 'text/html'}
    except Exception as e:
        return f"Error: {str(e)}", 500

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
    
    # 调用AI模型进行深度分析（根据配置选择 MiniMax 或 千帆）
    llm_prompt = ""
    llm_response = ""
    model_used = "minimax"  # 默认模型
    
    try:
        # 获取当前激活的模型配置
        # 使用本模块中已定义的 load_data 函数
        admin_data = load_data()
        models = admin_data.get('models', [])
        active_model = None
        for m in models:
            if m.get('is_active'):
                active_model = m
                break
        
        # 如果没有配置，使用默认
        if not active_model and models:
            active_model = models[0]
        
        # 根据模型类型调用不同的API
        if active_model:
            provider = active_model.get('provider', 'minimax')
            model_used = provider
            
            if provider == 'qianfan' and QIANFAN_AVAILABLE:
                # 使用千帆模型 - 优先使用模型配置中的密钥，否则使用环境变量
                access_key = active_model.get('access_key') or QIANFAN_ACCESS_KEY
                secret_key = active_model.get('secret_key') or QIANFAN_SECRET_KEY
                
                if access_key and secret_key:
                    # 创建临时客户端使用模型配置的密钥
                    from qianfan_client import QianfanClient
                    client = QianfanClient(access_key=access_key, secret_key=secret_key)
                    
                    # 获取模型名称
                    model_name = active_model.get('model_name', 'ERNIE-4.0-8K')
                    if model_name:
                        client.model_name = model_name
                    
                    deep_analysis, llm_prompt, llm_response = get_qianfan_deep_analysis(
                        char, 
                        question, 
                        result.get('meihua', {}).get('direction', '南'),
                        result.get('meihua', {}).get('time', {}),
                        result.get('analysis', {}),
                        result.get('meihua', {}),
                        client=client  # 传入自定义客户端
                    )
            elif provider == 'minimax' and MINIMAX_API_KEY:
                # 使用 MiniMax 模型
                deep_analysis, llm_prompt, llm_response = get_minimax_deep_analysis(
                    char, 
                    question, 
                    result.get('meihua', {}).get('direction', '南'),
                    result.get('meihua', {}).get('time', {}),
                    result.get('analysis', {}),
                    result.get('meihua', {})
                )
            else:
                # 默认使用 MiniMax
                deep_analysis, llm_prompt, llm_response = get_minimax_deep_analysis(
                    char, 
                    question, 
                    result.get('meihua', {}).get('direction', '南'),
                    result.get('meihua', {}).get('time', {}),
                    result.get('analysis', {}),
                    result.get('meihua', {})
                )
        else:
            # 默认使用 MiniMax
            deep_analysis, llm_prompt, llm_response = get_minimax_deep_analysis(
                char, 
                question, 
                result.get('meihua', {}).get('direction', '南'),
                result.get('meihua', {}).get('time', {}),
                result.get('analysis', {}),
                result.get('meihua', {})
            )
        
        if deep_analysis:
            result['deep_analysis'] = deep_analysis
            result['model_used'] = model_used
    except Exception as e:
        print(f"Deep analysis error: {e}")
        result['model_used'] = model_used
    
    increment_count(openid)
    
    # 保存用户历史（内存中，完整保存）
    user = get_user(openid)
    user["history"].append({
        "char": char,
        "time": time.time(),
        "brief": f"{char}字，{result['analysis']['jixiong']}"
    })
    
    # 格式化输出
    verbose_text = format_verbose(result)
    
    # 保存服务器端历史（Redis，最多100条）
    direction = data.get("direction", "南")
    time_info = result.get('meihua', {}).get('time', {}).get('shichen', '-')
    model_name = 'MiniMax-M2.5'  # 当前使用的模型
    
    # 获取完整的verbose结果作为展示
    display_result = verbose_text[:500] if verbose_text else result.get('conclusion', '')
    
    add_server_history({
        "id": int(time.time() * 1000),
        "char": char,
        "question": question,
        "direction": direction,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "time_info": time_info,
        "model_name": model_name,
        "result": result['analysis']['jixiong'],
        "prompt": llm_prompt,
        "llm_response": llm_response,
        "display_result": display_result,
        "openid": openid[:8] + "***"  # 脱敏处理
    })
    
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

@app.route("/api/health", methods=["GET"])
def health():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "version": "1.0.0"
    })

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
    # 获取端口，优先从环境变量读取，默认5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# Vercel handler - export app for Vercel
# The app is already defined above as `app`


# ========== Admin API (支持Vercel KV/Redis或本地文件) ==========
import os
import json
import datetime
from flask import jsonify

# Vercel 无服务器环境使用 /tmp 目录（唯一可写目录）
DATA_DIR = '/tmp'
DATA_FILE = os.path.join(DATA_DIR, 'admin_data.json')
DATA_KEY = 'cezi_admin_data'
MAX_SERVER_HISTORY = 100  # 服务器端最多保留100条

# 缓存客户端连接
_kv_client = None

def get_kv_client():
    """获取KV客户端，使用缓存连接"""
    global _kv_client
    if _kv_client is not None:
        return _kv_client
    
    kv_url = os.environ.get('KV_URL') or os.environ.get('REDIS_URL')
    if not kv_url:
        _kv_client = None
        return None
    try:
        import redis
        _kv_client = redis.from_url(kv_url)
        return _kv_client
    except Exception as e:
        print(f"Redis connection error: {e}")
        _kv_client = None
        return None

def load_data():
    """加载全部数据（包含prompts、models和server_history）"""
    # 优先使用 Vercel KV
    client = get_kv_client()
    if client:
        try:
            data = client.get(DATA_KEY)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Load data error: {e}")
    
    # 回退到本地文件
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {"prompts": [], "models": [], "server_history": []}

def save_data(data):
    """保存全部数据（包含prompts、models和server_history）"""
    json_str = json.dumps(data, ensure_ascii=False)
    
    # 优先使用 Vercel KV
    client = get_kv_client()
    if client:
        try:
            client.set(DATA_KEY, json_str)
            return
        except Exception as e:
            print(f"Save data error: {e}")
    
    # 回退到本地文件
    with open(DATA_FILE, 'w') as f:
        f.write(json_str)

def add_server_history(item):
    """添加服务器端历史记录（与prompts/models保存在同一Redis key中）"""
    data = load_data()
    if 'server_history' not in data:
        data['server_history'] = []
    
    data['server_history'].append(item)
    
    # 只保留最近100条
    if len(data['server_history']) > MAX_SERVER_HISTORY:
        data['server_history'] = data['server_history'][-MAX_SERVER_HISTORY:]
    
    save_data(data)

def load_server_history():
    """加载服务器端历史记录"""
    data = load_data()
    return data.get('server_history', [])

def init_admin_data():
    data = load_data()
    if not data.get('prompts'):
        data['prompts'] = [{
            "id": 1,
            "name": "默认模板",
            "template": "你是一位精通易经的测字先生，为人测字解惑。\n\n测字信息：\n- 所测之字：{char}\n- 所问之事：{question}\n- 测字方位：{direction}\n- 测字时辰：{time}\n\n请根据以上信息，以古代算命先生的语气对此字进行解析。要求：\n1. 先解释字形结构与含义\n2. 结合五行笔画分析\n3. 结合梅花易数解读方位与时辰\n4. 给出针对所问之事的具体建议\n5. 语气要像一位经验丰富的老师傅，不要像AI",
            "is_active": 1,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }]
    if not data.get('models'):
        now = datetime.datetime.now().isoformat()
        data['models'] = [
            {
                "id": 1, "name": "MiniMax", "provider": "minimax", "api_key": "", 
                "endpoint": "https://api.minimaxi.com/anthropic/v1", "model_name": "MiniMax-M2.5",
                "is_active": 0, "created_at": now, "updated_at": now
            },
            {
                "id": 2, "name": "千帆ERNIE-4.0", "provider": "qianfan",
                "access_key": "", "secret_key": "",
                "endpoint": "https://qianfan.baidubce.com/v2", "model_name": "ERNIE-4.0-8K",
                "is_active": 1, "created_at": now, "updated_at": now
            }
        ]
    save_data(data)

init_admin_data()

@app.route('/api/admin/prompt/list', methods=['GET'])
def list_prompts():
    return jsonify(load_data().get('prompts', []))

@app.route('/api/admin/prompt/save', methods=['POST'])
def save_prompt():
    try:
        req = request.json
        if not req or not req.get('name') or not req.get('template'):
            return jsonify({'success': False, 'error': 'Missing name or template'}), 400
        
        data = load_data()
        now = datetime.datetime.now().isoformat()
        new_name = req['name'].strip()
        
        # 检查名称重复
        current_id = req.get('id')
        for p in data['prompts']:
            if p['name'].strip() == new_name and p['id'] != current_id:
                return jsonify({'success': False, 'error': '模板名称已存在，请使用不同的名称'}), 400
        
        if req.get('id'):
            for p in data['prompts']:
                if p['id'] == req['id']:
                    p['name'] = new_name
                    p['template'] = req['template']
                    p['updated_at'] = now
                    break
        else:
            new_id = max([p['id'] for p in data['prompts']], default=0) + 1
            data['prompts'].append({
                "id": new_id, "name": new_name, "template": req['template'],
                "is_active": 0, "created_at": now, "updated_at": now
            })
        
        save_data(data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/admin/prompt/set_active', methods=['POST'])
def set_active_prompt():
    req = request.json
    data = load_data()
    for p in data['prompts']:
        p['is_active'] = 1 if p['id'] == req['id'] else 0
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/admin/prompt/delete', methods=['POST'])
def delete_prompt():
    """删除Prompt配置"""
    req = request.json
    prompt_id = req.get('id')
    if not prompt_id:
        return jsonify({'success': False, 'error': 'Missing id'}), 400
    
    data = load_data()
    original_count = len(data['prompts'])
    
    # Check if trying to delete the only active prompt
    prompt_to_delete = None
    for p in data['prompts']:
        if p['id'] == prompt_id:
            prompt_to_delete = p
            break
    
    if prompt_to_delete and prompt_to_delete.get('is_active') == 1:
        # Count other prompts
        other_prompts = [p for p in data['prompts'] if p['id'] != prompt_id]
        if len(other_prompts) == 0:
            return jsonify({'success': False, 'error': '不能删除唯一的Prompt配置'}), 400
        # Activate another prompt
        if other_prompts:
            other_prompts[0]['is_active'] = 1
    
    data['prompts'] = [p for p in data['prompts'] if p['id'] != prompt_id]
    
    if len(data['prompts']) == original_count:
        return jsonify({'success': False, 'error': 'Prompt not found'}), 404
    
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/admin/prompt/preview', methods=['POST'])
def preview_prompt():
    """预览Prompt模板替换变量后的效果"""
    req = request.json
    template = req.get('template', '')
    variables = req.get('variables', {})
    
    # 替换变量
    result = template
    for key, value in variables.items():
        result = result.replace('{' + key + '}', value)
    
    return jsonify({'preview': result})

@app.route('/api/admin/history/list', methods=['GET'])
def list_history():
    """获取服务器端历史记录（最多100条）"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    history = load_server_history()
    total = len(history)
    # 反转顺序，最新的在前
    history = list(reversed(history))
    return jsonify({'total': total, 'page': page, 'limit': limit, 'data': history[offset:offset+limit]})

@app.route('/api/admin/history/<int:id>', methods=['GET'])
def get_history(id):
    """获取单条历史记录详情"""
    history = load_server_history()
    for h in history:
        if h.get('id') == id:
            return jsonify(h)
    return jsonify({})

@app.route('/api/admin/history/delete', methods=['POST'])
def delete_history():
    """删除历史记录"""
    req = request.json
    history_id = req.get('id')
    if not history_id:
        return jsonify({'success': False, 'error': 'Missing id'}), 400
    
    history = load_server_history()
    original_count = len(history)
    history = [h for h in history if h.get('id') != history_id]
    
    if len(history) == original_count:
        return jsonify({'success': False, 'error': 'History not found'}), 404
    
    # Save back using load_data/save_data
    try:
        data = load_data()
        data['server_history'] = history
        save_data(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/models/list', methods=['GET'])
def list_models():
    """获取模型列表（隐藏API Key）"""
    data = load_data()
    models = data.get('models', [])
    # Hide API keys for security
    result = []
    for m in models:
        model_copy = dict(m)
        # 处理标准 API Key
        if model_copy.get('api_key'):
            key = model_copy['api_key']
            model_copy['api_key'] = '*' * 8 + key[-4:] if len(key) > 4 else '*' * len(key)
        # 处理千帆 Access Key
        if model_copy.get('access_key'):
            key = model_copy['access_key']
            model_copy['access_key'] = '*' * 8 + key[-4:] if len(key) > 4 else '*' * len(key)
        # 处理千帆 Secret Key
        if model_copy.get('secret_key'):
            key = model_copy['secret_key']
            model_copy['secret_key'] = '*' * 8 + key[-4:] if len(key) > 4 else '*' * len(key)
        result.append(model_copy)
    return jsonify(result)

@app.route('/api/admin/models/<int:id>', methods=['GET'])
def get_model(id):
    """获取单个模型详情（用于编辑，返回完整API Key）"""
    data = load_data()
    for m in data['models']:
        if m['id'] == id:
            return jsonify(m)
    return jsonify({'error': 'Model not found'}), 404

@app.route('/api/admin/models/save', methods=['POST'])
def save_model():
    try:
        req = request.json
        if not req or not req.get('name') or not req.get('provider'):
            return jsonify({'success': False, 'error': 'Missing name or provider'}), 400
        
        data = load_data()
        now = datetime.datetime.now().isoformat()
        new_name = req['name'].strip()
        provider = req.get('provider')
        
        # 检查名称重复
        current_id = req.get('id')
        for m in data['models']:
            if m['name'].strip() == new_name and m['id'] != current_id:
                return jsonify({'success': False, 'error': '模型名称已存在，请使用不同的名称'}), 400
        
        if req.get('id'):
            for m in data['models']:
                if m['id'] == req['id']:
                    m['name'] = new_name
                    m['provider'] = provider
                    m['endpoint'] = req.get('endpoint', '')
                    m['model_name'] = req.get('model_name', '')
                    
                    # 根据提供商处理不同的密钥字段
                    if provider == 'qianfan':
                        # 千帆：Access Key + Secret Key
                        new_access = req.get('access_key', '')
                        if new_access and not new_access.startswith('*'):
                            m['access_key'] = new_access
                        new_secret = req.get('secret_key', '')
                        if new_secret and not new_secret.startswith('*'):
                            m['secret_key'] = new_secret
                    else:
                        # 其他：单一 API Key
                        new_key = req.get('api_key', '')
                        if new_key and not new_key.startswith('*'):
                            m['api_key'] = new_key
                    
                    m['updated_at'] = now
                    break
        else:
            new_id = max([m['id'] for m in data['models']], default=0) + 1
            model_data = {
                "id": new_id,
                "name": new_name,
                "provider": provider,
                "endpoint": req.get('endpoint', ''),
                "model_name": req.get('model_name', ''),
                "is_active": 0,
                "created_at": now,
                "updated_at": now
            }
            
            # 根据提供商设置密钥
            if provider == 'qianfan':
                model_data['access_key'] = req.get('access_key', '')
                model_data['secret_key'] = req.get('secret_key', '')
            else:
                model_data['api_key'] = req.get('api_key', '')
            
            data['models'].append(model_data)
        
        save_data(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/models/set_active', methods=['POST'])
def set_active_model():
    req = request.json
    data = load_data()
    for m in data['models']:
        m['is_active'] = 1 if m['id'] == req['id'] else 0
    save_data(data)
    return jsonify({'success': True})

@app.route('/api/admin/models/delete', methods=['POST'])
def delete_model():
    req = request.json
    model_id = req.get('id')
    if not model_id:
        return jsonify({'success': False, 'error': 'Missing id'}), 400
    
    data = load_data()
    original_count = len(data['models'])
    
    # Find the model being deleted
    model_to_delete = None
    for m in data['models']:
        if m['id'] == model_id:
            model_to_delete = m
            break
    
    # Prevent deleting the last active model
    if model_to_delete and model_to_delete.get('is_active') == 1:
        other_models = [m for m in data['models'] if m['id'] != model_id]
        if len(other_models) == 0:
            return jsonify({'success': False, 'error': '不能删除唯一的活跃模型'}), 400
        # Activate another model
        if other_models:
            other_models[0]['is_active'] = 1
    
    data['models'] = [m for m in data['models'] if m['id'] != model_id]
    
    if len(data['models']) == original_count:
        return jsonify({'success': False, 'error': 'Model not found'}), 404
    
    save_data(data)
    return jsonify({'success': True})

# 获取活跃的Prompt模板
def get_active_prompt_template():
    data = load_data()
    for p in data.get('prompts', []):
        if p.get('is_active') == 1:
            return p.get('template')
    return None

# Vercel 无服务器函数入口 - 直接导出 Flask app
# Vercel Python 运行时自动处理 WSGI 应用

# 本地开发入口
if __name__ == "__main__":
    app.run(debug=True)
