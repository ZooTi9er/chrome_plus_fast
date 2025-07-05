#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Plus V2.1.1 - 后端服务
支持WebSocket实时通信、Celery异步任务处理和Redis消息队列
"""

from pathlib import Path
import os
import uuid
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import datetime
import difflib
import re
import shutil
import zipfile
import tarfile
import httpx
import ast

# 环境和配置
from dotenv import load_dotenv

# FastAPI和WebSocket
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Redis（可选依赖）
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# AI模块 (可选，用于兼容性)
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.messages import ModelMessage
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    Agent = None
    OpenAIModel = None
    OpenAIProvider = None
    ModelMessage = None

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 检查Redis可用性
if not REDIS_AVAILABLE:
    logger.warning("Redis不可用，将禁用Redis相关功能")

# --- 环境配置 ---
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# AI API配置
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
tavily_api_key = os.getenv('TAVILY_API_KEY')
if not deepseek_api_key:
    logger.warning("未找到 DEEPSEEK_API_KEY，使用测试模式")
if not tavily_api_key:
    logger.warning("未找到 TAVILY_API_KEY，网络搜索功能将不可用")

# Redis连接池
redis_pool = None

# WebSocket连接管理器
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_channels: Dict[str, str] = {}  # user_id -> channel_id

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """接受WebSocket连接并返回频道ID"""
        await websocket.accept()
        channel_id = str(uuid.uuid4())
        self.active_connections[channel_id] = websocket

        if user_id:
            self.user_channels[user_id] = channel_id

        logger.info(f"WebSocket连接建立: {channel_id}")
        return channel_id

    def disconnect(self, channel_id: str):
        """断开WebSocket连接"""
        if channel_id in self.active_connections:
            del self.active_connections[channel_id]

        # 清理用户频道映射
        for user_id, ch_id in list(self.user_channels.items()):
            if ch_id == channel_id:
                del self.user_channels[user_id]
                break

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

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = []
        for channel_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败 {channel_id}: {e}")
                disconnected.append(channel_id)

        # 清理断开的连接
        for channel_id in disconnected:
            self.disconnect(channel_id)

# 全局连接管理器实例
manager = ConnectionManager()

# Redis发布/订阅监听器
async def redis_listener():
    """监听Redis发布/订阅消息并转发到WebSocket"""
    global redis_pool
    if not redis_pool or not REDIS_AVAILABLE:
        logger.info("Redis不可用，跳过Redis监听器")
        return

    pubsub = redis_pool.pubsub()

    try:
        # 订阅所有结果频道
        await pubsub.psubscribe("result:*")
        logger.info("Redis监听器启动，订阅result:*频道")

        async for message in pubsub.listen():
            if message['type'] == 'pmessage':
                try:
                    # 解析频道名获取channel_id
                    channel_pattern = message['pattern'].decode('utf-8')
                    channel_name = message['channel'].decode('utf-8')
                    channel_id = channel_name.replace('result:', '')

                    # 解析消息数据
                    data = json.loads(message['data'].decode('utf-8'))

                    # 转发到对应的WebSocket连接
                    await manager.send_personal_message(data, channel_id)
                    logger.info(f"转发消息到频道 {channel_id}")

                except Exception as e:
                    logger.error(f"处理Redis消息失败: {e}")

    except Exception as e:
        logger.error(f"Redis监听器错误: {e}")
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global redis_pool

    # 启动时初始化
    logger.info("Chrome Plus V2.0 后端服务启动中...")

    try:
        # 初始化Redis连接池（如果可用）
        if REDIS_AVAILABLE:
            try:
                redis_pool = redis.ConnectionPool.from_url(REDIS_URL)
                redis_client = redis.Redis(connection_pool=redis_pool)

                # 测试Redis连接
                await redis_client.ping()
                logger.info("Redis连接成功")

                # 启动Redis监听器
                redis_task = asyncio.create_task(redis_listener())
            except Exception as e:
                logger.warning(f"Redis连接失败，将禁用Redis功能: {e}")
                redis_pool = None
        else:
            logger.info("Redis不可用，跳过Redis初始化")
            redis_pool = None

        logger.info("后端服务启动完成")

        yield

    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        raise
    finally:
        # 关闭时清理
        logger.info("正在关闭服务...")

        if 'redis_task' in locals():
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass

        if redis_pool:
            await redis_pool.disconnect()

        logger.info("服务已关闭")

# 全局基础目录
base_dir = Path(__file__).parent.resolve() / "test"
os.makedirs(base_dir, exist_ok=True)

# --- Pydantic 模型定义 ---
class ProxyAuth(BaseModel):
    """代理认证信息"""
    username: str
    password: str

class ProxyConfig(BaseModel):
    """代理配置模型"""
    enabled: bool = False
    type: str = "http"  # http, https, socks5
    host: str = ""
    port: int = 8080
    auth: Optional[ProxyAuth] = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    proxyConfig: Optional[ProxyConfig] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好，请帮我创建一个文件",
                "proxyConfig": {
                    "enabled": True,
                    "type": "http",
                    "host": "127.0.0.1",
                    "port": 8080,
                    "auth": {
                        "username": "user",
                        "password": "pass"
                    }
                }
            }
        }

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str

    class Config:
        json_schema_extra = {
            "example": {
                "response": "你好！我可以帮你创建文件。请告诉我文件名和内容。"
            }
        }

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str

    class Config:
        json_schema_extra = {
            "example": {
                "error": "请求处理失败"
            }
        }

# --- 代理配置函数 ---
def _get_proxy_url(proxy_config: ProxyConfig) -> Optional[str]:
    """根据ProxyConfig构建代理URL"""
    if proxy_config and proxy_config.enabled and proxy_config.host and proxy_config.port:
        if proxy_config.auth:
            import urllib.parse
            username = urllib.parse.quote(proxy_config.auth.username)
            password = urllib.parse.quote(proxy_config.auth.password)
            return f"{proxy_config.type}://{username}:{password}@{proxy_config.host}:{proxy_config.port}"
        else:
            return f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}"
    return None

def create_async_http_client_with_proxy(proxy_config: Optional[ProxyConfig] = None) -> httpx.AsyncClient:
    """创建带代理配置的异步HTTP客户端"""
    client_kwargs = {
        'timeout': httpx.Timeout(30.0, connect=10.0),
        'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10),
        'follow_redirects': True,
    }
    proxy_url = _get_proxy_url(proxy_config)
    if proxy_url:
        logger.info(f"使用代理: {proxy_config.type}://{proxy_config.host}:{proxy_config.port}")
        client_kwargs['proxies'] = proxy_url
    return httpx.AsyncClient(**client_kwargs)

def create_sync_http_client_with_proxy(proxy_config: Optional[ProxyConfig] = None) -> httpx.Client:
    """创建带代理配置的同步HTTP客户端"""
    client_kwargs = {
        'timeout': httpx.Timeout(30.0, connect=10.0),
        'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10),
        'follow_redirects': True,
    }
    proxy_url = _get_proxy_url(proxy_config)
    if proxy_url:
        logger.info(f"使用代理: {proxy_config.type}://{proxy_config.host}:{proxy_config.port}")
        client_kwargs['proxies'] = proxy_url
    return httpx.Client(**client_kwargs)


def create_openai_model_with_proxy(proxy_config: Optional[ProxyConfig] = None):
    """创建带代理配置的OpenAI模型"""
    if not deepseek_api_key or not PYDANTIC_AI_AVAILABLE:
        return None

    try:
        http_client = create_async_http_client_with_proxy(proxy_config)
        provider = OpenAIProvider(
            base_url='https://api.deepseek.com',
            api_key=deepseek_api_key,
            http_client=http_client
        )
        return OpenAIModel('deepseek-chat', provider=provider)
    except Exception as e:
        logger.error(f"创建代理模型失败: {e}")
        return None

async def test_proxy_connection(proxy_config: ProxyConfig) -> tuple[bool, str]:
    """测试代理连接"""
    client = create_async_http_client_with_proxy(proxy_config)
    try:
        test_url = "https://httpbin.org/ip"
        response = await client.get(test_url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return True, f"代理连接成功，IP: {data.get('origin', 'unknown')}"
    except Exception as e:
        return False, f"代理连接测试失败: {str(e)}"
    finally:
        await client.aclose()

def validate_proxy_config(proxy_config: Optional[ProxyConfig]) -> tuple[bool, str]:
    """验证代理配置"""
    if not proxy_config or not proxy_config.enabled:
        return True, ""
    if not proxy_config.host or not proxy_config.host.strip():
        return False, "代理地址不能为空"
    if not proxy_config.port or not (1 <= proxy_config.port <= 65535):
        return False, "代理端口必须在1-65535之间"
    if proxy_config.type not in ['http', 'https', 'socks5']:
        return False, f"不支持的代理类型: {proxy_config.type}"
    if proxy_config.auth:
        if not proxy_config.auth.username or not proxy_config.auth.username.strip():
            return False, "代理用户名不能为空"
        if not proxy_config.auth.password: # 允许空密码
            return False, "代理密码不能为空"
    return True, ""

# --- 数据模型 ---
class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    channel_id: Optional[str] = None

class ChatWebSocketRequest(BaseModel):
    """WebSocket聊天请求模型"""
    message: str
    user_id: Optional[str] = None
    proxy_config: Optional[ProxyConfig] = None
    api_config: Optional[Dict[str, Any]] = None

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="Chrome Plus V2.1.1 API",
    description="AI智能体API，支持WebSocket实时通信、Redis消息队列、文件操作和网络搜索",
    version="2.1.1",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 工具函数：路径验证 (保持不变) ---
def _validate_path(target_path: Path, check_existence=False, expect_dir=False, expect_file=False):
    try:
        if not base_dir.exists() or not base_dir.is_dir():
            return False, f"错误：基础目录 '{base_dir}' 不存在或不是目录。"
        resolved = target_path.resolve()
        resolved_base_dir = base_dir.resolve()
        if not (resolved == resolved_base_dir or \
                str(resolved).startswith(str(resolved_base_dir) + os.sep)):
            return False, f"错误：路径 '{resolved}' 超出了允许的操作范围 '{base_dir}'。"
        if check_existence and not resolved.exists():
            return False, f"错误：路径 '{target_path}' 不存在。"
        if resolved.exists():
            if expect_dir and not resolved.is_dir():
                return False, f"错误：路径 '{target_path}' 不是一个目录。"
            if expect_file and not resolved.is_file():
                return False, f"错误：路径 '{target_path}' 不是一个文件。"
        elif expect_dir or expect_file:
             pass # 允许路径在检查时不必须存在，如果只是为了后续创建
        return True, ""
    except Exception as e:
        return False, f"路径验证时发生异常：{e}"

# --- 文件操作工具 (保持不变) ---
def read_file(name: str) -> str:
    print(f"(read_file '{name}')")
    p = base_dir / name
    ok, msg = _validate_path(p, check_existence=True, expect_file=True)
    if not ok: return msg
    try: return p.read_text(encoding='utf-8')
    except Exception as e: return f"读取文件 '{name}' 时发生错误：{e}"
def list_files(path: str = ".") -> list[str]:
    print(f"(list_files '{path}')")
    p = (base_dir / path); ok, msg = _validate_path(p, check_existence=True, expect_dir=True)
    if not ok: return [msg]
    resolved_p = p.resolve(); items = []
    for item in sorted(resolved_p.iterdir(), key=lambda x:(x.is_file(), x.name.lower())):
        stat = item.stat(); mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        if item.is_dir(): items.append(f"{item.name}/ (目录, ---, {mtime})")
        else: items.append(f"{item.name} (文件, {stat.st_size} bytes, {mtime})")
    return items or [f"目录 '{path}' 为空。"]
def rename_file(name: str, new_name: str) -> str:
    print(f"(rename_file '{name}' -> '{new_name}')"); src_path = base_dir / name; dst_path = base_dir / new_name
    ok_src, msg_src = _validate_path(src_path, check_existence=True)
    if not ok_src: return msg_src
    ok_dst, msg_dst = _validate_path(dst_path, check_existence=False) # Destination may not exist
    if not ok_dst: return msg_dst
    try: dst_path.parent.mkdir(parents=True, exist_ok=True); os.rename(src_path, dst_path); return f"重命名成功：'{name}' → '{new_name}'"
    except Exception as e: return f"重命名文件/目录时发生错误：{e}"
def write_file(name: str, content: str, mode: str = 'w') -> str:
    print(f"(write_file '{name}' mode='{mode}')"); p = base_dir / name
    ok, msg = _validate_path(p, check_existence=False)
    if not ok: return msg
    if p.exists() and p.is_dir(): return f"错误：路径 '{name}' 是一个目录，无法写入文件。"
    if mode not in ('w', 'a'): return f"错误：不支持的写入模式 '{mode}'。请使用 'w' 或 'a'。"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode, encoding='utf-8') as f: f.write(content)
        return f"成功向 '{name}' 写入 {len(content.encode('utf-8'))} 字节。"
    except Exception as e: return f"写入文件 '{name}' 时发生错误：{e}"
def create_directory(name: str) -> str:
    print(f"(create_directory '{name}')"); p = base_dir / name
    ok, msg = _validate_path(p, check_existence=False)
    if not ok: return msg
    if p.exists(): return f"错误：路径 '{name}' 已存在。"
    try: p.mkdir(parents=True, exist_ok=False); return f"目录 '{name}' 创建成功。" # exist_ok=False to error if exists
    except FileExistsError: return f"错误：路径 '{name}' 已存在。"
    except Exception as e: return f"创建目录 '{name}' 失败：{e}"
def delete_file(name: str) -> str:
    print(f"(delete_file '{name}')"); p = base_dir / name
    ok, msg = _validate_path(p, check_existence=True, expect_file=True)
    if not ok: return msg
    try: p.unlink(); return f"文件 '{name}' 删除成功。"
    except Exception as e: return f"删除文件 '{name}' 时发生错误：{e}"
def pwd() -> str: print("(pwd)"); return f"当前操作目录限制在: './{base_dir.name}/'"
def diff_files(f1: str, f2: str) -> str:
    print(f"(diff_files '{f1}' '{f2}')"); path1 = base_dir / f1; path2 = base_dir / f2
    ok1, msg1 = _validate_path(path1, check_existence=True, expect_file=True)
    if not ok1: return msg1
    ok2, msg2 = _validate_path(path2, check_existence=True, expect_file=True)
    if not ok2: return msg2
    try:
        lines1 = path1.read_text(encoding='utf-8').splitlines(keepends=True)
        lines2 = path2.read_text(encoding='utf-8').splitlines(keepends=True)
        diff_result = list(difflib.unified_diff(lines1, lines2, fromfile=f1, tofile=f2, lineterm=''))
        return ''.join(diff_result) or f"文件 '{f1}' 和 '{f2}' 内容完全相同。"
    except Exception as e: return f"比较文件差异时发生错误: {e}"
def _gen_tree(dir_path: Path, prefix: str, current_depth: int, max_depth: int) -> list[str]:
    if max_depth != -1 and current_depth > max_depth: return []
    lines = [];
    try: entries = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
    except PermissionError: return [f"{prefix}└── [无法访问]"]
    except Exception as e: return [f"{prefix}└── [读取错误: {e}]"]
    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1); connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
        if entry.is_dir(): new_prefix = prefix + ("    " if is_last else "│   "); lines.extend(_gen_tree(entry, new_prefix, current_depth + 1, max_depth))
    return lines
def tree(path: str = ".", depth: int = -1) -> str:
    print(f"(tree '{path}' depth={depth})"); target_dir_path_relative = Path(path); target_dir_abs_path = (base_dir / target_dir_path_relative)
    ok, msg = _validate_path(target_dir_abs_path, check_existence=True, expect_dir=True)
    if not ok: return msg
    resolved_target_dir = target_dir_abs_path.resolve()
    if resolved_target_dir == base_dir.resolve(): root_display_name = f"./{base_dir.name}"
    else:
        try: root_display_name = str(resolved_target_dir.relative_to(base_dir.resolve()))
        except ValueError: root_display_name = resolved_target_dir.name # Should not happen due to _validate_path
    output_lines = [f"{root_display_name}/"]
    if depth != 0: output_lines.extend(_gen_tree(resolved_target_dir, "", 1, depth))
    return "\n".join(output_lines)
def find_files(pattern: str, path: str = ".", search_content_regex: Optional[str] = None, case_sensitive: bool = False, recursive: bool = True) -> str:
    print(f"(find_files pattern='{pattern}' path='{path}' content_regex='{search_content_regex}')"); search_root_path = (base_dir / path)
    ok, msg = _validate_path(search_root_path, check_existence=True, expect_dir=True)
    if not ok: return msg
    resolved_search_root = search_root_path.resolve(); glob_func = resolved_search_root.rglob if recursive else resolved_search_root.glob
    try: matched_paths = list(glob_func(pattern))
    except Exception as e: return f"查找文件时发生错误: {e}"
    if not matched_paths: return f"在 '{path}' 目录及其子目录（递归={recursive}）中未找到匹配模式 '{pattern}' 的文件或目录。"
    output_results = []
    if search_content_regex:
        try: regex_flags = 0 if case_sensitive else re.IGNORECASE; compiled_regex = re.compile(search_content_regex, regex_flags)
        except re.error as e: return f"提供的正则表达式 '{search_content_regex}' 无效: {e}"
        for file_path_obj in matched_paths:
            if file_path_obj.is_file(): # Only search content in files
                val_ok, val_msg = _validate_path(file_path_obj, check_existence=True, expect_file=True)
                if not val_ok:
                    output_results.append(f"跳过无效路径 {file_path_obj}: {val_msg}")
                    continue
                try:
                    content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
                    for line_num, line_content in enumerate(content.splitlines()):
                        if compiled_regex.search(line_content):
                            relative_file_path_str = str(file_path_obj.relative_to(base_dir))
                            output_results.append(f"{relative_file_path_str}: 第 {line_num+1} 行: {line_content.strip()}")
                except Exception as e:
                    relative_file_path_str = str(file_path_obj.relative_to(base_dir))
                    output_results.append(f"读取文件 {relative_file_path_str} 内容时出错: {e}")
        return "\n".join(output_results) or f"在匹配模式 '{pattern}' 的文件中未找到包含 '{search_content_regex}' 的内容。"
    else: return "\n".join(str(p.relative_to(base_dir)) for p in matched_paths)
def replace_in_file(name: str, search_regex: str, replace_string: str, count: int = 0) -> str:
    print(f"(replace_in_file '{name}' regex='{search_regex}' replacement='{replace_string}' count={count})"); file_to_modify = base_dir / name
    ok, msg = _validate_path(file_to_modify, check_existence=True, expect_file=True)
    if not ok: return msg
    try:
        original_content = file_to_modify.read_text(encoding='utf-8')
        new_content, num_replacements = re.subn(search_regex, replace_string, original_content, count=count)
        if num_replacements > 0: file_to_modify.write_text(new_content, encoding='utf-8'); return f"在文件 '{name}' 中成功替换了 {num_replacements} 处匹配。"
        else: return f"在文件 '{name}' 中未找到与正则表达式 '{search_regex}' 匹配的内容。"
    except re.error as e: return f"提供的正则表达式 '{search_regex}' 无效: {e}"
    except Exception as e: return f"在文件 '{name}' 中进行替换操作时发生错误：{e}"
def archive_files(archive_name: str, items_to_archive: list[str], archive_format: str = "zip") -> str:
    print(f"(archive_files '{archive_name}' items='{items_to_archive}' format='{archive_format}')"); guessed_format = archive_format.lower()
    if guessed_format == "tar":
        if archive_name.lower().endswith((".tar.gz", ".tgz")): guessed_format = "gztar"
        elif archive_name.lower().endswith((".tar.bz2", ".tbz2")): guessed_format = "bztar"

    final_archive_format = guessed_format; archive_path_full = base_dir / archive_name
    ok_arc_path, msg_arc_path = _validate_path(archive_path_full, check_existence=False)
    if not ok_arc_path: return msg_arc_path
    if archive_path_full.exists(): return f"错误：归档文件 '{archive_name}' 已存在。"

    abs_paths_to_archive = []
    for item_name_str in items_to_archive:
        item_path = base_dir / item_name_str; ok_item, msg_item = _validate_path(item_path, check_existence=True)
        if not ok_item: return f"错误：要归档的项 '{item_name_str}' 无效或不存在：{msg_item}"
        abs_paths_to_archive.append(item_path)
    if not abs_paths_to_archive: return "错误：没有指定任何有效的文件或目录进行归档。"

    valid_formats_map = {"zip": None, "tar": "w", "gztar": "w:gz", "bztar": "w:bz2"}
    if final_archive_format not in valid_formats_map: return f"错误：不支持的归档格式 '{final_archive_format}'。支持的格式: {', '.join(valid_formats_map.keys())}."
    try:
        archive_path_full.parent.mkdir(parents=True, exist_ok=True)
        if final_archive_format == "zip":
            with zipfile.ZipFile(archive_path_full, 'w', zipfile.ZIP_DEFLATED) as zf:
                for item_abs_path in abs_paths_to_archive:
                    arcname_in_zip = item_abs_path.relative_to(base_dir)
                    if item_abs_path.is_file(): zf.write(item_abs_path, arcname_in_zip)
                    elif item_abs_path.is_dir():
                        for root, _, files_in_dir in os.walk(item_abs_path):
                            root_path_obj = Path(root)
                            for file_name_in_dir in files_in_dir:
                                file_to_add_path = root_path_obj / file_name_in_dir
                                ok_f, msg_f = _validate_path(file_to_add_path, check_existence=True, expect_file=True)
                                if not ok_f:
                                    print(f"警告: 跳过归档中的无效文件 {file_to_add_path}: {msg_f}")
                                    continue
                                file_arcname_in_zip = file_to_add_path.relative_to(base_dir)
                                zf.write(file_to_add_path, file_arcname_in_zip)
        else: # tar based formats
            tar_mode = valid_formats_map[final_archive_format]
            with tarfile.open(archive_path_full, tar_mode) as tf:
                for item_abs_path in abs_paths_to_archive:
                    arcname_in_tar = item_abs_path.relative_to(base_dir)
                    tf.add(item_abs_path, arcname=arcname_in_tar)
        return f"成功创建归档 '{archive_name}' (格式: {final_archive_format})。"
    except Exception as e:
        if archive_path_full.exists():
            try: archive_path_full.unlink()
            except: pass
        return f"创建归档 '{archive_name}' 时发生错误：{e}"
def extract_archive(archive_name: str, destination_path: str = ".", specific_members: Optional[list[str]] = None) -> str:
    print(f"(extract_archive '{archive_name}' dest='{destination_path}' members='{specific_members}')"); archive_file_to_extract = base_dir / archive_name
    ok_arc, msg_arc = _validate_path(archive_file_to_extract, check_existence=True, expect_file=True)
    if not ok_arc: return msg_arc

    extraction_dest_dir_relative = Path(destination_path)
    extraction_dest_dir_abs = (base_dir / extraction_dest_dir_relative).resolve()
    
    ok_dest, msg_dest = _validate_path(extraction_dest_dir_abs, check_existence=False, expect_dir=True if extraction_dest_dir_abs.exists() else False)
    if not ok_dest: return msg_dest

    try:
        extraction_dest_dir_abs.mkdir(parents=True, exist_ok=True)
        extracted_count = 0
        actual_extracted_members = []

        if archive_file_to_extract.name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive_file_to_extract, 'r') as zf:
                members_to_extract_from_zip = zf.namelist()
                if specific_members:
                    selected_zip_members = []
                    normalized_zip_member_map = {m.replace("\\", "/"): m for m in members_to_extract_from_zip}
                    for sm_query in specific_members:
                        normalized_sm_query = sm_query.replace("\\", "/")
                        if normalized_sm_query in normalized_zip_member_map:
                            selected_zip_members.append(normalized_zip_member_map[normalized_sm_query])
                        else:
                            dir_sm_query = normalized_sm_query if normalized_sm_query.endswith("/") else normalized_sm_query + "/"
                            found_dir_member = False
                            for zip_m_norm, zip_m_orig in normalized_zip_member_map.items():
                                if zip_m_norm.startswith(dir_sm_query):
                                    selected_zip_members.append(zip_m_orig)
                                    found_dir_member = True
                            if not found_dir_member:
                                print(f"警告：在ZIP归档 '{archive_name}' 中未找到成员或以此为前缀的成员 '{sm_query}'。")
                    members_to_extract_from_zip = list(set(selected_zip_members))
                
                if not members_to_extract_from_zip and specific_members:
                    return f"错误：在ZIP归档中未找到任何指定的成员进行解压。"

                zf.extractall(path=extraction_dest_dir_abs, members=members_to_extract_from_zip if specific_members else None)
                extracted_count = len(members_to_extract_from_zip if specific_members else zf.namelist())
                actual_extracted_members = members_to_extract_from_zip if specific_members else zf.namelist()

        elif tarfile.is_tarfile(archive_file_to_extract):
            with tarfile.open(archive_file_to_extract, 'r:*') as tf:
                tar_members_to_extract_info = []
                all_tar_members_info = tf.getmembers()

                if specific_members:
                    normalized_tar_member_map = {m.name.replace("\\", "/"): m for m in all_tar_members_info}
                    for sm_name_query in specific_members:
                        normalized_sm_query = sm_name_query.replace("\\", "/")
                        if normalized_sm_query in normalized_tar_member_map:
                            tar_members_to_extract_info.append(normalized_tar_member_map[normalized_sm_query])
                        else:
                            dir_sm_query = normalized_sm_query if normalized_sm_query.endswith("/") else normalized_sm_query + "/"
                            found_dir_member = False
                            for tar_m_norm, tar_m_info in normalized_tar_member_map.items():
                                if tar_m_norm.startswith(dir_sm_query):
                                    tar_members_to_extract_info.append(tar_m_info)
                                    found_dir_member = True
                            if not found_dir_member:
                                print(f"警告：在TAR归档 '{archive_name}' 中未找到成员或以此为前缀的成员 '{sm_name_query}'。")
                    tar_members_to_extract_info = list(set(tar_members_to_extract_info))
                else:
                    tar_members_to_extract_info = all_tar_members_info
                
                if not tar_members_to_extract_info and specific_members:
                     return f"错误：在TAR归档中未找到任何指定的成员进行解压。"

                tf.extractall(path=extraction_dest_dir_abs, members=tar_members_to_extract_info if specific_members else None)
                extracted_count = len(tar_members_to_extract_info)
                actual_extracted_members = [m.name for m in tar_members_to_extract_info]
        else:
            return f"错误：无法识别的归档文件格式或文件 '{archive_name}' 已损坏。"

        display_destination_path = str(extraction_dest_dir_abs.relative_to(base_dir)) if extraction_dest_dir_abs.is_relative_to(base_dir) else str(extraction_dest_dir_abs)

        result_msg = f"从 '{archive_name}' 成功解压 {extracted_count} 个成员/文件到 './{display_destination_path}'。"
        if actual_extracted_members:
            result_msg += f"\n解压的成员列表 (部分): {', '.join(actual_extracted_members[:10])}{'...' if len(actual_extracted_members) > 10 else ''}"
        return result_msg
    except Exception as e:
        return f"解压归档 '{archive_name}' 时发生错误：{e}"
def backup_file(name: str, backup_dir_name: str = "backups") -> str:
    print(f"(backup_file '{name}' backup_dir='{backup_dir_name}')"); source_file = base_dir / name
    ok_src, msg_src = _validate_path(source_file, check_existence=True, expect_file=True)
    if not ok_src: return msg_src

    backup_target_dir_relative = Path(backup_dir_name)
    backup_target_dir_abs = (base_dir / backup_target_dir_relative).resolve()
    
    ok_dest_dir, msg_dest_dir = _validate_path(backup_target_dir_abs, check_existence=False)
    if not ok_dest_dir: return msg_dest_dir

    try: backup_target_dir_abs.mkdir(parents=True, exist_ok=True)
    except Exception as e: return f"创建备份目录 '{backup_dir_name}' 失败: {e}"

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{source_file.stem}.{timestamp}{source_file.suffix}.bak"
    destination_backup_file_path = backup_target_dir_abs / backup_filename

    ok_dest_file, msg_dest_file = _validate_path(destination_backup_file_path, check_existence=False)
    if not ok_dest_file: return msg_dest_file
    if destination_backup_file_path.exists(): return f"错误：备份目标文件 '{destination_backup_file_path.name}' 已在 '{backup_dir_name}' 中存在。"

    try:
        shutil.copy2(source_file, destination_backup_file_path)
        relative_backup_path_str = str(destination_backup_file_path.relative_to(base_dir))
        return f"文件 '{name}' 已成功备份到：'{relative_backup_path_str}'"
    except Exception as e: return f"备份文件 '{name}' 时发生错误：{e}"

def get_system_info() -> str:
    print("(get_system_info)")
    import platform
    import socket
    import psutil
    info = {
        "操作系统": platform.system() + " " + platform.release(),
        "主机名": socket.gethostname(),
        "CPU核心数": psutil.cpu_count(),
        "总内存(GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "当前用户": psutil.Process().username()
    }
    return json.dumps(info, ensure_ascii=False, indent=2)

def tavily_search_tool(query: str) -> str:
    """网络搜索工具，使用Tavily API进行实时搜索，包含重试机制"""
    print(f"(tavily_search_tool '{query}')")
    if not tavily_api_key:
        return "错误：未配置TAVILY_API_KEY，无法进行网络搜索。"

    endpoint = "https://api.tavily.com/search"
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {tavily_api_key}'}
    data = {'query': query, 'search_depth': 'basic', 'include_answer': True, 'max_results': 5}

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 每次重试都创建新的客户端实例
            client = create_sync_http_client_with_proxy(None)

            with client:
                response = client.post(endpoint, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                if result.get('results'):
                    formatted_results = f"🔍 搜索查询: {query}\n\n"
                    if result.get('answer'):
                        formatted_results += f"📝 答案摘要:\n{result['answer']}\n\n"
                    formatted_results += "🌐 相关链接:\n"
                    for i, item in enumerate(result['results'][:5], 1):
                        title = item.get('title', '无标题')
                        url = item.get('url', '')
                        content = item.get('content', '')[:200] + '...' if len(item.get('content', '')) > 200 else item.get('content', '')
                        formatted_results += f"{i}. **{title}**\n   🔗 {url}\n   📄 {content}\n\n"
                    return formatted_results
                return f"未找到关于 '{query}' 的搜索结果。"

        except httpx.ConnectError as e:
            if "SSL" in str(e) or "EOF" in str(e):
                logger.warning(f"Tavily搜索SSL连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    return f"网络搜索失败：SSL连接错误。建议检查网络连接。"
            else:
                return f"网络搜索失败：连接错误 - {str(e)}"

        except httpx.TimeoutException as e:
            logger.warning(f"Tavily搜索超时 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return f"网络搜索失败：请求超时。"

        except httpx.HTTPStatusError as e:
            return f"网络搜索失败：HTTP错误 {e.response.status_code}"

        except Exception as e:
            logger.error(f"Tavily搜索发生未知错误: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return f"网络搜索失败：{str(e)}"

    return "网络搜索失败：超过最大重试次数"

# --- 系统提示 (修改后) ---
BASE_SYSTEM_PROMPT = f"""你是 ShellAI，一个经验丰富的程序员助手，使用中文与用户交流。
你的主要任务是协助用户进行文件和目录操作，以及在需要时进行网络搜索。
当前工作目录严格限制在 './{base_dir.name}/'，所有文件操作都将在这个沙箱目录内进行。

