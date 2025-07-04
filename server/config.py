#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用配置文件
"""

import os
from pathlib import Path
from typing import List

class Settings:
    """应用设置"""

    # 服务器配置
    HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    PORT: int = 5001
    DEBUG: bool = True
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = [
        "chrome-extension://*",
        "http://localhost:*",
        "http://127.0.0.1:*"
    ]
    
    # API配置
    API_TITLE: str = "ShellAI API"
    API_DESCRIPTION: str = "AI助手API，支持文件操作和聊天功能"
    API_VERSION: str = "1.0.0"
    
    # 文件操作基础目录
    BASE_DIR: Path = Path(__file__).parent.resolve() / "test"
    
    # 环境变量
    DEEPSEEK_API_KEY: str = os.getenv('DEEPSEEK_API_KEY', '')
    TAVILY_API_KEY: str = os.getenv('TAVILY_API_KEY', '')
    
    def __init__(self):
        # 确保基础目录存在
        os.makedirs(self.BASE_DIR, exist_ok=True)

# 全局设置实例
settings = Settings()
