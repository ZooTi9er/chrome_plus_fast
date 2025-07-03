#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Plus V2.0 - 后端服务
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

# 环境和配置
from dotenv import load_dotenv

# FastAPI和WebSocket
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Redis（简化版本不使用Celery）
import redis.asyncio as redis
# from celery.result import AsyncResult

# 导入任务模块（简化版本不使用Celery）
# from tasks import celery_app, process_ai_message

# 原有的文件操作模块
import datetime
import difflib
import re
import shutil
import zipfile
import tarfile
import httpx

# AI模块 (可选，用于兼容性)
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
    from pydantic_ai.messages import ModelMessage
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    logger.warning("pydantic-ai不可用，将使用简化模式")
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

# --- 环境配置 ---
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# AI API配置
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
if not deepseek_api_key:
    logger.warning("未找到 DEEPSEEK_API_KEY，使用测试模式")

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
    if not redis_pool:
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
        # 初始化Redis连接池
        redis_pool = redis.ConnectionPool.from_url(REDIS_URL)
        redis_client = redis.Redis(connection_pool=redis_pool)

        # 测试Redis连接
        await redis_client.ping()
        logger.info("Redis连接成功")

        # 启动Redis监听器
        redis_task = asyncio.create_task(redis_listener())

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
def create_http_client_with_proxy(proxy_config: Optional[ProxyConfig] = None) -> httpx.AsyncClient:
    """创建带代理配置的HTTP客户端"""

    # 基础配置
    client_kwargs = {
        'timeout': httpx.Timeout(30.0, connect=10.0),  # 30秒总超时，10秒连接超时
        'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10),  # 连接池限制
        'follow_redirects': True,  # 跟随重定向
    }

    if proxy_config and proxy_config.enabled and proxy_config.host and proxy_config.port:
        # 构建代理URL
        if proxy_config.auth:
            # URL编码用户名和密码以处理特殊字符
            import urllib.parse
            username = urllib.parse.quote(proxy_config.auth.username)
            password = urllib.parse.quote(proxy_config.auth.password)
            proxy_url = f"{proxy_config.type}://{username}:{password}@{proxy_config.host}:{proxy_config.port}"
        else:
            proxy_url = f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}"

        print(f"使用代理: {proxy_config.type}://{proxy_config.host}:{proxy_config.port}")

        # 添加代理配置
        client_kwargs['proxy'] = proxy_url

    return httpx.AsyncClient(**client_kwargs)

def create_openai_model_with_proxy(proxy_config: Optional[ProxyConfig] = None):
    """创建带代理配置的OpenAI模型"""
    if not deepseek_api_key or not PYDANTIC_AI_AVAILABLE:
        return None

    try:
        # 创建带代理的HTTP客户端
        http_client = create_http_client_with_proxy(proxy_config)

        # 创建OpenAI Provider with custom http client
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
    try:
        client = create_http_client_with_proxy(proxy_config)

        # 测试连接到一个简单的HTTP服务
        test_url = "https://httpbin.org/ip"
        response = await client.get(test_url, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            return True, f"代理连接成功，IP: {data.get('origin', 'unknown')}"
        else:
            return False, f"代理连接失败，HTTP状态码: {response.status_code}"

    except Exception as e:
        return False, f"代理连接测试失败: {str(e)}"
    finally:
        try:
            await client.aclose()
        except:
            pass

def validate_proxy_config(proxy_config: Optional[ProxyConfig]) -> tuple[bool, str]:
    """验证代理配置"""
    if not proxy_config or not proxy_config.enabled:
        return True, ""

    # 验证必需字段
    if not proxy_config.host or not proxy_config.host.strip():
        return False, "代理地址不能为空"

    if not proxy_config.port or proxy_config.port < 1 or proxy_config.port > 65535:
        return False, "代理端口必须在1-65535之间"

    if proxy_config.type not in ['http', 'https', 'socks5']:
        return False, f"不支持的代理类型: {proxy_config.type}"

    # 验证认证信息
    if proxy_config.auth:
        if not proxy_config.auth.username or not proxy_config.auth.username.strip():
            return False, "代理用户名不能为空"
        if not proxy_config.auth.password or not proxy_config.auth.password.strip():
            return False, "代理密码不能为空"

    return True, ""

# --- 数据模型 ---
class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    type: str  # 'chat', 'status', 'error', 'result'
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
    title="Chrome Plus V2.0 API",
    description="AI助手API，支持WebSocket实时通信、异步任务处理和文件操作",
    version="2.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*", "http://localhost:*"],
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
                # Double check path validity, though glob should be within base_dir
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
    if guessed_format == "tar": # Auto-detect compression for tar based on extension
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
                                # Ensure file_to_add_path is also validated (though os.walk within validated dir is usually safe)
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
                    tf.add(item_abs_path, arcname=arcname_in_tar) # tf.add handles directories recursively
        return f"成功创建归档 '{archive_name}' (格式: {final_archive_format})。"
    except Exception as e:
        if archive_path_full.exists():
            try: archive_path_full.unlink() # Attempt to clean up failed archive
            except: pass
        return f"创建归档 '{archive_name}' 时发生错误：{e}"