可用工具:
- 文件/目录操作 (所有路径参数均相对于 './{base_dir.name}/'):
  `read_file(name: str)`: 读取文件内容。
  `list_files(path: str = ".")`: 列出目录内容。
  `rename_file(name: str, new_name: str)`: 重命名文件或目录。
  `write_file(name: str, content: str, mode: str = 'w')`: 写入文件 (w覆盖, a追加)。
  `create_directory(name: str)`: 创建目录。
  `delete_file(name: str)`: 删除文件 (不能删除目录)。
  `pwd()`: 显示当前AI操作的基础目录。
  `diff_files(f1: str, f2: str)`: 比较两个文件的差异。
  `tree(path: str = ".", depth: int = -1)`: 树状显示目录结构。
  `find_files(pattern: str, path: str = ".", search_content_regex: str = None, case_sensitive: bool = False, recursive: bool = True)`: 查找文件，可选内容搜索。
  `replace_in_file(name: str, search_regex: str, replace_string: str, count: int = 0)`: 文件内正则替换。
  `archive_files(archive_name: str, items_to_archive: list[str], archive_format: str = "zip")`: 归档文件或目录 (支持 zip, tar, tar.gz/tgz, tar.bz2/tbz2)。
  `extract_archive(archive_name: str, destination_path: str = ".", specific_members: list[str] = None)`: 解压归档文件。
  `backup_file(name: str, backup_dir_name: str = "backups")`: 备份文件。
  `get_system_info()`: 获取本机系统信息。
