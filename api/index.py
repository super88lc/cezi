"""
Vercel Python Handler - Simplified
"""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/api/cezi', methods=['POST'])
def cezi():
    data = request.get_json() or {}
    char = data.get('char', '')
    question = data.get('question', '综合运势')
    
    return jsonify({
        "data": {
            "char": char,
            "question": question,
            "result": {
                "conclusion": f"测字「{char}」结果：{question}"
            }
        }
    })

@app.route('/')
def index():
    return jsonify({
        "service": "zi-cesuan",
        "version": "1.0.0",
        "status": "ok"
    })

@app.route('/api/status')
def status():
    return jsonify({
        "version": "1.0.0",
        "features": {
            "cezi": True
        }
    })
