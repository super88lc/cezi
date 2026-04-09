#!/usr/bin/env python3
"""
测字算事小程序 - Vercel 入口（简化版）
"""

import os
import sys
import json
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": time.time()})

@app.route("/api/test", methods=["GET"])
def test():
    return jsonify({"message": "API is working", "path": sys.path})

# 导入主应用
try:
    from cezi_core_v3 import generate_enhanced_result
    CORE_AVAILABLE = True
except Exception as e:
    CORE_AVAILABLE = False
    CORE_ERROR = str(e)

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({
        "core_available": CORE_AVAILABLE,
        "core_error": CORE_ERROR if not CORE_AVAILABLE else None,
        "python_version": sys.version,
        "cwd": os.getcwd()
    })

@app.route("/api/cezi", methods=["POST"])
def cezi():
    if not CORE_AVAILABLE:
        return jsonify({"error": "Core module not available", "details": CORE_ERROR}), 500
    
    data = request.json
    char = data.get("char", "").strip()
    question = data.get("question", "")
    
    if not char:
        return jsonify({"error": "请输入要测的字"}), 400
    
    try:
        result = generate_enhanced_result(char, question, data.get("direction", "南"))
        return jsonify({"success": True, "data": result})
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# Vercel 入口
if __name__ == "__main__":
    app.run(debug=True)
