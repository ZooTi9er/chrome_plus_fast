#!/usr/bin/env python3
"""
Chrome Plus V2.0 简化测试服务器
用于测试Chrome扩展功能，不依赖Redis和Celery
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("正在安装必要依赖...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "fastapi", "uvicorn[standard]"])
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn

# 数据模型
class ChatRequest(BaseModel):
    message: str
    proxyConfig: Dict[str, Any] = None

class ChatResponse(BaseModel):
    response: str

class ErrorResponse(BaseModel):
    detail: str

# 创建FastAPI应用
app = FastAPI(
    title="Chrome Plus V2.0 测试服务器",
    description="简化版测试服务器，用于验证Chrome扩展功能",
    version="2.0.0-test"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket连接管理
active_connections: Dict[str, WebSocket] = {}

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "2.0.0-test",
        "mode": "simplified",
        "websocket_connections": len(active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """HTTP聊天端点（兼容V1.0）"""
    try:
        message = request.message.strip()
        if not message:
            raise HTTPException(status_code=400, detail="消息内容不能为空")
        
        # 模拟AI响应
        response_text = f"""# Chrome Plus V2.0 测试响应

您发送的消息：**{message}**

🎉 **恭喜！Chrome Plus V2.0 升级成功！**

## ✅ 测试结果
- ✅ Chrome扩展加载正常
- ✅ HTTP API通信正常
- ✅ 后端服务运行正常
- ✅ 消息处理功能正常

## 🚀 V2.0新特性
- **实时通信**: WebSocket支持（测试模式）
- **异步处理**: 后台任务处理
- **微服务架构**: 容器化部署
- **智能降级**: HTTP兼容模式

## 📊 系统信息
- **服务模式**: 简化测试模式
- **响应时间**: < 100ms
- **连接状态**: HTTP兼容模式
- **时间戳**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

感谢使用Chrome Plus V2.0！🚀"""

        return ChatResponse(response=response_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点"""
    await websocket.accept()
    connection_id = f"conn_{len(active_connections)}"
    active_connections[connection_id] = websocket
    
    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connection",
            "data": {
                "status": "connected",
                "channel_id": connection_id,
                "message": "WebSocket连接已建立（测试模式）"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "chat":
                    message = data.get("data", {}).get("message", "")
                    
                    # 发送处理状态
                    await websocket.send_json({
                        "type": "status",
                        "data": {
                            "status": "processing",
                            "message": "正在处理您的请求..."
                        },
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # 模拟处理延迟
                    await asyncio.sleep(1)
                    
                    # 发送响应
                    response_text = f"""# WebSocket实时响应

您的消息：**{message}**

🎉 **WebSocket连接测试成功！**

## ✅ 实时通信特性
- ✅ 双向通信正常
- ✅ 实时状态反馈
- ✅ 消息推送正常
- ✅ 连接状态稳定

## 🚀 V2.0优势
- **实时性**: 毫秒级响应
- **并发性**: 支持多连接
- **稳定性**: 自动重连
- **兼容性**: HTTP降级

连接ID: {connection_id}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

                    await websocket.send_json({
                        "type": "result",
                        "success": True,
                        "response": response_text,
                        "channel_id": connection_id,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                elif data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()},
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"处理消息失败: {str(e)}"},
                    "timestamp": datetime.now().isoformat()
                })
                
    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        if connection_id in active_connections:
            del active_connections[connection_id]

@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "Chrome Plus V2.0 测试服务器",
        "version": "2.0.0-test",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "websocket": "/ws"
        },
        "status": "running"
    }

def main():
    """启动服务器"""
    print("🚀 启动Chrome Plus V2.0测试服务器...")
    print("📍 服务地址: http://localhost:5001")
    print("🌐 WebSocket: ws://localhost:5001/ws")
    print("💊 健康检查: http://localhost:5001/health")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=5001,
        log_level="info"
    )

if __name__ == "__main__":
    main()
