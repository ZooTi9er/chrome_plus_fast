#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import os
from dotenv import load_dotenv
import datetime
import json
import difflib
import re       # 用于 find_files, replace_in_file
import shutil   # 用于 backup_file
import zipfile  # 用于 archive_files, extract_archive
import tarfile  # 用于 archive_files, extract_archive
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
# from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import ModelMessage

# 加载 .env 中的 API Key
load_dotenv()

# --- 模型配置 ---
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
if not deepseek_api_key:
    print("警告：未找到 DEEPSEEK_API_KEY，使用测试模式")
    # 在没有API密钥时，我们创建一个简单的模拟响应
    model = None
else:
    model = OpenAIModel(
        'deepseek-chat',
        provider=OpenAIProvider(
            base_url='https://api.deepseek.com',
            api_key=deepseek_api_key
        ),
    )

# 全局基础目录
base_dir = Path(__file__).parent.resolve() / "test"
os.makedirs(base_dir, exist_ok=True)

# --- Pydantic 模型定义 ---
class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好，请帮我创建一个文件"
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

# --- FastAPI 应用实例 ---
app = FastAPI(
    title="ShellAI API",
    description="AI助手API，支持文件操作和聊天功能",
    version="1.0.0"
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

# --- Tavily 工具实例化 (暂时禁用) ---
# tavily_api_key = os.getenv("TAVILY_API_KEY")
# if not tavily_api_key:
#     print("警告：未在环境变量中找到 TAVILY_API_KEY。Tavily 搜索功能将不可用。")
#     tavily_tool_instance = None
# else:
#     tavily_tool_instance = tavily_search_tool(api_key=tavily_api_key)
tavily_tool_instance = None

# --- Agent 初始化 ---
agent_tools = [
    read_file, list_files, rename_file, write_file, create_directory,
    delete_file, pwd, diff_files, tree, find_files, replace_in_file, get_system_info,
    archive_files, extract_archive, backup_file,
]
if tavily_tool_instance:
    agent_tools.append(tavily_tool_instance)

if model:
    agent = Agent(
        model=model,
        system_prompt=BASE_SYSTEM_PROMPT,
        tools=agent_tools
    )
else:
    agent = None

# --- FastAPI 路由 ---
@app.post("/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def chat(request: ChatRequest) -> ChatResponse:
    """
    聊天API端点

    接收用户消息并返回AI助手的回复。支持文件操作和各种工具调用。
    """
    user_message = request.message

    if not user_message.strip():
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    # 每次请求都使用新的历史记录，或者根据需要加载和管理历史
    # 这里为了简化，每次请求都从空历史开始，或者可以从文件加载
    # 如果需要会话持久性，需要更复杂的历史管理逻辑
    agent_message_history: list[ModelMessage] = []

    try:
        print(f"接收到用户消息: {user_message}")

        if agent is None:
            # 测试模式：返回简单的回复
            llm_response = f"测试模式回复：你说了 '{user_message}'。请配置 DEEPSEEK_API_KEY 以启用完整功能。"
        else:
            # 正常模式：使用LLM Agent
            # 使用线程池来运行同步代码，避免事件循环冲突
            import asyncio
            import concurrent.futures

            def run_agent_sync():
                return agent.run_sync(user_message, message_history=agent_message_history)

            # 在线程池中运行同步代码
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                resp = await loop.run_in_executor(executor, run_agent_sync)
                llm_response = resp.output

            # 确保LLM响应是UTF-8编码的字符串，避免乱码
            if isinstance(llm_response, bytes):
                llm_response = llm_response.decode('utf-8', errors='replace')
            elif not isinstance(llm_response, str):
                llm_response = str(llm_response)

        print(f"LLM Agent响应: {llm_response}")

        return ChatResponse(response=llm_response)

    except Exception as e:
        print(f"调用LLM Agent时发生错误: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"LLM Agent处理请求失败: {e}")

def main():
    # --- History File Paths ---
    history_dir = Path(__file__).parent.resolve()
    # For human-readable detailed log as per user request
    human_readable_history_md_file = history_dir / ".history.md"
    # For structured detailed log of interactions as per user request
    interaction_log_json_file = history_dir / ".history.json"
    # For pydantic-ai agent's internal message history (sequence of ModelMessage)
    agent_messages_json_file = history_dir / ".agent_messages.json"

    # --- Initialize Human-Readable Markdown History File ---
    if not human_readable_history_md_file.exists():
        human_readable_history_md_file.write_text(f"# ShellAI Command History Log\n\n", encoding='utf-8')

    # --- Load Agent's Message History (list[ModelMessage]) ---
    # agent_message_history: list[ModelMessage] = [] # 移动到chat函数内部或全局管理
    # if agent_messages_json_file.exists() and agent_messages_json_file.stat().st_size > 0:
    #     try:
    #         history_data_from_json = json.loads(agent_messages_json_file.read_text(encoding='utf-8'))
    #         if isinstance(history_data_from_json, list):
    #             for item in history_data_from_json:
    #                 if isinstance(item, dict) and "role" in item and "content" in item:
    #                     try:
    #                         item_content = item.get("content", "") # Default to empty string if content is missing
    #                         if not isinstance(item_content, str):
    #                             item_content = str(item_content) # Ensure content is string
    #                         agent_message_history.append(ModelMessage(role=item["role"], content=item_content))
    #                     except Exception as e:
    #                         print(f"警告：从 {agent_messages_json_file} 加载历史时，转换字典到ModelMessage失败: {item}, 错误: {e}")
    #                 else:
    #                     print(f"警告：从 {agent_messages_json_file} 加载的历史项格式不正确: {item}")
    #         else:
    #             print(f"警告: 历史文件 {agent_messages_json_file} 内容不是一个列表。将使用空历史。")
    #             agent_message_history = [] # Reset if format is incorrect
    #     except json.JSONDecodeError:
    #         print(f"警告: 历史文件 {agent_messages_json_file} 解析失败。将使用空历史。")
    #         agent_message_history = []
    #     except Exception as e:
    #         print(f"加载历史文件 {agent_messages_json_file} 时发生未知错误: {e}。将使用空历史。")
    #         agent_message_history = []
    
    # --- Load Interaction Log (list of interaction dicts for .history.json) ---
    # logged_interactions: list[dict] = [] # 移动到chat函数内部或全局管理
    # if interaction_log_json_file.exists() and interaction_log_json_file.stat().st_size > 0:
    #     try:
    #         loaded_data = json.loads(interaction_log_json_file.read_text(encoding='utf-8'))
    #         if isinstance(loaded_data, list):
    #             logged_interactions = loaded_data
    #         else:
    #             print(f"警告: 交互日志文件 {interaction_log_json_file} 内容不是一个列表。将重新初始化。")
    #             logged_interactions = []
    #     except json.JSONDecodeError:
    #         print(f"警告: 交互日志文件 {interaction_log_json_file} 解析失败。将重新初始化。")
    #         logged_interactions = []
    #     except Exception as e:
    #         print(f"加载交互日志文件 {interaction_log_json_file} 时发生未知错误: {e}。将重新初始化。")
    #         logged_interactions = []

    print(
        "欢迎使用 ShellAI！\n"
        f"所有文件操作都将限定在沙箱目录 './{base_dir.name}/' 中进行。\n"
        "输入 '/mode [chat|designer|coder]' 切换模式。\n"
        "输入 'exit' 或 'quit' 退出程序。\n"
    )
    # current_mode = "chat" # 不再需要

    # 移除命令行交互循环
    # while True:
    #     try:
    #         raw_input_str = input(f"[{current_mode}]> ").strip()
    #         if not raw_input_str:
    #             continue
    #         if raw_input_str.lower() in ("exit", "quit"):
    #             print("正在退出 ShellAI。再见！")
    #             break

    #         if raw_input_str.startswith("/mode"):
    #             parts = raw_input_str.split()
    #             if len(parts) == 2 and parts[1] in ("chat", "designer", "coder"):
    #                 current_mode = parts[1]
    #                 print(f"已切换到 {current_mode} 模式。")
    #             else:
    #                 print("用法：/mode [chat|designer|coder]")
    #             continue

    #         user_prompt_with_mode = f"[当前模式:{current_mode}] {raw_input_str}"
            
    #         resp = agent.run_sync(user_prompt_with_mode, message_history=agent_message_history)
    #         output_message_content = resp.output
    #         print(output_message_content)

    #         # --- Log to Human-Readable Markdown File ---
    #         timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         md_log_entry = f"## Timestamp: {timestamp_str} (Mode: {current_mode})\n\n"
    #         md_log_entry += "## Input\n```bash\n" # bash for syntax highlighting if it's command-like
    #         md_log_entry += f"{raw_input_str}\n```\n\n"
    #         md_log_entry += "## Output\n```\n" # Generic code block for LLM output
    #         md_log_entry += f"{output_message_content}\n```\n\n"
            
    #         with open(human_readable_history_md_file, "a", encoding='utf-8') as f_md:
    #             f_md.write(md_log_entry)

    #         # --- Log to Structured JSON File ---
    #         json_log_entry = {
    #             "timestamp": timestamp_str,
    #             "mode": current_mode,
    #             "input": raw_input_str,
    #             "input_to_llm": user_prompt_with_mode,
    #             "output": output_message_content
    #         }
    #         logged_interactions.append(json_log_entry)
    #         with open(interaction_log_json_file, "w", encoding='utf-8') as f_json_log:
    #             json.dump(logged_interactions, f_json_log, ensure_ascii=False, indent=4)


    #         # --- Update Agent's Message History for next turn & Prepare for JSON Save ---
    #         agent_message_history_for_next_turn: list[ModelMessage] = []
    #         agent_message_history_for_json_save: list[dict] = []
            
    #         messages_to_process = resp.all_messages()

    #         if messages_to_process:
    #             for msg_object in messages_to_process:
    #                 role_to_use = None
    #                 content_to_use = None

    #                 if hasattr(msg_object, 'role') and isinstance(msg_object.role, str):
    #                     if msg_object.role in ["user", "assistant", "tool", "system"]:
    #                         role_to_use = msg_object.role
    #                 if not role_to_use: continue # Skip if no valid role

    #                 # Extract content, ensuring it's a string, with special handling for ToolCallParts
    #                 if isinstance(msg_object, ModelMessage):
    #                     if isinstance(msg_object.content, str):
    #                         content_to_use = msg_object.content
    #                     elif isinstance(msg_object.content, list): # Content is list of Parts
    #                         temp_content_parts = []
    #                         for part_item in msg_object.content: # part_item is a BasePart instance
    #                             if hasattr(part_item, 'text') and isinstance(part_item.text, str):
    #                                 temp_content_parts.append(part_item.text)
    #                             elif hasattr(part_item, 'tool_calls') and isinstance(part_item.tool_calls, list) and part_item.tool_calls:
    #                                 # This part_item is a ToolCallPart, its .tool_calls is a list of ToolCall objects
    #                                 tc_strs = []
    #                                 for tc in part_item.tool_calls: # tc is a ToolCall object
    #                                     # tc.id, tc.name, tc.arguments (which is a JSON string of args)
    #                                     tc_strs.append(f"ToolCall(id='{tc.id}', name='{tc.name}', arguments='{tc.arguments}')")
    #                                 temp_content_parts.append("Tool Calls: " + "; ".join(tc_strs))
    #                             elif isinstance(part_item, str): # Fallback if a raw string is in the parts list
    #                                 temp_content_parts.append(part_item)
    #                             # else: # Optional: log or handle other unrecognised part types
    #                             #     temp_content_parts.append(f"[Unsupported Part: {type(part_item)}]")
    #                         if temp_content_parts:
    #                             content_to_use = "\n".join(temp_content_parts)
    #                         else: # If list is empty or only unhandled parts
    #                             content_to_use = "" # Default to empty string
    #                     else: # Fallback for ModelMessage.content if not str or list
    #                         content_to_use = str(msg_object.content) if msg_object.content is not None else ""
                    
    #                 elif hasattr(msg_object, 'content'): # E.g. SystemMessagePart, ToolMessage (where content is string output)
    #                     if isinstance(msg_object.content, str):
    #                         content_to_use = msg_object.content
    #                     else:
    #                         content_to_use = str(msg_object.content) if msg_object.content is not None else ""
    #                 # Removed 'parts' and 'text' direct access here, as ModelMessage covers them.
    #                 # ToolMessage's content is directly the tool's string output.
                    
    #                 if content_to_use is None: # Ensure content_to_use is always a string
    #                     content_to_use = ""

    #                 # This check was `if role_to_use and content_to_use is not None:`
    #                 # Now content_to_use is initialized or set, so it won't be None.
    #                 # We still need role_to_use.
    #                 try:
    #                     model_msg_for_agent = ModelMessage(role=role_to_use, content=content_to_use)
    #                     agent_message_history_for_next_turn.append(model_msg_for_agent)
    #                     agent_message_history_for_json_save.append({"role": role_to_use, "content": content_to_use})
    #                 except Exception as e:
    #                     print(f"警告：为Agent历史创建 ModelMessage (role: {role_to_use}) 失败: {e}")
            
    #         agent_message_history = agent_message_history_for_next_turn

    #         with open(agent_messages_json_file, "w", encoding='utf-8') as f_agent_hist:
    #             json.dump(agent_message_history_for_json_save, f_agent_hist, ensure_ascii=False, indent=2)

    #     except KeyboardInterrupt:
    #         print("\n捕获到中断信号 (Ctrl+C)，正在退出 ShellAI...")
    #         break
    #     except Exception as e:
    #         print(f"程序运行中发生未捕获的错误：{e}")
    #         import traceback
    #         traceback.print_exc()
    pass # 移除原有的命令行交互逻辑

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
