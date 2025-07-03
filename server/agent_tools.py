#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体工具模块
集成文件操作工具和AI智能体功能
"""

import os
import json
import datetime
import difflib
import re
import shutil
import zipfile
import tarfile
import platform
import socket
import psutil
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 全局基础目录
base_dir = Path(__file__).parent.resolve() / "test"
os.makedirs(base_dir, exist_ok=True)

# AI API配置
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
tavily_api_key = os.getenv('TAVILY_API_KEY')

# 尝试导入pydantic-ai
try:
    from pydantic_ai import Agent
    from pydantic_ai.models.openai import OpenAIModel
    from pydantic_ai.providers.openai import OpenAIProvider
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PYDANTIC_AI_AVAILABLE = False
    Agent = None
    OpenAIModel = None
    OpenAIProvider = None

# --- 文件操作工具函数 ---
def _validate_path(target_path: Path, check_existence=False, expect_dir=False, expect_file=False):
    """验证路径是否在允许的操作范围内"""
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
        return True, ""
    except Exception as e:
        return False, f"路径验证时发生异常：{e}"

def read_file(name: str) -> str:
    """读取文件内容"""
    print(f"(read_file '{name}')")
    p = base_dir / name
    ok, msg = _validate_path(p, check_existence=True, expect_file=True)
    if not ok: return msg
    try: 
        return p.read_text(encoding='utf-8')
    except Exception as e: 
        return f"读取文件 '{name}' 时发生错误：{e}"

def list_files(path: str = ".") -> list[str]:
    """列出目录内容"""
    print(f"(list_files '{path}')")
    p = (base_dir / path)
    ok, msg = _validate_path(p, check_existence=True, expect_dir=True)
    if not ok: return [msg]
    resolved_p = p.resolve()
    items = []
    for item in sorted(resolved_p.iterdir(), key=lambda x:(x.is_file(), x.name.lower())):
        stat = item.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        if item.is_dir(): 
            items.append(f"{item.name}/ (目录, ---, {mtime})")
        else: 
            items.append(f"{item.name} (文件, {stat.st_size} bytes, {mtime})")
    return items or [f"目录 '{path}' 为空。"]

def write_file(name: str, content: str, mode: str = 'w') -> str:
    """写入文件"""
    print(f"(write_file '{name}' mode='{mode}')")
    p = base_dir / name
    ok, msg = _validate_path(p, check_existence=False)
    if not ok: return msg
    if p.exists() and p.is_dir(): 
        return f"错误：路径 '{name}' 是一个目录，无法写入文件。"
    if mode not in ('w', 'a'): 
        return f"错误：不支持的写入模式 '{mode}'。请使用 'w' 或 'a'。"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode, encoding='utf-8') as f: 
            f.write(content)
        return f"成功向 '{name}' 写入 {len(content.encode('utf-8'))} 字节。"
    except Exception as e: 
        return f"写入文件 '{name}' 时发生错误：{e}"

def create_directory(name: str) -> str:
    """创建目录"""
    print(f"(create_directory '{name}')")
    p = base_dir / name
    ok, msg = _validate_path(p, check_existence=False)
    if not ok: return msg
    if p.exists(): return f"错误：路径 '{name}' 已存在。"
    try: 
        p.mkdir(parents=True, exist_ok=False)
        return f"目录 '{name}' 创建成功。"
    except FileExistsError: 
        return f"错误：路径 '{name}' 已存在。"
    except Exception as e: 
        return f"创建目录 '{name}' 失败：{e}"

def delete_file(name: str) -> str:
    """删除文件"""
    print(f"(delete_file '{name}')")
    p = base_dir / name
    ok, msg = _validate_path(p, check_existence=True, expect_file=True)
    if not ok: return msg
    try: 
        p.unlink()
        return f"文件 '{name}' 删除成功。"
    except Exception as e: 
        return f"删除文件 '{name}' 时发生错误：{e}"

def pwd() -> str:
    """显示当前工作目录"""
    print("(pwd)")
    return f"当前操作目录限制在: './{base_dir.name}/'"

def get_system_info() -> str:
    """获取系统信息"""
    print("(get_system_info)")
    info = {
        "操作系统": platform.system() + " " + platform.release(),
        "主机名": socket.gethostname(),
        "CPU核心数": psutil.cpu_count(),
        "总内存(GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "当前用户": psutil.Process().username()
    }
    return json.dumps(info, ensure_ascii=False, indent=2)

def tavily_search_tool(query: str) -> str:
    """网络搜索工具，使用Tavily API进行实时搜索"""
    print(f"(tavily_search_tool '{query}')")

    if not tavily_api_key:
        return "错误：未配置TAVILY_API_KEY，无法进行网络搜索。请在.env文件中设置TAVILY_API_KEY。"

    try:
        # Tavily API端点
        endpoint = "https://api.tavily.com/search"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {tavily_api_key}'
        }

        data = {
            'query': query,
            'search_depth': 'basic',
            'include_answer': True,
            'include_raw_content': False,
            'max_results': 5,
            'include_domains': [],
            'exclude_domains': []
        }

        with httpx.Client(timeout=httpx.Timeout(30.0)) as client:
            response = client.post(endpoint, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()

            # 格式化搜索结果
            if result.get('results'):
                formatted_results = f"🔍 搜索查询: {query}\n\n"

                # 添加答案摘要（如果有）
                if result.get('answer'):
                    formatted_results += f"📝 答案摘要:\n{result['answer']}\n\n"

                # 添加搜索结果
                formatted_results += "🌐 相关链接:\n"
                for i, item in enumerate(result['results'][:5], 1):
                    title = item.get('title', '无标题')
                    url = item.get('url', '')
                    content = item.get('content', '')[:200] + '...' if len(item.get('content', '')) > 200 else item.get('content', '')

                    formatted_results += f"{i}. **{title}**\n"
                    formatted_results += f"   🔗 {url}\n"
                    if content:
                        formatted_results += f"   📄 {content}\n"
                    formatted_results += "\n"

                return formatted_results
            else:
                return f"未找到关于 '{query}' 的搜索结果。"

    except httpx.HTTPStatusError as e:
        return f"搜索API调用失败: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"网络请求失败: {str(e)}"
    except Exception as e:
        return f"搜索过程中发生错误: {str(e)}"

# 系统提示
BASE_SYSTEM_PROMPT = f"""你是 ShellAI，一个经验丰富的程序员助手，使用中文与用户交流。
你的主要任务是协助用户进行文件和目录操作，以及在需要时进行网络搜索。
当前工作目录严格限制在 './{base_dir.name}/'，所有文件操作都将在这个沙箱目录内进行。

