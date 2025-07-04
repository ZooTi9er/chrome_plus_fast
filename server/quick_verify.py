#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证增强版 main.py 的功能完整性
检查所有必要的函数和配置是否正确集成
"""

import sys
import importlib.util
from pathlib import Path

def check_function_exists(content, func_name):
    """检查函数是否在代码中定义"""
    pattern = f"def {func_name}("
    if pattern in content:
        print(f"  ✅ {func_name}")
        return True
    else:
        print(f"  ❌ {func_name} - 缺失")
        return False

def check_variable_exists(content, var_name):
    """检查变量是否在代码中定义"""
    patterns = [
        f"{var_name} = ",
        f"{var_name}=",
        f"global {var_name}"
    ]
    if any(pattern in content for pattern in patterns):
        print(f"  ✅ {var_name}")
        return True
    else:
        print(f"  ❌ {var_name} - 缺失")
        return False

def main():
    """主验证函数"""
    print("🔍 快速验证增强版 main.py 功能完整性")
    print("=" * 50)

    # 读取 main.py 文件内容
    main_py_path = Path(__file__).parent / "main.py"
    if not main_py_path.exists():
        print("❌ 错误: 未找到 server/main.py 文件")
        sys.exit(1)

    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
        print("✅ main.py 文件读取成功")
    except Exception as e:
        print(f"❌ main.py 文件读取失败: {e}")
        sys.exit(1)
    
    # 检查核心配置
    print("\n📋 检查核心配置...")
    config_checks = [
        ("deepseek_api_key", "DeepSeek API密钥配置"),
        ("tavily_api_key", "Tavily API密钥配置"),
        ("base_dir", "沙箱基础目录"),
        ("app", "FastAPI应用实例"),
        ("manager", "WebSocket连接管理器")
    ]
    
    config_passed = 0
    for var_name, description in config_checks:
        if check_variable_exists(main_content, var_name):
            config_passed += 1

    # 检查文件操作函数
    print("\n📁 检查文件操作函数...")
    file_functions = [
        "read_file",
        "list_files",
        "write_file",
        "create_directory",
        "delete_file",
        "pwd",
        "rename_file",
        "diff_files",
        "tree",
        "find_files",
        "replace_in_file",
        "archive_files",
        "extract_archive",
        "backup_file"
    ]

    file_passed = 0
    for func_name in file_functions:
        if check_function_exists(main_content, func_name):
            file_passed += 1

    # 检查智能体函数
    print("\n🤖 检查智能体函数...")
    agent_functions = [
        "get_system_info",
        "tavily_search_tool",
        "create_intelligent_agent",
        "run_agent_with_tools",
        "_call_deepseek_api",
        "_build_proxy_url",
        "_process_tool_calls"
    ]

    agent_passed = 0
    for func_name in agent_functions:
        if check_function_exists(main_content, func_name):
            agent_passed += 1

    # 检查代理相关函数
    print("\n🌐 检查代理相关函数...")
    proxy_functions = [
        "create_http_client_with_proxy",
        "test_proxy_connection",
        "validate_proxy_config"
    ]

    proxy_passed = 0
    for func_name in proxy_functions:
        if check_function_exists(main_content, func_name):
            proxy_passed += 1
    
    # 检查路由端点
    print("\n🛣️  检查路由端点...")
    expected_routes = ["/health", "/ws", "/chat", "/test-proxy"]

    route_passed = 0
    for route in expected_routes:
        if f'"{route}"' in main_content or f"'{route}'" in main_content:
            print(f"  ✅ {route}")
            route_passed += 1
        else:
            print(f"  ❌ {route} - 缺失")

    # 检查智能体工具集配置
    print("\n🔧 检查智能体工具集配置...")
    expected_tools = [
        'read_file', 'list_files', 'write_file', 'create_directory',
        'delete_file', 'pwd', 'get_system_info', 'tavily_search_tool',
        'rename_file', 'diff_files', 'tree', 'find_files',
        'replace_in_file', 'archive_files', 'extract_archive', 'backup_file'
    ]

    tools_passed = 0
    for tool_name in expected_tools:
        if f"'{tool_name}'" in main_content or f'"{tool_name}"' in main_content:
            print(f"  ✅ {tool_name}")
            tools_passed += 1
        else:
            print(f"  ❌ {tool_name} - 缺失")

    print(f"  📊 工具集完整性: {tools_passed}/{len(expected_tools)}")
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 验证结果汇总:")
    
    total_checks = len(config_checks) + len(file_functions) + len(agent_functions) + len(proxy_functions) + len(expected_routes)
    total_passed = config_passed + file_passed + agent_passed + proxy_passed + route_passed
    
    print(f"  配置检查: {config_passed}/{len(config_checks)}")
    print(f"  文件操作: {file_passed}/{len(file_functions)}")
    print(f"  智能体功能: {agent_passed}/{len(agent_functions)}")
    print(f"  代理功能: {proxy_passed}/{len(proxy_functions)}")
    print(f"  路由端点: {route_passed}/{len(expected_routes)}")
    print(f"  智能体工具: {tools_passed}/{len(expected_tools)}")
    
    print(f"\n总体完整性: {total_passed}/{total_checks} ({total_passed/total_checks*100:.1f}%)")
    
    if total_passed == total_checks and tools_passed == len(expected_tools):
        print("\n🎉 验证通过！增强版 main.py 功能完整，可以正常使用。")
        print("\n🚀 启动命令:")
        print("   python server/main.py")
        print("   或者: ./start-enhanced-server.sh")
        return True
    else:
        print("\n⚠️  验证未完全通过，可能存在功能缺失。")
        print("   请检查上述标记为 ❌ 的项目。")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n验证过程异常: {e}")
        sys.exit(1)