- 网络搜索:
  `tavily_search_tool(query: str)`: 当你需要查找当前知识库之外的信息、实时信息或进行广泛的网络搜索时使用此工具。

# <<< 核心修改区域：用户交互指南 >>>
用户交互指南:
- **首要原则**: 仔细理解用户意图。区分用户是在进行普通对话，还是在下达需要使用工具的明确指令。
- **何时直接回答 (不使用工具)**:
  - 当用户进行问候（如“你好”）、感谢或进行简单的日常对话时，请像一个助手一样用自然语言回复。
  - 当用户询问你的身份、能力或可用工具（如“你是谁”、“你能做什么”、“你有什么工具”）时，请根据本提示中的信息直接回答，不要调用工具。
  - 例如，如果用户问“你有什么工具”，你应该回答：“我可用的工具有文件操作类的（如读写、列出、重命名文件等）和网络搜索类的...”，而不是调用`list_files()`。
- **何时使用工具**:
  - 仅当用户的请求是一个**明确的、可执行的任务**，且该任务与上述某个工具的功能完全匹配时，才调用工具。
  - 例如：“创建一个名为'a.txt'的文件”、“列出当前目录下的所有文件”、“搜索一下今天的天气”。
  - **工具调用格式**: 当你决定使用工具时，你的回复**必须且只能**是一行Python代码，即函数调用本身，例如：`write_file("example.txt", "hello world")`。不要添加任何解释或\`\`\`标记。
- **操作后报告**: 在工具执行后，你会收到结果。请根据该结果向用户报告操作的成功与否。如果失败，请解释原因。
"""

def create_intelligent_agent(proxy_config: Optional[Dict] = None):
    """创建智能体实例"""
    return {
        'proxy_config': proxy_config,
        'tools': {
            'read_file': read_file,
            'list_files': list_files,
            'write_file': write_file,
            'create_directory': create_directory,
            'delete_file': delete_file,
            'pwd': pwd,
            'get_system_info': get_system_info,
            'tavily_search_tool': tavily_search_tool,
            'rename_file': rename_file,
            'diff_files': diff_files,
            'tree': tree,
            'find_files': find_files,
            'replace_in_file': replace_in_file,
            'archive_files': archive_files,
            'extract_archive': extract_archive,
            'backup_file': backup_file
        },
        'system_prompt': BASE_SYSTEM_PROMPT
    }

def _call_deepseek_api(prompt: str, proxy_config: Optional[Dict] = None) -> str:
    """调用DeepSeek API，包含SSL错误处理和重试机制"""
    if not deepseek_api_key:
        # 如果没有API Key，模拟一个对话式的回复
        if "你好" in prompt or "你 好" in prompt:
             return "你好！有什么可以帮助你的吗？"
        return "未配置DEEPSEEK_API_KEY，当前为测试模式。"

    endpoint = "https://api.deepseek.com/v1/chat/completions"
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {deepseek_api_key}'}
    data = {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'stream': False, 'temperature': 0.1, 'max_tokens': 4000}

    proxy_obj = ProxyConfig(**proxy_config) if proxy_config else None

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 每次重试都创建新的客户端实例
            client = create_sync_http_client_with_proxy(proxy_obj)

            with client:
                response = client.post(endpoint, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()

                # 检查响应格式
                if not result.get('choices'):
                    raise Exception(f"API响应缺少choices字段: {result}")

                if not isinstance(result['choices'], list) or len(result['choices']) == 0:
                    raise Exception(f"API响应choices字段格式错误: {result['choices']}")

                first_choice = result['choices'][0]
                if not first_choice.get('message'):
                    raise Exception(f"API响应缺少message字段: {first_choice}")

                message_content = first_choice['message'].get('content')
                if not message_content:
                    raise Exception(f"API响应message内容为空: {first_choice['message']}")

                return message_content

        except httpx.ConnectError as e:
            if "SSL" in str(e) or "EOF" in str(e):
                logger.warning(f"SSL连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    return f"SSL连接失败: {str(e)}。建议检查网络连接或配置代理。"
            else:
                return f"连接错误: {str(e)}"

        except httpx.TimeoutException as e:
            logger.warning(f"请求超时 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return f"请求超时: {str(e)}"

        except httpx.HTTPStatusError as e:
            return f"HTTP错误 {e.response.status_code}: {e.response.text}"

        except Exception as e:
            logger.error(f"调用DeepSeek API时发生未知错误: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            else:
                return f"API调用失败: {str(e)}"
    return "API调用失败: 超过最大重试次数"

def _process_tool_calls(response: str, tools: Dict[str, Any]) -> str:
    """
    【已实现】处理AI响应中可能包含的工具调用。
    解析并执行形如 `function_name(arg1, "arg2", ...)` 的调用。
    """
    response = response.strip()
    # 移除可能的Markdown代码块标记
    if response.startswith("```") and response.endswith("```"):
        response = response.strip("`\n")
        if response.startswith("python"):
            response = response[6:].strip()

    # 使用更健壮的正则表达式来匹配函数调用
    match = re.fullmatch(r"^\s*(\w+)\((.*)\)\s*$", response, re.DOTALL)
    if not match:
        # 如果不匹配工具调用格式，直接返回AI的自然语言响应
        return response

    tool_name = match.group(1)
    args_str = match.group(2)

    if tool_name not in tools:
        # 如果AI幻觉出一个不存在的工具，我们不应该执行它，而是返回原始响应
        logger.warning(f"AI试图调用一个不存在的工具: {tool_name}。返回原始文本。")
        return response

    try:
        # 使用ast.literal_eval安全地解析参数
        # 尝试解析为关键字参数
        parsed_args = ()
        parsed_kwargs = {}
        if args_str.strip(): # 确保参数字符串不为空
            try:
                # 尝试同时解析位置和关键字参数
                # 为了安全，我们用ast.parse来解析一个函数调用表达式
                tree = ast.parse(f"f({args_str})", mode='eval')
                call_node = tree.body
                
                # 解析位置参数
                parsed_args = [ast.literal_eval(arg) for arg in call_node.args]

                # 解析关键字参数
                parsed_kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call_node.keywords}

            except (ValueError, SyntaxError, TypeError) as e:
                 logger.error(f"使用AST解析参数 '{args_str}' 失败: {e}。将作为普通文本处理。")
                 return response # 参数解析失败，返回原始AI响应

        logger.info(f"执行工具调用: {tool_name} with args={parsed_args}, kwargs={parsed_kwargs}")
        tool_function = tools[tool_name]
        result = tool_function(*parsed_args, **parsed_kwargs)
        
        # 对列表结果进行格式化
        if isinstance(result, list):
            return "\n".join(map(str, result)) #确保所有项都是字符串
        return str(result)

    except Exception as e:
        logger.error(f"解析或执行工具 '{tool_name}' 时出错: {e}")
        return f"错误：执行工具 '{tool_name}' 失败。原因: {e}"

