#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Plus V2.0 - 智能体服务器（简化版）
集成文件操作工具和AI智能体功能
"""

import os
import uuid
import asyncio
import json
import logging
import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# FastAPI和WebSocket
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- 数据模型 ---
class ProxyAuth(BaseModel):
    """代理认证信息"""
    username: str
    password: str

class ProxyConfig(BaseModel):
    """代理配置模型"""
    enabled: bool = False
    type: str = "http"
    host: str = ""
    port: int = 8080
    auth: Optional[ProxyAuth] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    proxyConfig: Optional[ProxyConfig] = None

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str

class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None

# WebSocket连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """接受WebSocket连接并返回频道ID"""
        await websocket.accept()
        channel_id = str(uuid.uuid4())
        self.active_connections[channel_id] = websocket
        logger.info(f"WebSocket连接建立: {channel_id}")
        return channel_id

    def disconnect(self, channel_id: str):
        """断开WebSocket连接"""
        if channel_id in self.active_connections:
            del self.active_connections[channel_id]
        logger.info(f"WebSocket连接断开: {channel_id}")

    async def send_personal_message(self, message: dict, channel_id: str):
        """发送消息到特定频道"""
        if channel_id in self.active_connections:
            websocket = self.active_connections[channel_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败 {channel_id}: {e}")
                self.disconnect(channel_id)

# 全局连接管理器实例
manager = ConnectionManager()

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Chrome Plus V2.0 智能体API",
    description="AI智能体API，支持文件操作和WebSocket实时通信",
    version="2.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": "2.0.0-agent",
        "message": "智能体服务正常运行",
        "websocket_connections": len(manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，处理实时通信"""
    channel_id = None
    try:
        # 建立连接
        channel_id = await manager.connect(websocket)

        # 发送连接确认
        await manager.send_personal_message({
            "type": "connection",
            "data": {
                "status": "connected",
                "channel_id": channel_id,
                "message": "WebSocket连接已建立，智能体已就绪"
            },
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

        # 监听消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()

                # 验证消息格式
                if not isinstance(data, dict) or 'type' not in data:
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": "无效的消息格式"},
                        "timestamp": datetime.datetime.now().isoformat()
                    }, channel_id)
                    continue

                message_type = data.get('type')

                if message_type == 'chat':
                    # 处理聊天消息
                    await handle_chat_message(data, channel_id)
                elif message_type == 'ping':
                    # 处理心跳
                    await manager.send_personal_message({
                        "type": "pong",
                        "data": {"timestamp": datetime.datetime.now().isoformat()},
                        "timestamp": datetime.datetime.now().isoformat()
                    }, channel_id)
                else:
                    await manager.send_personal_message({
                        "type": "error",
                        "data": {"message": f"不支持的消息类型: {message_type}"},
                        "timestamp": datetime.datetime.now().isoformat()
                    }, channel_id)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket消息处理错误: {e}")
                await manager.send_personal_message({
                    "type": "error",
                    "data": {"message": f"消息处理失败: {str(e)}"},
                    "timestamp": datetime.datetime.now().isoformat()
                }, channel_id)

    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        if channel_id:
            manager.disconnect(channel_id)

async def handle_chat_message(data: dict, channel_id: str):
    """处理聊天消息"""
    try:
        # 解析聊天请求
        chat_data = data.get('data', {})
        message = chat_data.get('message', '').strip()

        if not message:
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": "消息内容不能为空"},
                "timestamp": datetime.datetime.now().isoformat()
            }, channel_id)
            return

        # 发送处理状态
        await manager.send_personal_message({
            "type": "status",
            "data": {
                "status": "processing",
                "message": "智能体正在处理您的请求..."
            },
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

        # 处理消息
        try:
            from agent_tools import create_intelligent_agent, run_agent_with_tools
            
            # 创建智能体
            agent = create_intelligent_agent(chat_data.get('proxy_config'))
            
            # 处理消息
            response = run_agent_with_tools(agent, message)
            
            # 发送结果
            await manager.send_personal_message({
                "type": "result",
                "data": {
                    "response": response,
                    "success": True
                },
                "timestamp": datetime.datetime.now().isoformat()
            }, channel_id)
            
            logger.info(f"智能体处理完成，频道: {channel_id}")
            
        except Exception as e:
            logger.error(f"智能体处理失败: {e}")
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": f"智能体处理失败: {str(e)}"},
                "timestamp": datetime.datetime.now().isoformat()
            }, channel_id)

    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"处理失败: {str(e)}"},
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """聊天API端点"""
    user_message = request.message
    proxy_config = request.proxyConfig

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    try:
        logger.info(f"HTTP聊天请求: {user_message}")

        # 处理消息
        from agent_tools import create_intelligent_agent, run_agent_with_tools
        
        # 创建智能体
        agent = create_intelligent_agent(proxy_config.dict() if proxy_config else None)
        
        # 处理消息
        response = run_agent_with_tools(agent, user_message)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error(f"HTTP聊天处理失败: {e}")
        fallback_response = f"Chrome Plus V2.0 智能体响应：收到消息 '{user_message}'。\n\n" \
                          f"注意：智能体处理失败，错误: {str(e)}"
        return ChatResponse(response=fallback_response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")
