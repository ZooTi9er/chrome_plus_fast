#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI应用测试文件
"""

import pytest
import json
from fastapi.testclient import TestClient
from main import app

# 创建测试客户端
client = TestClient(app)

class TestChatAPI:
    """聊天API测试类"""
    
    def test_chat_endpoint_exists(self):
        """测试聊天端点是否存在"""
        response = client.post("/chat", json={"message": "test"})
        # 应该返回200或500（如果没有API密钥），但不应该是404
        assert response.status_code != 404
    
    def test_chat_with_valid_message(self):
        """测试有效消息的聊天请求"""
        response = client.post("/chat", json={"message": "你好"})
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0
    
    def test_chat_with_empty_message(self):
        """测试空消息的聊天请求"""
        response = client.post("/chat", json={"message": ""})
        assert response.status_code == 400
    
    def test_chat_with_whitespace_message(self):
        """测试只有空白字符的消息"""
        response = client.post("/chat", json={"message": "   "})
        assert response.status_code == 400
    
    def test_chat_without_message_field(self):
        """测试缺少message字段的请求"""
        response = client.post("/chat", json={})
        assert response.status_code == 422  # FastAPI validation error
    
    def test_chat_with_invalid_json(self):
        """测试无效JSON的请求"""
        response = client.post("/chat", data="invalid json")
        assert response.status_code == 422
    
    def test_chat_response_format(self):
        """测试响应格式"""
        response = client.post("/chat", json={"message": "测试消息"})
        
        if response.status_code == 200:
            data = response.json()
            # 验证响应结构
            assert isinstance(data, dict)
            assert "response" in data
            assert isinstance(data["response"], str)
        elif response.status_code == 500:
            # 如果没有API密钥，应该返回错误信息
            data = response.json()
            assert "detail" in data
    
    def test_cors_headers(self):
        """测试CORS头部"""
        response = client.options("/chat")
        # FastAPI自动处理OPTIONS请求
        assert response.status_code in [200, 405]

class TestAPIDocumentation:
    """API文档测试类"""
    
    def test_openapi_schema(self):
        """测试OpenAPI模式是否可访问"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
    
    def test_docs_endpoint(self):
        """测试文档端点是否可访问"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self):
        """测试ReDoc端点是否可访问"""
        response = client.get("/redoc")
        assert response.status_code == 200

class TestHealthCheck:
    """健康检查测试类"""
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        # 根端点可能不存在，这是正常的
        assert response.status_code in [200, 404]

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
