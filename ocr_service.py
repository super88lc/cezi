#!/usr/bin/env python3
"""
OCR 识别服务 - 百度云
"""

import base64
import json
import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# 百度云 OCR 配置
BAIDU_API_KEY = os.environ.get("BAIDU_API_KEY", "")
BAIDU_SECRET_KEY = os.environ.get("BAIDU_SECRET_KEY", "")

def get_baidu_token():
    """获取百度API访问令牌"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_API_KEY,
        "client_secret": BAIDU_SECRET_KEY
    }
    response = requests.post(url, params=params)
    return response.json().get("access_token")

def baidu_ocr(image_base64):
    """百度文字识别"""
    if not BAIDU_API_KEY or not BAIDU_SECRET_KEY:
        return {"error": "百度API未配置", "char": None}
    
    try:
        token = get_baidu_token()
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token={token}"
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"image": image_base64}
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        if "words_result" in result and result["words_result"]:
            # 提取第一个识别的文字
            words = result["words_result"]
            if words:
                first_word = words[0].get("words", "")[0] if words[0].get("words") else None
                return {
                    "success": True,
                    "char": first_word,
                    "all_words": [w.get("words", "") for w in words],
                    "confidence": words[0].get("probability", {}).get("average", 0)
                }
        
        return {"error": "未识别到文字", "char": None}
        
    except Exception as e:
        return {"error": str(e), "char": None}

def ali_ocr(image_base64):
    """阿里云手写识别（预留）"""
    # 阿里云配置
    ali_access_key = os.environ.get("ALI_ACCESS_KEY", "")
    ali_secret = os.environ.get("ALI_SECRET_KEY", "")
    
    if not ali_access_key:
        return {"error": "阿里云API未配置", "char": None}
    
    # TODO: 实现阿里云手写识别
    # 参考: https://help.aliyun.com/document_detail/151897.html
    return {"error": "阿里云OCR开发中", "char": None}

@app.route("/api/ocr", methods=["POST"])
def recognize():
    """OCR识别接口"""
    data = request.json
    image_base64 = data.get("image", "")
    provider = data.get("provider", "baidu")  # baidu, ali
    
    if not image_base64:
        return jsonify({"error": "请上传图片"}), 400
    
    # 去除 data:image 前缀
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    if provider == "baidu":
        result = baidu_ocr(image_base64)
    elif provider == "ali":
        result = ali_ocr(image_base64)
    else:
        result = {"error": "不支持的OCR提供商"}
    
    if result.get("char"):
        return jsonify({"success": True, **result})
    else:
        return jsonify({"success": False, **result}), 400

@app.route("/api/ocr/config", methods=["GET"])
def ocr_config():
    """获取OCR配置状态"""
    return jsonify({
        "baidu_configured": bool(BAIDU_API_KEY and BAIDU_SECRET_KEY),
        "ali_configured": bool(os.environ.get("ALI_ACCESS_KEY")),
        "providers": ["baidu"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
