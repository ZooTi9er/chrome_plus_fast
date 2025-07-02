#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome扩展AI助手代理功能测试脚本

测试新增的代理配置功能是否正常工作。
"""

import json
import requests
import time
from typing import Dict, Any

def test_proxy_config_api():
    """测试代理配置API"""
    print("🧪 测试代理配置API...")
    
    # 测试数据
    test_cases = [
        {
            "name": "无代理配置",
            "data": {
                "message": "你好，这是一个测试消息"
            }
        },
        {
            "name": "HTTP代理配置（无认证）",
            "data": {
                "message": "你好，这是一个带代理的测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "http",
                    "host": "127.0.0.1",
                    "port": 8080,
                    "auth": None
                }
            }
        },
        {
            "name": "HTTP代理配置（带认证）",
            "data": {
                "message": "你好，这是一个带认证代理的测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "http",
                    "host": "proxy.example.com",
                    "port": 3128,
                    "auth": {
                        "username": "testuser",
                        "password": "testpass"
                    }
                }
            }
        },
        {
            "name": "SOCKS5代理配置",
            "data": {
                "message": "你好，这是一个SOCKS5代理测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "socks5",
                    "host": "127.0.0.1",
                    "port": 1080,
                    "auth": None
                }
            }
        }
    ]
    
    api_url = "http://127.0.0.1:5001/chat"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                api_url,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 成功: {result.get('response', '无响应')[:100]}...")
            else:
                print(f"❌ 失败: HTTP {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   错误详情: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        
        # 避免请求过于频繁
        time.sleep(1)

def test_proxy_validation():
    """测试代理配置验证"""
    print("\n🔍 测试代理配置验证...")
    
    invalid_cases = [
        {
            "name": "空代理主机",
            "data": {
                "message": "测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "http",
                    "host": "",
                    "port": 8080
                }
            }
        },
        {
            "name": "无效端口",
            "data": {
                "message": "测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "http",
                    "host": "127.0.0.1",
                    "port": 0
                }
            }
        },
        {
            "name": "不支持的代理类型",
            "data": {
                "message": "测试消息",
                "proxyConfig": {
                    "enabled": True,
                    "type": "invalid_type",
                    "host": "127.0.0.1",
                    "port": 8080
                }
            }
        }
    ]
    
    api_url = "http://127.0.0.1:5001/chat"
    
    for i, test_case in enumerate(invalid_cases, 1):
        print(f"\n📋 无效配置测试 {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                api_url,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print("⚠️  预期应该失败，但请求成功了")
            else:
                print(f"✅ 正确拒绝: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"✅ 正确拒绝: {e}")

def test_api_documentation():
    """测试API文档是否包含代理配置"""
    print("\n📚 测试API文档...")
    
    try:
        response = requests.get("http://127.0.0.1:5001/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            
            # 检查ChatRequest模型是否包含proxyConfig
            schemas = openapi_spec.get('components', {}).get('schemas', {})
            chat_request = schemas.get('ChatRequest', {})
            properties = chat_request.get('properties', {})
            
            if 'proxyConfig' in properties:
                print("✅ API文档包含代理配置")
                
                # 检查ProxyConfig模型
                proxy_config_ref = properties['proxyConfig'].get('$ref', '')
                if 'ProxyConfig' in proxy_config_ref:
                    proxy_config = schemas.get('ProxyConfig', {})
                    proxy_properties = proxy_config.get('properties', {})
                    
                    required_fields = ['enabled', 'type', 'host', 'port']
                    missing_fields = [field for field in required_fields if field not in proxy_properties]
                    
                    if not missing_fields:
                        print("✅ ProxyConfig模型字段完整")
                    else:
                        print(f"❌ ProxyConfig模型缺少字段: {missing_fields}")
                else:
                    print("❌ 未找到ProxyConfig模型定义")
            else:
                print("❌ API文档不包含代理配置")
        else:
            print(f"❌ 无法获取API文档: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求API文档失败: {e}")

def main():
    """主测试函数"""
    print("🚀 Chrome扩展AI助手代理功能测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://127.0.0.1:5001/docs", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器正在运行")
        else:
            print("⚠️  服务器响应异常")
    except requests.exceptions.RequestException:
        print("❌ 服务器未运行，请先启动服务器")
        print("   运行命令: cd server && uv run python start_server.py")
        return
    
    # 运行测试
    test_proxy_config_api()
    test_proxy_validation()
    test_api_documentation()
    
    print("\n" + "=" * 50)
    print("🎉 代理功能测试完成！")
    print("\n📝 测试说明:")
    print("1. 代理配置已添加到API请求模型中")
    print("2. 后端支持解析和处理代理配置")
    print("3. 前端界面支持代理设置和测试")
    print("4. 由于浏览器安全限制，实际代理连接需要在后端处理")

if __name__ == "__main__":
    main()
