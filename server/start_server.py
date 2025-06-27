#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI服务器启动脚本
"""

import uvicorn

if __name__ == "__main__":
    print("启动 ShellAI FastAPI 服务器...")
    print("API文档地址: http://127.0.0.1:5001/docs")
    print("交互式API文档: http://127.0.0.1:5001/redoc")
    print("按 Ctrl+C 停止服务器")
    
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5001,
        log_level="info",
        reload=True,  # 开发模式下自动重载
        access_log=True
    )
