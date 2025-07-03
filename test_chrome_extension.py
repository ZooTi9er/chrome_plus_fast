#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chrome扩展测试脚本
测试Chrome扩展的基本配置和文件完整性
"""

import json
import os
import sys
from pathlib import Path

def test_manifest_json():
    """测试manifest.json文件"""
    print("📋 测试 manifest.json...")
    
    try:
        with open('manifest.json', 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # 检查必需字段
        required_fields = ['manifest_version', 'name', 'version', 'permissions']
        for field in required_fields:
            if field not in manifest:
                print(f"❌ 缺少必需字段: {field}")
                return False
        
        # 检查manifest版本
        if manifest['manifest_version'] != 3:
            print(f"❌ Manifest版本错误: {manifest['manifest_version']}, 应该是3")
            return False
        
        # 检查权限
        if 'sidePanel' not in manifest['permissions']:
            print("❌ 缺少sidePanel权限")
            return False
        
        print(f"✅ manifest.json 验证通过")
        print(f"   - 扩展名称: {manifest['name']}")
        print(f"   - 版本: {manifest['version']}")
        print(f"   - Manifest版本: {manifest['manifest_version']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ manifest.json JSON语法错误: {e}")
        return False
    except FileNotFoundError:
        print("❌ 找不到 manifest.json 文件")
        return False

def test_required_files():
    """测试必需文件是否存在"""
    print("\n📁 测试必需文件...")
    
    required_files = [
        'sidepanel.html',
        'sidepanel.css', 
        'background.js',
        'chat.js',
        'api.js'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            size = os.path.getsize(file)
            print(f"✅ {file} ({size} bytes)")
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    return True

def test_icon_files():
    """测试图标文件"""
    print("\n🖼️ 测试图标文件...")
    
    required_icons = [
        'images/icon-16.png',
        'images/icon-48.png', 
        'images/icon-128.png'
    ]
    
    missing_icons = []
    for icon in required_icons:
        if not os.path.exists(icon):
            missing_icons.append(icon)
        else:
            size = os.path.getsize(icon)
            print(f"✅ {icon} ({size} bytes)")
    
    if missing_icons:
        print(f"❌ 缺少图标: {', '.join(missing_icons)}")
        return False
    
    return True

def test_html_structure():
    """测试HTML文件结构"""
    print("\n🌐 测试 HTML 结构...")
    
    try:
        with open('sidepanel.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 检查关键元素
        required_elements = [
            'chat-container',
            'chat-box',
            'message-input',
            'send-button',
            'settings-modal'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html_content:
                missing_elements.append(element)
            else:
                print(f"✅ 找到元素: {element}")
        
        if missing_elements:
            print(f"❌ 缺少HTML元素: {', '.join(missing_elements)}")
            return False
        
        # 检查外部依赖
        if 'marked.min.js' in html_content:
            print("✅ 包含 Markdown 渲染库")
        else:
            print("⚠️ 未找到 Markdown 渲染库")
        
        if 'highlight.js' in html_content:
            print("✅ 包含代码高亮库")
        else:
            print("⚠️ 未找到代码高亮库")
        
        return True
        
    except FileNotFoundError:
        print("❌ 找不到 sidepanel.html 文件")
        return False

def test_backend_connection():
    """测试后端连接配置"""
    print("\n🔌 测试后端连接配置...")
    
    try:
        with open('api.js', 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        # 检查API基础URL
        if 'localhost:5001' in api_content:
            print("✅ 找到后端API地址配置")
        else:
            print("⚠️ 未找到标准的后端API地址")
        
        # 检查关键函数
        if 'sendMessageToBackend' in api_content:
            print("✅ 找到消息发送函数")
        else:
            print("❌ 缺少消息发送函数")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ 找不到 api.js 文件")
        return False

def test_backend_service():
    """测试后端服务是否运行"""
    print("\n🖥️ 测试后端服务...")
    
    try:
        import requests
        response = requests.get('http://127.0.0.1:5001/docs', timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
            print("✅ API文档可访问")
            return True
        else:
            print(f"❌ 后端服务响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://127.0.0.1:5001)")
        print("   请确保运行: cd server && uv run python start_server.py")
        return False
    except ImportError:
        print("⚠️ 未安装 requests 库，跳过后端连接测试")
        return True

def main():
    """主测试函数"""
    print("🧪 Chrome扩展AI助手 - 测试报告")
    print("=" * 50)
    
    tests = [
        ("Manifest配置", test_manifest_json),
        ("必需文件", test_required_files), 
        ("图标文件", test_icon_files),
        ("HTML结构", test_html_structure),
        ("后端连接配置", test_backend_connection),
        ("后端服务", test_backend_service)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Chrome扩展配置正确")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
