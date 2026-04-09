#!/usr/bin/env python3
"""
Admin后台路由
提供管理后台API支持
"""

from flask import Blueprint, request, jsonify
import sqlite3
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'admin.db')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@admin_bp.route('/')
def admin_index():
    """管理后台首页"""
    return jsonify({"message": "Admin API", "status": "ok"})

@admin_bp.route('/stats', methods=['GET'])
def admin_stats():
    """获取统计数据"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # 测字次数统计
        c.execute('SELECT COUNT(*) FROM history')
        total_cezi = c.fetchone()[0]
        
        # 今日测字次数
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('SELECT COUNT(*) FROM history WHERE DATE(created_at) = ?', (today,))
        today_cezi = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "total_cezi": total_cezi,
                "today_cezi": today_cezi
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
