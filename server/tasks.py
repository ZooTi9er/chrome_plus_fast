"""
Celery任务定义文件
处理异步任务，包括AI API调用、文件操作等
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional
from celery import Celery
from celery.utils.log import get_task_logger
import redis
import httpx
from pydantic import BaseModel

# 配置日志
logger = get_task_logger(__name__)

# Redis配置
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# 创建Celery应用
celery_app = Celery(
    'chrome_plus_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['tasks']
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    task_soft_time_limit=240,  # 4分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Redis客户端用于发布/订阅
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class TaskRequest(BaseModel):
    """任务请求模型"""
    message: str
    channel_id: str
    user_id: Optional[str] = None
    proxy_config: Optional[Dict[str, Any]] = None
    api_config: Optional[Dict[str, Any]] = None

class TaskResult(BaseModel):
    """任务结果模型"""
    success: bool
    response: str
    error: Optional[str] = None
    task_id: str
    channel_id: str

@celery_app.task(bind=True, name='process_ai_message')
def process_ai_message(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理AI消息的异步任务
    
    Args:
        task_data: 包含消息和配置的字典
        
    Returns:
        处理结果字典
    """
    try:
        # 解析任务数据
        request = TaskRequest(**task_data)
        task_id = self.request.id
        
        logger.info(f"开始处理任务 {task_id}, 频道: {request.channel_id}")
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': '正在处理AI请求...', 'progress': 10}
        )
        
        # 调用AI API
        response = _call_ai_api(request.message, request.api_config, request.proxy_config)
        
        # 更新任务状态
        self.update_state(
            state='PROGRESS',
            meta={'status': '处理完成，准备返回结果...', 'progress': 90}
        )
        
        # 构建结果
        result = TaskResult(
            success=True,
            response=response,
            task_id=task_id,
            channel_id=request.channel_id
        )
        
        # 发布结果到Redis频道
        _publish_result(request.channel_id, result.dict())
        
        logger.info(f"任务 {task_id} 处理完成")
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"任务处理失败: {str(e)}")
        
        # 构建错误结果
        error_result = TaskResult(
            success=False,
            response="",
            error=str(e),
            task_id=self.request.id,
            channel_id=task_data.get('channel_id', 'unknown')
        )
        
        # 发布错误结果
        _publish_result(task_data.get('channel_id', 'unknown'), error_result.dict())
        
        return error_result.dict()

def _call_ai_api(message: str, api_config: Optional[Dict], proxy_config: Optional[Dict]) -> str:
    """
    调用AI API
    
    Args:
        message: 用户消息
        api_config: API配置
        proxy_config: 代理配置
        
    Returns:
        AI响应
    """
    try:
        # 如果有自定义API配置，使用自定义配置
        if api_config and api_config.get('endpoint') and api_config.get('api_key'):
            return _call_custom_api(message, api_config, proxy_config)
        else:
            # 使用默认配置
            return _call_default_api(message, proxy_config)
            
    except Exception as e:
        logger.error(f"AI API调用失败: {str(e)}")
        raise

def _call_custom_api(message: str, api_config: Dict, proxy_config: Optional[Dict]) -> str:
    """调用自定义AI API"""
    endpoint = api_config['endpoint']
    api_key = api_config['api_key']
    model = api_config.get('model', 'gpt-3.5-turbo')
    
    # 确保端点包含完整路径
    if not endpoint.endswith('/chat/completions') and not endpoint.endswith('/v1/chat/completions'):
        if endpoint.endswith('/'):
            endpoint = endpoint + 'v1/chat/completions'
        else:
            endpoint = endpoint + '/v1/chat/completions'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': message}],
        'stream': False
    }
    
    # 配置代理
    proxies = None
    if proxy_config and proxy_config.get('enabled'):
        proxy_url = _build_proxy_url(proxy_config)
        proxies = {'http': proxy_url, 'https': proxy_url}
    
    # 创建HTTP客户端，根据是否有代理配置
    if proxies:
        client = httpx.Client(proxy=proxies['https'], timeout=60.0)
    else:
        client = httpx.Client(timeout=60.0)

    with client:
        response = client.post(endpoint, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if result.get('choices') and result['choices'][0].get('message'):
            return result['choices'][0]['message']['content']
        else:
            raise Exception("API响应格式异常")

def _call_default_api(message: str, proxy_config: Optional[Dict]) -> str:
    """调用智能体API（使用本地智能体和工具）"""
    try:
        # 导入智能体相关模块
        from agent_tools import create_intelligent_agent, run_agent_with_tools

        # 创建智能体实例
        agent = create_intelligent_agent(proxy_config)

        # 使用智能体处理消息
        response = run_agent_with_tools(agent, message)

        return response

    except ImportError as e:
        logger.warning(f"智能体模块导入失败，回退到基础API: {e}")
        return _call_basic_api(message, proxy_config)
    except Exception as e:
        logger.error(f"智能体调用失败: {e}")
        return _call_basic_api(message, proxy_config)

def _call_basic_api(message: str, proxy_config: Optional[Dict]) -> str:
    """调用基础DeepSeek API（回退方案）"""
    # 获取DeepSeek API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        logger.warning("未找到DEEPSEEK_API_KEY，返回测试响应")
        return f"收到消息: {message}\n\n注意：未配置API密钥，当前为测试模式。请在.env文件中设置DEEPSEEK_API_KEY。"

    # DeepSeek API配置
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
        # 创建HTTP客户端，根据是否有代理配置
        if proxies:
            client = httpx.Client(proxy=proxies['https'], timeout=60.0)
        else:
            client = httpx.Client(timeout=60.0)

        with client:
            response = client.post(endpoint, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get('choices') and result['choices'][0].get('message'):
                return result['choices'][0]['message']['content']
            else:
                raise Exception("API响应格式异常")

    except httpx.HTTPStatusError as e:
        logger.error(f"DeepSeek API HTTP错误: {e.response.status_code} - {e.response.text}")
        raise Exception(f"API调用失败: HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"DeepSeek API请求错误: {e}")
        raise Exception(f"网络请求失败: {str(e)}")
    except Exception as e:
        logger.error(f"DeepSeek API调用异常: {e}")
        raise

def _build_proxy_url(proxy_config: Dict) -> str:
    """构建代理URL"""
    proxy_type = proxy_config.get('type', 'http')
    host = proxy_config['host']
    port = proxy_config['port']
    
    auth = ""
    if proxy_config.get('auth'):
        username = proxy_config['auth']['username']
        password = proxy_config['auth']['password']
        auth = f"{username}:{password}@"
    
    return f"{proxy_type}://{auth}{host}:{port}"

def _publish_result(channel_id: str, result: Dict[str, Any]) -> None:
    """
    将结果发布到Redis频道
    
    Args:
        channel_id: 频道ID
        result: 结果数据
    """
    try:
        channel_name = f"result:{channel_id}"
        redis_client.publish(channel_name, json.dumps(result))
        logger.info(f"结果已发布到频道: {channel_name}")
    except Exception as e:
        logger.error(f"发布结果失败: {str(e)}")

@celery_app.task(name='health_check')
def health_check() -> Dict[str, Any]:
    """健康检查任务"""
    return {
        'status': 'healthy',
        'timestamp': asyncio.get_event_loop().time(),
        'worker_id': os.getpid()
    }

# 导出Celery应用供其他模块使用
__all__ = ['celery_app', 'process_ai_message', 'health_check']
