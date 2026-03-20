# -*- coding: utf-8 -*-
"""
腾讯云函数 - 简单测试
"""

def main_handler(event, context):
    """云函数入口"""
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': '{"message": "Hello from SCF!"}'
    }

if __name__ == '__main__':
    print(main_handler({}, None))
