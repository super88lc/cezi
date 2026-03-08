#!/usr/bin/env python3
"""
微信支付服务
"""

import hashlib
import time
import random
import string
import requests
import json
import os
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

# 微信支付配置
WECHAT_MCH_ID = os.environ.get("WECHAT_MCH_ID", "")       # 商户号
WECHAT_API_KEY = os.environ.get("WECHAT_API_KEY", "")       # API密钥
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")        # 小程序AppID
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "") # 小程序AppSecret

# Redis连接（用于订单缓存）
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

def generate_nonce():
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

def generate_sign(params, api_key):
    """生成签名"""
    # 按key排序
    sorted_params = sorted(params.items())
    # 拼接成字符串
    sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
    sign_str += f"&key={api_key}"
    # MD5加密
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

def get_wechat_access_token():
    """获取微信access_token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": WECHAT_APP_ID,
        "secret": WECHAT_APP_SECRET
    }
    response = requests.get(url, params=params)
    return response.json().get("access_token")

def create_order(out_trade_no, total_fee, description, openid):
    """创建微信支付订单"""
    if not all([WECHAT_MCH_ID, WECHAT_API_KEY, WECHAT_APP_ID]):
        return {"error": "微信支付未配置"}
    
    # 获取access_token
    access_token = get_wechat_access_token()
    if not access_token:
        return {"error": "获取access_token失败"}
    
    # 统一下单API
    url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
    
    nonce = generate_nonce()
    
    params = {
        "appid": WECHAT_APP_ID,
        "mchid": WECHAT_MCH_ID,
        "description": description,
        "out_trade_no": out_trade_no,
        "notify_url": os.environ.get("WECHAT_NOTIFY_URL", ""),
        "amount": {
            "total": total_fee,  # 单位：分
            "currency": "CNY"
        },
        "payer": {
            "openid": openid
        }
    }
    
    # 生成签名
    sign = generate_sign(params, WECHAT_API_KEY)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"WECHAT3-SHA256-RSA2048签名"
    }
    
    # TODO: 实际调用需要配置证书和签名
    # 这里返回预支付参数
    
    return {
        "success": True,
        "prepay_id": "prepay_id_placeholder",
        "order_id": out_trade_no
    }

def query_order(out_trade_no):
    """查询订单状态"""
    url = f"https://api.mch.weixin.qq.com/v3/pay/transactions/out_trade_no/{out_trade_no}"
    # TODO: 实现订单查询
    return {"status": "PAID"}

def close_order(out_trade_no):
    """关闭订单"""
    # TODO: 实现关闭订单
    return {"success": True}

# 会员套餐
MEMBERSHIP_PLANS = {
    "monthly": {
        "name": "月卡会员",
        "price": 3000,  # 30元 = 3000分
        "days": 30,
        "features": ["无限测字", "深度分析", "诸葛神签", "历史记录"]
    },
    "quarterly": {
        "name": "季卡会员", 
        "price": 8000,  # 80元
        "days": 90,
        "features": ["无限测字", "深度分析", "诸葛神签", "历史记录", "优先客服"]
    },
    "yearly": {
        "name": "年卡会员",
        "price": 29800,  # 298元
        "days": 365,
        "features": ["无限测字", "深度分析", "诸葛神签", "历史记录", "优先客服", "专属祝福"]
    }
}

@app.route("/api/payment/create", methods=["POST"])
def create_payment():
    """创建支付订单"""
    data = request.json
    plan = data.get("plan", "monthly")  # monthly, quarterly, yearly
    openid = data.get("openid", "")
    
    if not openid:
        return jsonify({"error": "需要用户openid"}), 400
    
    if plan not in MEMBERSHIP_PLANS:
        return jsonify({"error": "无效的套餐"}), 400
    
    plan_info = MEMBERSHIP_PLANS[plan]
    
    # 生成订单号
    out_trade_no = f"CEZI{int(time.time())}{random.randint(1000,9999)}"
    
    # 创建订单
    result = create_order(
        out_trade_no=out_trade_no,
        total_fee=plan_info["price"],
        description=plan_info["name"],
        openid=openid
    )
    
    if "error" in result:
        return jsonify(result), 500
    
    return jsonify({
        "success": True,
        "order_id": out_trade_no,
        "plan": plan,
        "price": plan_info["price"] / 100,
        "name": plan_info["name"]
    })

@app.route("/api/payment/notify", methods=["POST"])
def payment_notify():
    """支付回调"""
    # TODO: 验证签名，处理回调
    data = request.json
    return jsonify({"code": "SUCCESS", "message": "成功"})

@app.route("/api/payment/query/<order_id>", methods=["GET"])
def query_payment(order_id):
    """查询订单"""
    result = query_order(order_id)
    return jsonify(result)

@app.route("/api/payment/plans", methods=["GET"])
def get_plans():
    """获取会员套餐"""
    plans = []
    for key, val in MEMBERSHIP_PLANS.items():
        plans.append({
            "id": key,
            "name": val["name"],
            "price": val["price"] / 100,
            "days": val["days"],
            "features": val["features"]
        })
    return jsonify({"success": True, "plans": plans})

@app.route("/api/payment/config", methods=["GET"])
def payment_config():
    """获取支付配置状态"""
    return jsonify({
        "configured": bool(WECHAT_MCH_ID and WECHAT_API_KEY and WECHAT_APP_ID),
        "mch_id": WECHAT_MCH_ID[:4] + "****" if WECHAT_MCH_ID else None
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
