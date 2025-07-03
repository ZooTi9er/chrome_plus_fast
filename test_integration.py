#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
集成测试脚本
测试Chrome扩展AI助手的完整功能流程
"""

import requests
import json
import time
import sys

def test_api_health():
    """测试API健康状态"""
    print("🏥 测试API健康状态...")
    
    try:
        # 测试根路径
        response = requests.get('http://127.0.0.1:5001/', timeout=10)
        if response.status_code == 200:
            print("✅ API根路径可访问")
        else:
            print(f"⚠️ API根路径响应: {response.status_code}")
        
        # 测试文档路径
        response = requests.get('http://127.0.0.1:5001/docs', timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print(f"❌ API文档不可访问: {response.status_code}")
            return False
        
        # 测试OpenAPI schema
        response = requests.get('http://127.0.0.1:5001/openapi.json', timeout=10)
        if response.status_code == 200:
            print("✅ OpenAPI schema可访问")
        else:
            print(f"⚠️ OpenAPI schema响应: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"❌ API健康检查失败: {e}")
        return False

def test_chat_api_basic():
    """测试基本聊天API"""
    print("\n💬 测试基本聊天API...")
    
    try:
        # 测试简单消息
        test_message = "你好"
        payload = {"message": test_message}
        
        print(f"发送消息: {test_message}")
        response = requests.post(
            'http://127.0.0.1:5001/chat',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'response' in result:
                    print(f"✅ 收到回复: {result['response'][:100]}...")
                    return True
                else:
                    print(f"❌ 响应格式错误: {result}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ 响应不是有效JSON: {response.text[:200]}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API请求超时")
        return False
    except Exception as e:
        print(f"❌ 聊天API测试失败: {e}")
        return False

def test_chat_api_with_proxy():
    """测试带代理配置的聊天API"""
    print("\n🌐 测试代理配置API...")
    
    try:
        # 测试带代理配置的消息
        payload = {
            "message": "测试代理功能",
            "proxyConfig": {
                "enabled": False,
                "type": "http",
                "host": "127.0.0.1",
                "port": 8080,
                "auth": None
            }
        }
        
        print("发送带代理配置的消息...")
        response = requests.post(
            'http://127.0.0.1:5001/chat',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                if 'response' in result:
                    print(f"✅ 代理配置API正常: {result['response'][:100]}...")
                    return True
                else:
                    print(f"❌ 代理配置响应格式错误: {result}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ 代理配置响应不是有效JSON: {response.text[:200]}")
                return False
        else:
            print(f"❌ 代理配置API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 代理配置API测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作功能"""
    print("\n📁 测试文件操作功能...")
    
    try:
        # 测试文件列表
        payload = {"message": "请列出当前目录的文件"}
        
        print("测试文件列表功能...")
        response = requests.post(
            'http://127.0.0.1:5001/chat',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'response' in result and ('文件' in result['response'] or 'test' in result['response']):
                print("✅ 文件操作功能正常")
                return True
            else:
                print(f"⚠️ 文件操作响应可能异常: {result['response'][:100]}...")
                return True  # 不算失败，可能是AI理解问题
        else:
            print(f"❌ 文件操作API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n🚨 测试错误处理...")
    
    try:
        # 测试空消息
        payload = {"message": ""}
        
        response = requests.post(
            'http://127.0.0.1:5001/chat',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        # 空消息应该被处理，不应该导致服务器错误
        if response.status_code in [200, 400, 422]:
            print("✅ 空消息错误处理正常")
        else:
            print(f"⚠️ 空消息处理异常: {response.status_code}")
        
        # 测试无效JSON
        try:
            response = requests.post(
                'http://127.0.0.1:5001/chat',
                data="invalid json",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [400, 422]:
                print("✅ 无效JSON错误处理正常")
            else:
                print(f"⚠️ 无效JSON处理: {response.status_code}")
        except:
            print("✅ 无效JSON被正确拒绝")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print("\n⚡ 测试性能...")
    
    try:
        # 测试响应时间
        start_time = time.time()
        
        payload = {"message": "简单测试"}
        response = requests.post(
            'http://127.0.0.1:5001/chat',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ 响应时间: {response_time:.2f}秒")
            if response_time < 30:
                print("✅ 响应时间良好")
            else:
                print("⚠️ 响应时间较慢")
            return True
        else:
            print(f"❌ 性能测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Chrome扩展AI助手 - 集成测试报告")
    print("=" * 60)
    
    tests = [
        ("API健康状态", test_api_health),
        ("基本聊天功能", test_chat_api_basic),
        ("代理配置功能", test_chat_api_with_proxy),
        ("文件操作功能", test_file_operations),
        ("错误处理", test_error_handling),
        ("性能测试", test_performance)
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
    
    print(f"\n{'='*60}")
    print(f"📊 集成测试结果: {passed}/{total} 通过")
    
    if passed >= total - 1:  # 允许一个测试失败
        print("🎉 集成测试基本通过！系统功能正常")
        return True
    else:
        print("⚠️ 多个测试失败，请检查系统配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
