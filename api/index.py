"""
Vercel Python Handler - Minimal Version
"""
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/cezi', methods=['POST'])
def cezi():
    data = request.get_json() or {}
    char = data.get('char', '')
    question = data.get('question', '综合运势')
    
    # Simple response for testing
    return jsonify({
        "data": {
            "char": char,
            "question": question,
            "result": {
                "conclusion": f"测字「{char}」结果：{question}"
            }
        }
    })

def handler(request, response):
    """Vercel serverless function handler"""
    with app.test_client() as client:
        path = request.path or '/api/cezi'
        method = request.method or 'POST'
        body = request.body or b'{}'
        
        import json
        try:
            json_data = json.loads(body)
        except:
            json_data = {}
        
        if method == 'POST':
            resp = client.post(path, json=json_data)
        else:
            resp = client.get(path)
        
        response.status_code = resp.status_code
        for key, value in resp.headers:
            if key.lower() not in ['content-encoding', 'transfer-encoding']:
                response.header(key, value)
        
        return resp.get_data(as_text=True)
