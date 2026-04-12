#!/usr/bin/env python3
"""
测字API诊断测试
测试API响应格式和常见问题
"""

import json
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_cezi_api():
    """测试测字API"""
    print("=" * 50)
    print("🔮 测字API诊断测试")
    print("=" * 50)
    
    # 1. 检查必要文件
    print("\n1️⃣ 检查必要文件...")
    files_to_check = [
        'api/index.py',
        'api/cezi.py',
        'cezi_core_v3.py',
        'qianfan_client.py',
        'templates/index.html',
        'vercel.json'
    ]
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    missing_files = []
    for f in files_to_check:
        full_path = os.path.join(base_dir, f)
        if os.path.exists(full_path):
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f} - 缺失!")
            missing_files.append(f)
    
    if missing_files:
        print(f"\n⚠️  缺失 {len(missing_files)} 个文件，需要修复")
    
    # 2. 检查环境变量
    print("\n2️⃣ 检查环境变量...")
    env_vars = ['MINIMAX_API_KEY', 'QIANFAN_ACCESS_KEY', 'QIANFAN_SECRET_KEY', 'KV_URL']
    for var in env_vars:
        value = os.getenv(var, '')
        if value:
            print(f"  ✅ {var}: 已设置 ({len(value)}字符)")
        else:
            print(f"  ⚠️  {var}: 未设置")
    
    # 3. 测试核心模块导入
    print("\n3️⃣ 测试模块导入...")
    try:
        from cezi_core_v3 import generate_enhanced_result
        print("  ✅ cezi_core_v3 导入成功")
        
        # 测试生成结果
        print("\n4️⃣ 测试测字算法...")
        result = generate_enhanced_result("福", "事业如何？", "南")
        print(f"  ✅ 算法执行成功")
        print(f"     - 字符: {result.get('char')}")
        print(f"     - 分析: {result.get('analysis', {})}")
        print(f"     - 梅花: {result.get('meihua', {})}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 检查API响应格式
    print("\n5️⃣ 检查API响应格式...")
    expected_format = {
        "success": True,
        "data": {
            "char": "测",
            "analysis": {},
            "meihua": {}
        },
        "verbose": "..."
    }
    print(f"  预期格式: {json.dumps(expected_format, ensure_ascii=False, indent=2)[:200]}...")
    
    # 6. 检查前端API_BASE
    print("\n6️⃣ 检查前端API配置...")
    html_path = os.path.join(base_dir, 'templates', 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'API_BASE' in content:
                # 提取API_BASE定义
                import re
                match = re.search(r'const\s+API_BASE\s*=\s*"([^"]+)"', content)
                if match:
                    api_base = match.group(1)
                    print(f"  📍 API_BASE: {api_base}")
                    if 'localhost' in api_base or '127.0.0.1' in api_base:
                        print(f"  ⚠️  当前是本地开发环境")
                    elif 'vercel.app' in api_base:
                        print(f"  ✅ 已配置Vercel生产环境")
                else:
                    print(f"  ❌ 无法解析API_BASE")
            else:
                print(f"  ❌ 未找到API_BASE定义")
    
    print("\n" + "=" * 50)
    print("诊断完成")
    print("=" * 50)

if __name__ == "__main__":
    test_cezi_api()