def run_agent_with_tools(agent: Dict, message: str) -> str:
    """
    【已修改】运行智能体处理消息。
    移除了硬编码的关键字匹配，让所有请求都由AI模型处理。
    """
    if not agent:
        return "智能体未初始化，请检查配置。"
    try:
        full_prompt = f"{agent['system_prompt']}\n\n用户: {message}\n\n助手: "
        
        # 1. 让AI决定是直接回答还是调用工具
        ai_response = _call_deepseek_api(full_prompt, agent.get('proxy_config'))
        
        # 2. 处理AI的响应，如果响应是工具调用，则执行它；否则直接返回
        final_response = _process_tool_calls(ai_response, agent['tools'])
        
        return final_response

    except Exception as e:
        logger.error(f"智能体处理失败: {e}", exc_info=True)
        return f"智能体处理失败: {str(e)}"

# --- 任务状态查询端点 (简化) ---
# @app.get("/task/{task_id}") ...

# --- FastAPI 路由 ---
@app.get("/health")
async def health_check():
    """健康检查端点"""
    redis_status = "disabled"
    if REDIS_AVAILABLE and redis_pool:
        try:
            redis_client = redis.Redis(connection_pool=redis_pool)
            await redis_client.ping()
            redis_status = "healthy"
        except Exception:
            redis_status = "error"
    
    return {
        "status": "healthy",
        "version": app.version, # 使用app.version
        "features": {
            "redis": redis_status,
            "intelligent_agent": "enabled",
            "file_operations": "enabled",
            "network_search": "enabled" if tavily_api_key else "disabled",
            "ai_api": "enabled" if deepseek_api_key else "disabled"
        },
        "websocket_connections": len(manager.active_connections)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，处理实时通信"""
    channel_id = await manager.connect(websocket)
    try:
        await manager.send_personal_message({
            "type": "connection",
            "data": {"status": "connected", "channel_id": channel_id},
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict) or 'type' not in data:
                await manager.send_personal_message({"type": "error", "data": {"message": "无效的消息格式"}}, channel_id)
                continue

            message_type = data.get('type')
            if message_type == 'chat':
                await handle_chat_message(data, channel_id)
            elif message_type == 'ping':
                await manager.send_personal_message({"type": "pong"}, channel_id)
            else:
                await manager.send_personal_message({"type": "error", "data": {"message": f"不支持的消息类型: {message_type}"}}, channel_id)

    except WebSocketDisconnect:
        logger.info(f"WebSocket {channel_id} 断开连接")
    except Exception as e:
        logger.error(f"WebSocket {channel_id} 错误: {e}")
    finally:
        if channel_id:
            manager.disconnect(channel_id)

async def handle_chat_message(data: dict, channel_id: str):
    """处理聊天消息"""
    try:
        chat_data = data.get('data', {})
        message = chat_data.get('message', '').strip()
        if not message:
            await manager.send_personal_message({"type": "error", "data": {"message": "消息内容不能为空"}}, channel_id)
            return

        await manager.send_personal_message({"type": "status", "data": {"status": "processing"}}, channel_id)

        task_data = {
            "message": message,
            "proxy_config": chat_data.get('proxy_config'),
        }

        agent = create_intelligent_agent(task_data.get('proxy_config'))
        response = run_agent_with_tools(agent, message)

        await manager.send_personal_message({
            "type": "result",
            "data": {"response": response, "success": True},
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}", exc_info=True)
        await manager.send_personal_message({"type": "error", "data": {"message": f"处理失败: {str(e)}"}}, channel_id)

@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def chat(request: ChatRequest) -> ChatResponse:
    """聊天API端点 (兼容性接口)"""
    user_message = request.message
    proxy_config = request.proxyConfig

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    if proxy_config:
        is_valid, error_msg = validate_proxy_config(proxy_config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"代理配置无效: {error_msg}")

    try:
        logger.info(f"HTTP聊天请求: {user_message}")
        proxy_config_dict = proxy_config.model_dump() if proxy_config else None
        agent = create_intelligent_agent(proxy_config_dict)
        response = run_agent_with_tools(agent, user_message)
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"HTTP聊天处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理请求失败: {e}")

@app.post("/test-proxy", responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def test_proxy_endpoint(proxy_config: ProxyConfig):
    """测试代理连接端点"""
    is_valid, error_msg = validate_proxy_config(proxy_config)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"代理配置无效: {error_msg}")
    try:
        success, message = await test_proxy_connection(proxy_config)
        return {"success": success, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理测试失败: {str(e)}")

def main():
    """主函数 - 启动FastAPI服务"""
    logger.info("Chrome Plus V2.0 后端服务启动中...")
    os.makedirs(base_dir, exist_ok=True)
    
    import uvicorn
    from config import settings
    uvicorn.run(
        "__main__:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=(ENVIRONMENT == 'development')
    )

if __name__ == "__main__":
    main()