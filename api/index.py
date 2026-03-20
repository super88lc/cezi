# Vercel Python Handler
import json
from flask import Flask, request, jsonify
from cezi import app

# Export the handler for Vercel
def handler(request, response):
    """Handle requests for Vercel"""
    with app.test_client() as client:
        # Get request data
        path = request.path
        method = request.method
        headers = dict(request.headers)
        
        # Get body
        body = request.body
        if body:
            try:
                json_data = json.loads(body)
            except:
                json_data = {}
        else:
            json_data = {}
        
        # Make request to Flask
        if method == 'POST':
            resp = client.post(path, json=json_data, headers=headers)
        else:
            resp = client.get(path, headers=headers)
        
        # Set response
        response.status_code = resp.status_code
        for key, value in resp.headers:
            if key.lower() != 'content-encoding':  # Skip encoding headers
                response.header(key, value)
        
        return resp.get_data(as_text=True)
