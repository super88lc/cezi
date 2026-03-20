"""
Vercel Python Handler
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

# This is the Vercel Python handler format
def handler(event, context):
    """Handle Vercel serverless function"""
    # Parse the incoming request
    from werkzeug.wrappers import Request, Response
    
    # Convert event to WSGI environ
    environ = {
        'REQUEST_METHOD': event.get('method', 'POST'),
        'SCRIPT_NAME': '',
        'PATH_INFO': event.get('path', '/api/cezi'),
        'QUERY_STRING': event.get('queryString', ''),
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'HTTP_HOST': event.get('headers', {}).get('host', 'zi-cesuan.vercel.app'),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': event.get('body', b''),
        'wsgi.errors': __import__('sys').stderr,
    }
    
    # Create request and response objects
    req = Request(environ)
    resp = app(req.environ, lambda s, h: Response(s, headers=h))
    
    # Return the response in Vercel format
    return {
        'statusCode': resp.status_code,
        'headers': dict(resp.headers),
        'body': resp.get_data(as_text=True)
    }
