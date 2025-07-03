#!/usr/bin/env python3
"""
Chrome Plus V2.0 简化版API服务器
用于测试AI API集成
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = FastAPI(
    title="Chrome Plus V2.0 Simple API",
    description="简化版AI助手API，用于测试",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ProxyConfig(BaseModel):
    enabled: bool = False
    type: str = "http"
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    proxy_config: Optional[ProxyConfig] = None
    api_config: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool = True
    timestamp: Optional[str] = None

def _build_proxy_url(proxy_config: Dict[str, Any]) -> str:
    """构建代理URL"""
    proxy_type = proxy_config.get('type', 'http')
    host = proxy_config.get('host', '')
    port = proxy_config.get('port', 0)
    username = proxy_config.get('username')
    password = proxy_config.get('password')
    
    if username and password:
        return f"{proxy_type}://{username}:{password}@{host}:{port}"
    else:
        return f"{proxy_type}://{host}:{port}"

def call_deepseek_api(message: str, proxy_config: Optional[Dict] = None) -> str:
    """调用DeepSeek API"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        return "注意：未配置DEEPSEEK_API_KEY，当前为测试模式。请在.env文件中设置API密钥。"
    
    endpoint = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': message}],
        'stream': False,
        'temperature': 0.7,
        'max_tokens': 4000
    }
    
    # 配置代理
    proxies = None
    if proxy_config and proxy_config.get('enabled'):
        proxy_url = _build_proxy_url(proxy_config)
        proxies = {'http': proxy_url, 'https': proxy_url}
    
    try:
        with httpx.Client(timeout=60.0) as client:
            if proxies:
                client = httpx.Client(proxy=proxies['https'], timeout=60.0)
            
            response = client.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('choices') and result['choices'][0].get('message'):
                return result['choices'][0]['message']['content']
            else:
                raise Exception("API响应格式异常")
                
    except httpx.HTTPStatusError as e:
        error_msg = f"DeepSeek API HTTP错误: {e.response.status_code}"
        if e.response.status_code == 401:
            error_msg += " - API密钥无效"
        elif e.response.status_code == 429:
            error_msg += " - 请求频率限制"
        return f"错误: {error_msg}"
    except httpx.RequestError as e:
        return f"网络请求失败: {str(e)}"
    except Exception as e:
        return f"处理失败: {str(e)}"

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "2.0.0-simple",
        "message": "简化版API服务正常运行"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """聊天API端点"""
    try:
        # 调用AI API
        response_text = call_deepseek_api(
            request.message, 
            request.proxy_config.dict() if request.proxy_config else None
        )
        
        return ChatResponse(
            response=response_text,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_endpoint_simple(request: ChatRequest):
    """简化聊天端点（兼容性）"""
    try:
        response_text = call_deepseek_api(
            request.message, 
            request.proxy_config.dict() if request.proxy_config else None
        )
        
        return {
            "response": response_text,
            "success": True
        }
        
    except Exception as e:
        return {
            "response": f"处理失败: {str(e)}",
            "success": False
        }

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    uvicorn.run(app, host="0.0.0.0", port=port)