可用工具:
- 文件/目录操作 (所有路径参数均相对于 './{base_dir.name}/'):
  `read_file(name: str)`: 读取文件内容。
  `list_files(path: str = ".")`: 列出目录内容。
  `write_file(name: str, content: str, mode: str = 'w')`: 写入文件 (w覆盖, a追加)。
  `create_directory(name: str)`: 创建目录。
  `delete_file(name: str)`: 删除文件 (不能删除目录)。
  `pwd()`: 显示当前AI操作的基础目录。
  `get_system_info()`: 获取本机系统信息，包括操作系统、主机名、CPU核心数、内存和当前用户。
- 网络搜索:
  `tavily_search_tool(query: str)`: 当你需要查找当前知识库之外的信息、实时信息或进行广泛的网络搜索时使用此工具。例如，查找最新的编程库用法、特定错误代码的解决方案、最新新闻等。

用户交互指南:
- 当用户询问 shell 命令的用法或示例时，请提供清晰的命令示例和解释。
- 当用户要求翻译时 (例如英译中)，请直接进行翻译，这不需要特定工具。
- 当用户询问实时信息、最新新闻、当前事件或你知识库之外的信息时，使用 tavily_search_tool 进行网络搜索。
- 对于所有文件操作请求，请仔细分析用户意图，并选择上述合适的文件/目录操作工具来执行。
- 在调用工具前，请确认路径和参数的正确性。所有路径都应在 './{base_dir.name}/' 沙箱内。
- 操作完成后，向用户报告操作结果。如果操作失败，请解释原因。
"""

def create_http_client_with_proxy(proxy_config: Optional[Dict] = None) -> httpx.AsyncClient:
    """创建带代理配置的HTTP客户端"""
    client_kwargs = {
        'timeout': httpx.Timeout(30.0, connect=10.0),
        'limits': httpx.Limits(max_keepalive_connections=5, max_connections=10),
        'follow_redirects': True,
    }

    if proxy_config and proxy_config.get('enabled') and proxy_config.get('host') and proxy_config.get('port'):
        if proxy_config.get('auth'):
            import urllib.parse
            username = urllib.parse.quote(proxy_config['auth']['username'])
            password = urllib.parse.quote(proxy_config['auth']['password'])
            proxy_url = f"{proxy_config['type']}://{username}:{password}@{proxy_config['host']}:{proxy_config['port']}"
        else:
            proxy_url = f"{proxy_config['type']}://{proxy_config['host']}:{proxy_config['port']}"
        
        client_kwargs['proxy'] = proxy_url

    return httpx.AsyncClient(**client_kwargs)

def create_intelligent_agent(proxy_config: Optional[Dict] = None):
    """创建智能体实例（简化版本）"""
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
            'tavily_search_tool': tavily_search_tool
        },
        'system_prompt': BASE_SYSTEM_PROMPT
    }

def run_agent_with_tools(agent, message: str) -> str:
    """运行智能体处理消息（简化版本）"""
    if not agent:
        return "智能体未初始化，请检查配置。"

    try:
        # 检查是否直接请求搜索
        if any(keyword in message.lower() for keyword in ['搜索', 'search', '查找', '查询', '新闻', 'news']):
            # 如果是搜索请求，直接调用搜索工具
            if 'tavily_search_tool' in agent['tools']:
                search_query = message.replace('搜索', '').replace('查找', '').replace('查询', '').strip()
                if search_query:
                    return agent['tools']['tavily_search_tool'](search_query)

        # 检查是否是文件操作请求
        if any(keyword in message.lower() for keyword in ['列出', 'ls', '目录', '文件']):
            if 'list_files' in agent['tools']:
                result = agent['tools']['list_files']()
                if isinstance(result, list):
                    return '\n'.join(result)
                return result

        if any(keyword in message.lower() for keyword in ['系统信息', '电脑信息', 'system info']):
            if 'get_system_info' in agent['tools']:
                result = agent['tools']['get_system_info']()
                return result

        # 构建完整的提示，包含系统提示和用户消息
        full_prompt = f"{agent['system_prompt']}\n\n用户: {message}\n\n助手: "

        # 调用DeepSeek API
        response = _call_deepseek_api(full_prompt, agent['proxy_config'])

        # 检查是否需要调用工具
        response = _process_tool_calls(response, agent['tools'])

        return response

    except Exception as e:
        return f"智能体处理失败: {str(e)}"

def _call_deepseek_api(prompt: str, proxy_config: Optional[Dict] = None) -> str:
    """调用DeepSeek API"""
    if not deepseek_api_key:
        return "未配置DEEPSEEK_API_KEY，当前为测试模式。"

    endpoint = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {deepseek_api_key}'
    }

    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'stream': False,
        'temperature': 0.7,
        'max_tokens': 4000
    }

    # 配置代理
    if proxy_config and proxy_config.get('enabled'):
        proxy_url = _build_proxy_url(proxy_config)
        client = httpx.Client(
            timeout=httpx.Timeout(60.0),
            proxy=proxy_url
        )
    else:
        client = httpx.Client(timeout=httpx.Timeout(60.0))

    try:
        with client:
            response = client.post(endpoint, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get('choices') and result['choices'][0].get('message'):
                return result['choices'][0]['message']['content']
            else:
                raise Exception("API响应格式异常")

    except Exception as e:
        return f"API调用失败: {str(e)}"

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

def _process_tool_calls(response: str, tools: Dict[str, Any]) -> str:
    """处理工具调用（简化版本）"""
    # 这里可以添加更复杂的工具调用逻辑
    # 目前返回原始响应
    return response