def extract_archive(archive_name: str, destination_path: str = ".", specific_members: Optional[list[str]] = None) -> str:
    print(f"(extract_archive '{archive_name}' dest='{destination_path}' members='{specific_members}')"); archive_file_to_extract = base_dir / archive_name
    ok_arc, msg_arc = _validate_path(archive_file_to_extract, check_existence=True, expect_file=True)
    if not ok_arc: return msg_arc

    extraction_dest_dir_relative = Path(destination_path)
    extraction_dest_dir_abs = (base_dir / extraction_dest_dir_relative).resolve()
    
    # Validate destination directory (it might not exist yet, which is fine for mkdir)
    # If it exists, it must be a directory.
    ok_dest, msg_dest = _validate_path(extraction_dest_dir_abs, check_existence=False, expect_dir=True if extraction_dest_dir_abs.exists() else False)
    if not ok_dest: return msg_dest

    try:
        extraction_dest_dir_abs.mkdir(parents=True, exist_ok=True)
        extracted_count = 0
        actual_extracted_members = [] # For reporting

        if archive_file_to_extract.name.lower().endswith(".zip"):
            with zipfile.ZipFile(archive_file_to_extract, 'r') as zf:
                members_to_extract_from_zip = zf.namelist()
                if specific_members:
                    selected_zip_members = []
                    # Normalize member names for comparison (replace \ with /)
                    normalized_zip_member_map = {m.replace("\\", "/"): m for m in members_to_extract_from_zip}
                    for sm_query in specific_members:
                        normalized_sm_query = sm_query.replace("\\", "/")
                        if normalized_sm_query in normalized_zip_member_map:
                            selected_zip_members.append(normalized_zip_member_map[normalized_sm_query])
                        else: # Check if it's a directory prefix
                            dir_sm_query = normalized_sm_query if normalized_sm_query.endswith("/") else normalized_sm_query + "/"
                            found_dir_member = False
                            for zip_m_norm, zip_m_orig in normalized_zip_member_map.items():
                                if zip_m_norm.startswith(dir_sm_query):
                                    selected_zip_members.append(zip_m_orig)
                                    found_dir_member = True
                            if not found_dir_member:
                                print(f"警告：在ZIP归档 '{archive_name}' 中未找到成员或以此为前缀的成员 '{sm_query}'。")
                    members_to_extract_from_zip = list(set(selected_zip_members)) # Remove duplicates
                
                if not members_to_extract_from_zip and specific_members: # If specific were requested but none found
                    return f"错误：在ZIP归档中未找到任何指定的成员进行解压。"

                zf.extractall(path=extraction_dest_dir_abs, members=members_to_extract_from_zip if specific_members else None)
                extracted_count = len(members_to_extract_from_zip if specific_members else zf.namelist())
                actual_extracted_members = members_to_extract_from_zip if specific_members else zf.namelist()

        elif tarfile.is_tarfile(archive_file_to_extract): # Handles .tar, .tar.gz, .tar.bz2 etc.
            with tarfile.open(archive_file_to_extract, 'r:*') as tf: # r:* tries to auto-detect compression
                tar_members_to_extract_info = [] # List of TarInfo objects
                all_tar_members_info = tf.getmembers()

                if specific_members:
                    normalized_tar_member_map = {m.name.replace("\\", "/"): m for m in all_tar_members_info}
                    for sm_name_query in specific_members:
                        normalized_sm_query = sm_name_query.replace("\\", "/")
                        if normalized_sm_query in normalized_tar_member_map:
                            tar_members_to_extract_info.append(normalized_tar_member_map[normalized_sm_query])
                        else: # Check for directory prefix
                            dir_sm_query = normalized_sm_query if normalized_sm_query.endswith("/") else normalized_sm_query + "/"
                            found_dir_member = False
                            for tar_m_norm, tar_m_info in normalized_tar_member_map.items():
                                if tar_m_norm.startswith(dir_sm_query):
                                    tar_members_to_extract_info.append(tar_m_info)
                                    found_dir_member = True
                            if not found_dir_member:
                                print(f"警告：在TAR归档 '{archive_name}' 中未找到成员或以此为前缀的成员 '{sm_name_query}'。")
                    tar_members_to_extract_info = list(set(tar_members_to_extract_info)) # Remove duplicates
                else:
                    tar_members_to_extract_info = all_tar_members_info
                
                if not tar_members_to_extract_info and specific_members:
                     return f"错误：在TAR归档中未找到任何指定的成员进行解压。"

                tf.extractall(path=extraction_dest_dir_abs, members=tar_members_to_extract_info if specific_members else None)
                extracted_count = len(tar_members_to_extract_info)
                actual_extracted_members = [m.name for m in tar_members_to_extract_info]
        else:
            return f"错误：无法识别的归档文件格式或文件 '{archive_name}' 已损坏。"

        # Path for reporting should be relative to base_dir
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
    
    ok_dest_dir, msg_dest_dir = _validate_path(backup_target_dir_abs, check_existence=False) # Dir may not exist
    if not ok_dest_dir: return msg_dest_dir

    try: backup_target_dir_abs.mkdir(parents=True, exist_ok=True)
    except Exception as e: return f"创建备份目录 '{backup_dir_name}' 失败: {e}"

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_filename = f"{source_file.stem}.{timestamp}{source_file.suffix}.bak" # More robust for extensions
    destination_backup_file_path = backup_target_dir_abs / backup_filename

    # Final check for destination file path (should not exist, and be within base_dir)
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

