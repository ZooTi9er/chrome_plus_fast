#!/usr/bin/env python3
"""
Chrome Plus V2.0 架构测试脚本
测试WebSocket连接、Celery任务处理和Redis通信
"""

import asyncio
import json
import time
import websockets
import requests
from typing import Dict, Any

# 测试配置
API_BASE_URL = "http://localhost:5001"
WS_URL = "ws://localhost:5001/ws"

class ArchitectureTest:
    """V2.0架构测试类"""
    
    def __init__(self):
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Health Check",
                    True,
                    "健康检查端点正常",
                    {
                        "status": data.get("status"),
                        "version": data.get("version"),
                        "redis": data.get("redis"),
                        "celery": data.get("celery"),
                        "websocket_connections": data.get("websocket_connections")
                    }
                )
                return True
            else:
                self.log_test(
                    "Health Check",
                    False,
                    f"健康检查失败，状态码: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Health Check",
                False,
                f"健康检查异常: {str(e)}"
            )
            return False
    
    async def test_websocket_connection(self):
        """测试WebSocket连接"""
        try:
            async with websockets.connect(WS_URL) as websocket:
                # 等待连接确认消息
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                
                if data.get("type") == "connection" and data.get("data", {}).get("status") == "connected":
                    channel_id = data.get("data", {}).get("channel_id")
                    self.log_test(
                        "WebSocket Connection",
                        True,
                        "WebSocket连接建立成功",
                        {"channel_id": channel_id}
                    )
                    return True, websocket, channel_id
                else:
                    self.log_test(
                        "WebSocket Connection",
                        False,
                        "WebSocket连接确认消息格式异常",
                        {"received": data}
                    )
                    return False, None, None
                    
        except Exception as e:
            self.log_test(
                "WebSocket Connection",
                False,
                f"WebSocket连接失败: {str(e)}"
            )
            return False, None, None
    
    async def test_websocket_ping_pong(self, websocket):
        """测试WebSocket心跳"""
        try:
            # 发送ping消息
            ping_message = {
                "type": "ping",
                "data": {"timestamp": time.time()}
            }
            await websocket.send(json.dumps(ping_message))
            
            # 等待pong响应
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") == "pong":
                self.log_test(
                    "WebSocket Ping-Pong",
                    True,
                    "WebSocket心跳测试成功"
                )
                return True
            else:
                self.log_test(
                    "WebSocket Ping-Pong",
                    False,
                    "WebSocket心跳响应格式异常",
                    {"received": data}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "WebSocket Ping-Pong",
                False,
                f"WebSocket心跳测试失败: {str(e)}"
            )
            return False
    
    async def test_websocket_chat(self, websocket):
        """测试WebSocket聊天功能"""
        try:
            # 发送聊天消息
            chat_message = {
                "type": "chat",
                "data": {
                    "message": "测试消息：Chrome Plus V2.0 架构测试",
                    "user_id": "test_user"
                }
            }
            await websocket.send(json.dumps(chat_message))
            
            # 等待处理状态消息
            status_received = False
            queued_received = False
            result_received = False
            
            for _ in range(10):  # 最多等待10个消息
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(response)
                    
                    message_type = data.get("type")
                    
                    if message_type == "status":
                        status = data.get("data", {}).get("status")
                        if status == "processing":
                            status_received = True
                        elif status == "queued":
                            queued_received = True
                            
                    elif message_type == "result":
                        result_received = True
                        success = data.get("success", False)
                        response_text = data.get("response", "")
                        
                        self.log_test(
                            "WebSocket Chat",
                            success,
                            "WebSocket聊天测试完成",
                            {
                                "status_received": status_received,
                                "queued_received": queued_received,
                                "response_length": len(response_text)
                            }
                        )
                        return success
                        
                    elif message_type == "error":
                        error_msg = data.get("data", {}).get("message", "未知错误")
                        self.log_test(
                            "WebSocket Chat",
                            False,
                            f"WebSocket聊天收到错误: {error_msg}"
                        )
                        return False
                        
                except asyncio.TimeoutError:
                    break
            
            self.log_test(
                "WebSocket Chat",
                False,
                "WebSocket聊天测试超时，未收到结果"
            )
            return False
            
        except Exception as e:
            self.log_test(
                "WebSocket Chat",
                False,
                f"WebSocket聊天测试失败: {str(e)}"
            )
            return False
    
    def test_http_chat_compatibility(self):
        """测试HTTP聊天兼容性"""
        try:
            payload = {
                "message": "HTTP兼容性测试消息"
            }
            
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                self.log_test(
                    "HTTP Chat Compatibility",
                    True,
                    "HTTP聊天兼容性测试成功",
                    {"response_length": len(response_text)}
                )
                return True
            else:
                self.log_test(
                    "HTTP Chat Compatibility",
                    False,
                    f"HTTP聊天请求失败，状态码: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test(
                "HTTP Chat Compatibility",
                False,
                f"HTTP聊天兼容性测试失败: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Chrome Plus V2.0 架构测试开始")
        print("=" * 50)
        
        # 1. 健康检查
        health_ok = self.test_health_endpoint()
        
        if not health_ok:
            print("\n❌ 健康检查失败，跳过其他测试")
            return
        
        # 2. WebSocket连接测试
        ws_connected, websocket, channel_id = await self.test_websocket_connection()
        
        if ws_connected and websocket:
            # 3. WebSocket心跳测试
            await self.test_websocket_ping_pong(websocket)
            
            # 4. WebSocket聊天测试
            await self.test_websocket_chat(websocket)
            
            # 关闭WebSocket连接
            await websocket.close()
        
        # 5. HTTP兼容性测试
        self.test_http_chat_compatibility()
        
        # 输出测试总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！Chrome Plus V2.0 架构运行正常")
        else:
            print(f"\n⚠️ {failed_tests} 个测试失败，请检查系统配置")

async def main():
    """主函数"""
    tester = ArchitectureTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
