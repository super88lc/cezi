"""
Vercel Python Handler for 测字算事
"""

from flask import Flask, request, jsonify
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from cezi
# We need to import the cezi module and get the app
import importlib.util

# Load cezi.py as a module
spec = importlib.util.spec_from_file_location("cezi", "api/cezi.py")
cezi_module = importlib.util.module_from_spec(spec)

# We need to execute the module to get the app
exec(open("api/cezi.py").read(), globals())

# Get the app
app = globals().get('app')

# Vercel handler
def handler(request, response):
    """Vercel serverless function handler"""
    # Use Flask's test client
    with app.test_client() as client:
        # Get request data
        path = request.path or '/api/cezi'
        method = request.method or 'POST'
        
        # Get body
        body = request.body or b'{}'
        import json
        try:
            json_data = json.loads(body)
        except:
            json_data = {}
        
        # Make request to Flask
        if method == 'POST':
            resp = client.post(path, json=json_data)
        else:
            resp = client.get(path)
        
        # Set response
        response.status_code = resp.status_code
        for key, value in resp.headers:
            response.header(key, value)
        
        return resp.get_data(as_text=True)
