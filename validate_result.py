#!/usr/bin/env python3
"""
测字结果验证脚本 - 自动检查前端渲染是否符合标准
"""
import re
import json

def validate_cezi_result():
    """验证测字结果的前端渲染是否符合要求"""
    
    # 模拟从API获取的数据
    sample_deep_analysis = """# 测字「测」字深度分析

---

## 一、字形解字

**「测」字，左为「氵」，右为「则」**。氵者，水也，流动变化，智慧之源也；则者，法度准则，边界分明之象也。

## 二、五行分析

**九画属水，水数至九，阳极生阴之象**。水主智，主变，亦主险。

## 三、事业发展详解

**事业发展，当以"测"字为镜**。南方火旺之地，宜避其锐气，待时而动。

具体建议：
- 方位趋吉：南方属火
- 时辰注意：申时
"""
    
    print("=" * 60)
    print("🔍 测字结果验证")
    print("=" * 60)
    
    # 模拟前端处理逻辑
    content = sample_deep_analysis
    
    # 移除所有标题格式
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[一二三四五六七八九十]+[、.]', '', content)
    content = re.sub(r'^\d+[、.]\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    content = re.sub(r'\*(.*?)\*', r'\1', content)
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[-*+]\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{2,}', '\n\n', content)
    content = content.strip()
    
    # 按段落分割
    paragraphs = content.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    print(f"\n📝 验证项目:")
    print("-" * 40)
    
    errors = []
    
    # 1. 检查是否还有标题格式
    title_patterns = [
        r'^[一二三四五六七八九十]+[、.]\s*\S',
        r'^\d+[、.]\s*\S',
        r'^#{1,3}\s+',
    ]
    
    for p in paragraphs:
        for pattern in title_patterns:
            if re.match(pattern, p):
                errors.append(f"❌ 残留标题格式: {p[:30]}...")
                break
    
    if not errors:
        print("✅ 无残留标题格式")
    
    # 2. 检查段落数量
    print(f"✅ 段落数量: {len(paragraphs)}")
    
    # 3. 检查每段内容
    print(f"\n📄 渲染后的段落内容:")
    print("-" * 40)
    for i, p in enumerate(paragraphs, 1):
        print(f"\n段落 {i}:")
        print(f"  {p[:80]}...")
    
    # 4. 检查是否完整（无截断）
    total_chars = sum(len(p) for p in paragraphs)
    print(f"\n✅ 总字符数: {total_chars}")
    
    if total_chars < 100:
        errors.append("❌ 内容可能被截断")
    
    # 最终结果
    print("\n" + "=" * 60)
    if errors:
        print("❌ 验证失败:")
        for e in errors:
            print(f"  {e}")
    else:
        print("✅ 验证通过！")
    print("=" * 60)

def test_with_real_api():
    """测试真实API并验证"""
    import requests
    import threading
    import time
    import sys
    sys.path.insert(0, '/Users/apple/.openclaw/workspace/zi-cesuan')
    
    print("\n" + "=" * 60)
    print("🌐 测试真实API")
    print("=" * 60)
    
    # 启动本地服务器
    from api.cezi import app
    
    def run():
        app.run(port=5005, debug=False, use_reloader=False)
    
    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(2)
    
    # 调用API
    resp = requests.post('http://localhost:5005/api/cezi', 
                         json={'char': '测', 'question': '事业发展'}, 
                         timeout=30)
    
    data = resp.json()
    deep_analysis = data.get('data', {}).get('deep_analysis', '')
    
    print(f"\n📥 获取到 deep_analysis ({len(deep_analysis)} 字符)")
    
    # 验证
    content = deep_analysis
    
    # 移除标题
    content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'^[一二三四五六七八九十]+[、.]', '', content)
    content = re.sub(r'^\d+[、.]\s*', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
    content = content.strip()
    
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    print(f"\n✅ 段落数量: {len(paragraphs)}")
    
    # 检查是否有残留标题
    has_title = False
    for p in paragraphs:
        if re.match(r'^[一二三四五六七八九十]+[、.]', p):
            has_title = True
            print(f"❌ 残留标题: {p[:50]}")
    
    if not has_title:
        print("✅ 无残留标题格式")

if __name__ == "__main__":
    # 先运行模拟验证
    validate_cezi_result()
    
    # 可选：测试真实API
    # test_with_real_api()