# --- 系统提示 (保持不变) ---
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
  `get_system_info()`: 获取本机系统信息，包括操作系统、主机名、CPU核心数、内存和当前用户。
- 网络搜索:
  `tavily_search_tool(query: str)`: 当你需要查找当前知识库之外的信息、实时信息或进行广泛的网络搜索时使用此工具。例如，查找最新的编程库用法、特定错误代码的解决方案等。

用户交互指南:
- 当用户询问 shell 命令的用法或示例时，请提供清晰的命令示例和解释。
- 当用户要求翻译时 (例如英译中)，请直接进行翻译，这不需要特定工具。
- 对于所有文件操作请求，请仔细分析用户意图，并选择上述合适的文件/目录操作工具来执行。
- 在调用工具前，请确认路径和参数的正确性。所有路径都应在 './{base_dir.name}/' 沙箱内。
- 操作完成后，向用户报告操作结果。如果操作失败，请解释原因。
"""

# --- 任务状态查询端点 ---
# 任务状态查询端点（简化版本不使用Celery）
# @app.get("/task/{task_id}")
# async def get_task_status(task_id: str):
#     """查询任务状态"""
#     return {"message": "简化版本不支持任务状态查询"}

# --- FastAPI 路由 ---

@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查Redis连接
        if redis_pool:
            redis_client = redis.Redis(connection_pool=redis_pool)
            await redis_client.ping()
            redis_status = "healthy"
        else:
            redis_status = "disconnected"

        # 检查Celery Worker（简化版本不使用）
        celery_status = "disabled"

        return {
            "status": "healthy",
            "version": "2.0.0",
            "redis": redis_status,
            "celery": celery_status,
            "websocket_connections": len(manager.active_connections)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

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
                "message": "WebSocket连接已建立"
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
                "message": "正在处理您的请求..."
            },
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

        # 构建任务数据
        task_data = {
            "message": message,
            "channel_id": channel_id,
            "user_id": chat_data.get('user_id'),
            "proxy_config": chat_data.get('proxy_config'),
            "api_config": chat_data.get('api_config')
        }

        # 直接处理任务（简化版本，不使用Celery）
        try:
            from agent_tools import create_intelligent_agent, run_agent_with_tools

            # 创建智能体
            agent = create_intelligent_agent(task_data.get('proxy_config'))

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

            logger.info(f"消息处理完成，频道: {channel_id}")

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            await manager.send_personal_message({
                "type": "error",
                "data": {"message": f"处理失败: {str(e)}"},
                "timestamp": datetime.datetime.now().isoformat()
            }, channel_id)

    except Exception as e:
        logger.error(f"处理聊天消息失败: {e}")
        await manager.send_personal_message({
            "type": "error",
            "data": {"message": f"处理失败: {str(e)}"},
            "timestamp": datetime.datetime.now().isoformat()
        }, channel_id)

@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def chat(request: ChatRequest) -> ChatResponse:
    """
    聊天API端点 (兼容性接口)

    为了向后兼容，保留HTTP接口。建议使用WebSocket接口获得更好的实时体验。
    """
    user_message = request.message
    proxy_config = request.proxyConfig

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # 验证代理配置
    if proxy_config:
        is_valid, error_msg = validate_proxy_config(proxy_config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"代理配置无效: {error_msg}")

    try:
        logger.info(f"HTTP聊天请求: {user_message}")

        # 构建任务数据
        task_data = {
            "message": user_message,
            "channel_id": f"http_{uuid.uuid4()}",  # 为HTTP请求生成临时频道ID
            "proxy_config": proxy_config.model_dump() if proxy_config else None,
            "api_config": None
        }

        # 直接处理任务（简化版本）
        try:
            from agent_tools import create_intelligent_agent, run_agent_with_tools

            # 创建智能体
            agent = create_intelligent_agent(task_data.get('proxy_config'))

            # 处理消息
            response = run_agent_with_tools(agent, user_message)

            return ChatResponse(response=response)

        except Exception as e:
            logger.error(f"处理失败: {e}")
            # 如果处理失败，返回简单的测试响应
            proxy_info = ""
            if proxy_config and proxy_config.enabled:
                proxy_info = f" (代理: {proxy_config.type}://{proxy_config.host}:{proxy_config.port})"

            fallback_response = f"Chrome Plus V2.0 智能体响应：收到消息 '{user_message}'。{proxy_info}\n\n" \
                              f"注意：智能体处理失败，错误: {str(e)}"

            return ChatResponse(response=fallback_response)

    except Exception as e:
        logger.error(f"HTTP聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {e}")

@app.post("/test-proxy", responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def test_proxy_endpoint(proxy_config: ProxyConfig):
    """
    测试代理连接端点

    测试指定的代理配置是否可用。
    """
    try:
        # 验证代理配置
        is_valid, error_msg = validate_proxy_config(proxy_config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"代理配置无效: {error_msg}")

        # 测试代理连接
        success, message = await test_proxy_connection(proxy_config)

        return {
            "success": success,
            "message": message,
            "proxy_info": f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代理测试失败: {str(e)}")

def main():
    """主函数 - 启动FastAPI服务"""
    logger.info("Chrome Plus V2.0 后端服务启动中...")

    # 确保基础目录存在
    if not base_dir.exists():
        logger.info(f"创建沙箱目录: {base_dir}")
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"无法创建基础目录 {base_dir}: {e}")
            exit(1)

    # 启动FastAPI服务
    import uvicorn

    # 根据环境选择配置
    if ENVIRONMENT == 'development':
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=5001,
            log_level="info",
            reload=True,
            reload_dirs=["./"]
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=5001,
            log_level="info"
        )

if __name__ == "__main__":
    if not base_dir.exists():
        print(f"提示：正在创建脚本所需的基础测试目录: {base_dir}")
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"错误：无法创建基础目录 {base_dir}：{e}。程序可能无法正常工作。")
            exit(1) # Exit if base dir cannot be created

    # 启动FastAPI服务
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")
