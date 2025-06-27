#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动测试脚本 - 验证FastAPI应用功能
"""

import requests
import json
import time

def test_fastapi_server():
    """测试FastAPI服务器功能"""
    base_url = "http://127.0.0.1:5001"
    
    print("🚀 开始测试FastAPI服务器...")
    
    # 测试1: 基本聊天功能
    print("\n📝 测试1: 基本聊天功能")
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"message": "你好，请介绍一下你自己"},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data['response'][:100]}...")
            print("✅ 基本聊天功能正常")
        else:
            print(f"❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False
    
    # 测试2: 文件操作功能
    print("\n📁 测试2: 文件操作功能")
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"message": "请创建一个名为test.txt的文件，内容是'Hello FastAPI'"},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"响应: {data['response'][:100]}...")
            print("✅ 文件操作功能正常")
        else:
            print(f"❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试3: 错误处理
    print("\n❌ 测试3: 错误处理")
    try:
        response = requests.post(
            f"{base_url}/chat",
            json={"message": ""},
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 400:
            print("✅ 空消息错误处理正常")
        else:
            print(f"⚠️  预期400状态码，实际: {response.status_code}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试4: API文档
    print("\n📚 测试4: API文档")
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"文档页面状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API文档可访问")
        else:
            print(f"❌ API文档不可访问: {response.status_code}")
            
        response = requests.get(f"{base_url}/openapi.json")
        print(f"OpenAPI模式状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ OpenAPI模式可访问")
        else:
            print(f"❌ OpenAPI模式不可访问: {response.status_code}")
    except Exception as e:
        print(f"❌ 文档测试失败: {e}")
    
    print("\n🎉 测试完成！")
    return True

def test_performance():
    """简单的性能测试"""
    base_url = "http://127.0.0.1:5001"
    
    print("\n⚡ 性能测试...")
    
    # 发送10个请求并测量时间
    times = []
    for i in range(10):
        start_time = time.time()
        try:
            response = requests.post(
                f"{base_url}/chat",
                json={"message": f"测试消息 {i+1}"},
                headers={"Content-Type": "application/json"}
            )
            end_time = time.time()
            if response.status_code == 200:
                times.append(end_time - start_time)
                print(f"请求 {i+1}: {end_time - start_time:.2f}秒")
        except Exception as e:
            print(f"请求 {i+1} 失败: {e}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n平均响应时间: {avg_time:.2f}秒")
        print(f"最快响应: {min(times):.2f}秒")
        print(f"最慢响应: {max(times):.2f}秒")

if __name__ == "__main__":
    print("请确保FastAPI服务器正在运行 (python start_server.py)")
    input("按Enter键开始测试...")
    
    if test_fastapi_server():
        test_performance()
    else:
        print("基本功能测试失败，跳过性能测试")
