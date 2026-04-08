"""
测字算事 - PC后台管理系统
"""
import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'admin.db')

# 确保数据目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Prompt配置表
    c.execute('''CREATE TABLE IF NOT EXISTS prompt_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        template TEXT NOT NULL,
        is_active INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT
    )''')
    
    # 历史记录表
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        char TEXT,
        question TEXT,
        direction TEXT,
        time_info TEXT,
        prompt TEXT,
        llm_response TEXT,
        display_result TEXT,
        model_used TEXT,
        created_at TEXT
    )''')
    
    # 模型配置表
    c.execute('''CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        provider TEXT,
        api_key TEXT,
        endpoint TEXT,
        model_name TEXT,
        is_active INTEGER DEFAULT 0,
        created_at TEXT
    )''')
    
    # 插入默认配置
    c.execute('SELECT count(*) FROM prompt_configs')
    if c.fetchone()[0] == 0:
        default_template = """你是一位精通易经的测字先生，为人测字解惑。

测字信息：
- 所测之字：{char}
- 所问之事：{question}
- 测字方位：{direction}
- 测字时辰：{time}

请根据以上信息，以古代算命先生的语气对此字进行解析。要求：
1. 先解释字形结构与含义
2. 结合五行笔画分析
3. 结合梅花易数解读方位与时辰
4. 给出针对所问之事的具体建议
5. 语气要像一位经验丰富的老师傅，不要像AI"""
        
        c.execute('''INSERT INTO prompt_configs (name, template, is_active, created_at, updated_at) 
                      VALUES (?, ?, 1, ?, ?)''', 
                   ('默认模板', default_template, datetime.now().isoformat(), datetime.now().isoformat()))
    
    # 插入默认模型
    c.execute('SELECT count(*) FROM models')
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO models (name, provider, api_key, endpoint, model_name, is_active, created_at)
                      VALUES (?, ?, ?, ?, ?, 1, ?)''', 
                   ('MiniMax', 'minimax', '', 'https://api.minimaxi.com/anthropic/v1', 'MiniMax-M2.5', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

init_db()

# ========== Prompt配置 API ==========

@app.route('/api/admin/prompt/list', methods=['GET'])
def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM prompt_configs ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/admin/prompt/save', methods=['POST'])
def save_prompt():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    if data.get('id'):
        c.execute('''UPDATE prompt_configs SET name=?, template=?, updated_at=? WHERE id=?''',
                  (data['name'], data['template'], now, data['id']))
    else:
        c.execute('''INSERT INTO prompt_configs (name, template, is_active, created_at, updated_at)
                      VALUES (?, ?, 0, ?, ?)''',
                  (data['name'], data['template'], now, now))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/prompt/set_active', methods=['POST'])
def set_active_prompt():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE prompt_configs SET is_active = 0')
    c.execute('UPDATE prompt_configs SET is_active = 1 WHERE id = ?', (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/prompt/preview', methods=['POST'])
def preview_prompt():
    data = request.json
    template = data.get('template', '')
    variables = data.get('variables', {})
    
    # 替换变量
    preview = template
    for key, value in variables.items():
        preview = preview.replace(f'{{{key}}}', value)
    
    return jsonify({'preview': preview})

# ========== 历史记录 API ==========

@app.route('/api/admin/history/list', methods=['GET'])
def list_history():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM history')
    total = c.fetchone()[0]
    
    c.execute('SELECT * FROM history ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))
    rows = c.fetchall()
    conn.close()
    
    return jsonify({
        'total': total,
        'page': page,
        'limit': limit,
        'data': [dict(row) for row in rows]
    })

@app.route('/api/admin/history/<int:id>', methods=['GET'])
def get_history(id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM history WHERE id = ?', (id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Not found'}), 404

# ========== 模型管理 API ==========

@app.route('/api/admin/models/list', methods=['GET'])
def list_models():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM models ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/admin/models/save', methods=['POST'])
def save_model():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    if data.get('id'):
        c.execute('''UPDATE models SET name=?, provider=?, api_key=?, endpoint=?, model_name=? WHERE id=?''',
                  (data['name'], data['provider'], data.get('api_key',''), 
                   data.get('endpoint',''), data.get('model_name',''), data['id']))
    else:
        c.execute('''INSERT INTO models (name, provider, api_key, endpoint, model_name, is_active, created_at)
                      VALUES (?, ?, ?, ?, ?, 0, ?)''',
                  (data['name'], data['provider'], data.get('api_key',''),
                   data.get('endpoint',''), data.get('model_name',''), now))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/models/set_active', methods=['POST'])
def set_active_model():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE models SET is_active = 0')
    c.execute('UPDATE models SET is_active = 1 WHERE id = ?', (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/models/delete', methods=['POST'])
def delete_model():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM models WHERE id = ?', (data['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== 页面路由 ==========

@app.route('/admin')
def admin_page():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测字算事 - 管理后台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; }
        .container { display: flex; min-height: 100vh; }
        
        /* 侧边栏 */
        .sidebar { width: 220px; background: #1a1a2e; padding: 20px; border-right: 1px solid #2a2a4e; }
        .logo { font-size: 20px; font-weight: bold; color: #d4a574; margin-bottom: 30px; padding: 10px; }
        .nav-item { padding: 12px 16px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; transition: all 0.2s; color: #888; }
        .nav-item:hover { background: #2a2a4e; color: #d4a574; }
        .nav-item.active { background: #d4a574; color: #1a1a2e; font-weight: bold; }
        
        /* 主内容 */
        .main { flex: 1; padding: 30px; overflow-y: auto; }
        .page { display: none; }
        .page.active { display: block; }
        .page-title { font-size: 24px; margin-bottom: 20px; color: #d4a574; }
        
        /* 卡片 */
        .card { background: #1a1a2e; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #2a2a4e; }
        .card-title { font-size: 16px; margin-bottom: 15px; color: #d4a574; }
        
        /* 表单 */
        .form-group { margin-bottom: 15px; }
        .form-label { display: block; margin-bottom: 6px; color: #888; font-size: 14px; }
        .form-input, .form-select, .form-textarea { width: 100%; padding: 10px; background: #0f0f1a; border: 1px solid #2a2a4e; border-radius: 6px; color: #e0e0e0; font-size: 14px; }
        .form-textarea { min-height: 200px; font-family: monospace; }
        .form-input:focus, .form-textarea:focus { outline: none; border-color: #d4a574; }
        
        /* 按钮 */
        .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .btn-primary { background: #d4a574; color: #1a1a2e; }
        .btn-primary:hover { background: #e5b785; }
        .btn-secondary { background: #2a2a4e; color: #e0e0e0; }
        .btn-danger { background: #ff4757; color: white; }
        
        /* 表格 */
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #2a2a4e; }
        .table th { color: #d4a574; font-weight: bold; }
        .table tr:hover { background: #2a2a4e; }
        
        /* 徽章 */
        .badge { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .badge-active { background: #2ed573; color: #1a1a2e; }
        .badge-inactive { background: #57606f; color: white; }
        
        /* 变量提示 */
        .var-tip { background: #2a2a4e; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 13px; color: #888; }
        .var-tip code { color: #d4a574; background: #0f0f1a; padding: 2px 6px; border-radius: 4px; }
        
        /* 预览 */
        .preview-box { background: #0f0f1a; padding: 15px; border-radius: 6px; border: 1px solid #2a2a4e; white-space: pre-wrap; font-size: 13px; line-height: 1.6; max-height: 300px; overflow-y: auto; }
        
        /* 分页 */
        .pagination { display: flex; gap: 10px; margin-top: 20px; }
        .pagination button { padding: 8px 14px; }
        
        /* 历史详情 */
        .history-detail { background: #0f0f1a; padding: 15px; border-radius: 8px; margin-top: 10px; }
        .history-section { margin-bottom: 15px; }
        .history-label { color: #d4a574; font-size: 12px; margin-bottom: 5px; }
        .history-content { font-size: 13px; line-height: 1.6; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <div class="sidebar">
            <div class="logo">🔮 测字管理后台</div>
            <div class="nav-item active" data-page="prompt" onclick="showPage('prompt')">📝 Prompt配置</div>
            <div class="nav-item" data-page="history" onclick="showPage('history')">📜 历史记录</div>
            <div class="nav-item" data-page="models" onclick="showPage('models')">🤖 模型管理</div>
        </div>
        
        <div class="main">
            <!-- Prompt配置页面 -->
            <div class="page active" id="page-prompt">
                <div class="page-title">📝 Prompt配置</div>
                
                <div class="card">
                    <div class="card-title">编辑Prompt模板</div>
                    <div class="var-tip">
                        可用变量: <code>{char}</code> <code>{question}</code> <code>{direction}</code> <code>{time}</code>
                    </div>
                    <div class="form-group">
                        <label class="form-label">配置名称</label>
                        <input type="text" class="form-input" id="promptName" placeholder="例如：默认模板">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Prompt模板内容</label>
                        <textarea class="form-textarea" id="promptTemplate" placeholder="输入Prompt模板..."></textarea>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-primary" onclick="savePrompt()">保存配置</button>
                        <button class="btn btn-secondary" onclick="previewPrompt()">预览</button>
                        <button class="btn btn-secondary" onclick="loadActivePrompt()">加载当前</button>
                    </div>
                </div>
                
                <div class="card" id="previewCard" style="display:none;">
                    <div class="card-title">预览效果</div>
                    <div class="preview-box" id="previewContent"></div>
                </div>
                
                <div class="card">
                    <div class="card-title">已有配置</div>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>名称</th>
                                <th>状态</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="promptList"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 历史记录页面 -->
            <div class="page" id="page-history">
                <div class="page-title">📜 测字历史记录</div>
                <div class="card">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>字</th>
                                <th>问题</th>
                                <th>方位</th>
                                <th>时间</th>
                                <th>模型</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="historyList"></tbody>
                    </table>
                    <div class="pagination" id="historyPagination"></div>
                </div>
            </div>
            
            <!-- 模型管理页面 -->
            <div class="page" id="page-models">
                <div class="page-title">🤖 模型管理</div>
                
                <div class="card">
                    <div class="card-title">添加/编辑模型</div>
                    <div class="form-group">
                        <label class="form-label">模型名称</label>
                        <input type="text" class="form-input" id="modelName" placeholder="例如：MiniMax">
                    </div>
                    <div class="form-group">
                        <label class="form-label">提供商</label>
                        <select class="form-select" id="modelProvider">
                            <option value="minimax">MiniMax</option>
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="custom">自定义</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">API端点</label>
                        <input type="text" class="form-input" id="modelEndpoint" placeholder="例如：https://api.minimaxi.com/anthropic/v1">
                    </div>
                    <div class="form-group">
                        <label class="form-label">模型名称</label>
                        <input type="text" class="form-input" id="modelName2" placeholder="例如：MiniMax-M2.5">
                    </div>
                    <div class="form-group">
                        <label class="form-label">API Key</label>
                        <input type="password" class="form-input" id="modelApiKey" placeholder="API密钥">
                    </div>
                    <button class="btn btn-primary" onclick="saveModel()">保存模型</button>
                </div>
                
                <div class="card">
                    <div class="card-title">已有模型</div>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>名称</th>
                                <th>提供商</th>
                                <th>模型</th>
                                <th>状态</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="modelList"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    let currentPage = 1;
    
    function showPage(page) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.getElementById('page-' + page).classList.add('active');
        document.querySelector('[data-page="' + page + '"]').classList.add('active');
        
        if (page === 'prompt') loadPrompts();
        if (page === 'history') loadHistory();
        if (page === 'models') loadModels();
    }
    
    // Prompt管理
    async function loadPrompts() {
        const res = await fetch('/api/admin/prompt/list');
        const data = await res.json();
        let html = '';
        data.forEach(p => {
            html += `<tr>
                <td>${p.id}</td>
                <td>${p.name}</td>
                <td><span class="badge ${p.is_active ? 'badge-active' : 'badge-inactive'}">${p.is_active ? '应用中' : '未启用'}</span></td>
                <td>
                    ${p.is_active ? '' : '<button class="btn btn-primary" style="padding:4px 10px;font-size:12px;" onclick="activatePrompt(' + p.id + ')">启用</button>'}
                    <button class="btn btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="editPrompt(${p.id}, '${p.name}', '${p.template.replace(/'/g, "\\'")}')">编辑</button>
                </td>
            </tr>`;
        });
        document.getElementById('promptList').innerHTML = html;
    }
    
    async function loadActivePrompt() {
        const res = await fetch('/api/admin/prompt/list');
        const data = await res.json();
        const active = data.find(p => p.is_active);
        if (active) {
            document.getElementById('promptName').value = active.name;
            document.getElementById('promptTemplate').value = active.template;
        }
    }
    
    async function savePrompt() {
        const name = document.getElementById('promptName').value;
        const template = document.getElementById('promptTemplate').value;
        const id = document.getElementById('promptName').dataset.id;
        
        await fetch('/api/admin/prompt/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id: id ? parseInt(id) : null, name, template})
        });
        
        document.getElementById('promptName').value = '';
        document.getElementById('promptName').dataset.id = '';
        document.getElementById('promptTemplate').value = '';
        loadPrompts();
    }
    
    function editPrompt(id, name, template) {
        document.getElementById('promptName').value = name;
        document.getElementById('promptName').dataset.id = id;
        document.getElementById('promptTemplate').value = template;
    }
    
    async function activatePrompt(id) {
        await fetch('/api/admin/prompt/set_active', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id})
        });
        loadPrompts();
    }
    
    async function previewPrompt() {
        const template = document.getElementById('promptTemplate').value;
        const variables = {
            char: '测',
            question: '事业发展',
            direction: '南',
            time: '辰时'
        };
        
        const res = await fetch('/api/admin/prompt/preview', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({template, variables})
        });
        const data = await res.json();
        document.getElementById('previewCard').style.display = 'block';
        document.getElementById('previewContent').textContent = data.preview;
    }
    
    // 历史记录
    async function loadHistory(page = 1) {
        currentPage = page;
        const res = await fetch('/api/admin/history/list?page=' + page + '&limit=20');
        const data = await res.json();
        
        let html = '';
        data.data.forEach(h => {
            html += `<tr>
                <td>${h.id}</td>
                <td>${h.char || '-'}</td>
                <td>${h.question || '-'}</td>
                <td>${h.direction || '-'}</td>
                <td>${h.time_info || '-'}</td>
                <td>${h.model_used || '-'}</td>
                <td><button class="btn btn-secondary" style="padding:4px 10px;font-size:12px;" onclick="viewHistory(${h.id})">查看</button></td>
            </tr>`;
        });
        document.getElementById('historyList').innerHTML = html;
        
        // 分页
        let paging = '';
        for (let i = 1; i <= Math.ceil(data.total / data.limit); i++) {
            paging += '<button class="btn ' + (i === page ? 'btn-primary' : 'btn-secondary') + '" onclick="loadHistory(' + i + ')">' + i + '</button>';
        }
        document.getElementById('historyPagination').innerHTML = paging;
    }
    
    async function viewHistory(id) {
        const res = await fetch('/api/admin/history/' + id);
        const h = await res.json();
        
        const content = `
<div class="history-detail">
    <div class="history-section">
        <div class="history-label">用户输入</div>
        <div class="history-content">字: ${h.char || '-'} | 问题: ${h.question || '-'} | 方位: ${h.direction || '-'} | 时辰: ${h.time_info || '-'}</div>
    </div>
    <div class="history-section">
        <div class="history-label">发送给LLM的Prompt</div>
        <div class="history-content">${h.prompt || '-'}</div>
    </div>
    <div class="history-section">
        <div class="history-label">LLM原始返回</div>
        <div class="history-content">${h.llm_response || '-'}</div>
    </div>
    <div class="history-section">
        <div class="history-label">前端展示结果</div>
        <div class="history-content">${h.display_result || '-'}</div>
    </div>
</div>`;
        
        // 显示在弹窗或新页面
        const win = window.open('', '_blank', 'width=800,height=600');
        win.document.write('<html><head><title>测字记录详情</title></head><body style="background:#0f0f1a;color:#e0e0e0;padding:20px;">' + content + '</body></html>');
    }
    
    // 模型管理
    async function loadModels() {
        const res = await fetch('/api/admin/models/list');
        const data = await res.json();
        let html = '';
        data.forEach(m => {
            html += `<tr>
                <td>${m.id}</td>
                <td>${m.name}</td>
                <td>${m.provider}</td>
                <td>${m.model_name || '-'}</td>
                <td><span class="badge ${m.is_active ? 'badge-active' : 'badge-inactive'}">${m.is_active ? '应用中' : '未启用'}</span></td>
                <td>
                    ${m.is_active ? '' : '<button class="btn btn-primary" style="padding:4px 10px;font-size:12px;" onclick="activateModel(' + m.id + ')">启用</button>'}
                    <button class="btn btn-danger" style="padding:4px 10px;font-size:12px;" onclick="deleteModel(' + m.id + ')">删除</button>
                </td>
            </tr>`;
        });
        document.getElementById('modelList').innerHTML = html;
    }
    
    async function saveModel() {
        const name = document.getElementById('modelName').value;
        const provider = document.getElementById('modelProvider').value;
        const endpoint = document.getElementById('modelEndpoint').value;
        const model_name = document.getElementById('modelName2').value;
        const api_key = document.getElementById('modelApiKey').value;
        
        await fetch('/api/admin/models/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, provider, endpoint, model_name, api_key})
        });
        
        document.getElementById('modelName').value = '';
        document.getElementById('modelEndpoint').value = '';
        document.getElementById('modelName2').value = '';
        document.getElementById('modelApiKey').value = '';
        loadModels();
    }
    
    async function activateModel(id) {
        await fetch('/api/admin/models/set_active', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id})
        });
        loadModels();
    }
    
    async function deleteModel(id) {
        if (confirm('确定删除?')) {
            await fetch('/api/admin/models/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id})
            });
            loadModels();
        }
    }
    
    // 初始化
    loadPrompts();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)
