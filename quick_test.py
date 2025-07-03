#!/usr/bin/env python3
"""
Chrome Plus V2.0 快速验证脚本
快速检查升级是否成功
"""

import json
import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (文件不存在)")
        return False

def check_file_content(file_path, keywords, description):
    """检查文件内容是否包含关键词"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_keywords = []
        for keyword in keywords:
            if keyword not in content:
                missing_keywords.append(keyword)
        
        if not missing_keywords:
            print(f"✅ {description}: 包含所有必要内容")
            return True
        else:
            print(f"❌ {description}: 缺少关键词 {missing_keywords}")
            return False
            
    except Exception as e:
        print(f"❌ {description}: 读取失败 - {str(e)}")
        return False

def check_manifest():
    """检查manifest.json"""
    print("\n📋 检查 manifest.json...")
    
    if not check_file_exists("manifest.json", "Manifest文件"):
        return False
    
    try:
        with open("manifest.json", 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # 检查版本
        version = manifest.get("version", "")
        if version == "2.0.0":
            print(f"✅ 版本号: {version}")
        else:
            print(f"❌ 版本号错误: {version} (应该是 2.0.0)")
            return False
        
        # 检查名称
        name = manifest.get("name", "")
        if "Chrome Plus V2.0" in name:
            print(f"✅ 扩展名称: {name}")
        else:
            print(f"❌ 扩展名称错误: {name}")
            return False
        
        # 检查权限
        permissions = manifest.get("permissions", [])
        required_permissions = ["sidePanel", "storage"]
        missing_permissions = [p for p in required_permissions if p not in permissions]
        
        if not missing_permissions:
            print(f"✅ 基础权限: {permissions}")
        else:
            print(f"❌ 缺少权限: {missing_permissions}")
            return False
        
        # 检查主机权限
        host_permissions = manifest.get("host_permissions", [])
        if "ws://localhost:5001/*" in host_permissions:
            print(f"✅ WebSocket权限: 已配置")
        else:
            print(f"❌ WebSocket权限: 未配置")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Manifest解析失败: {str(e)}")
        return False

def check_frontend_files():
    """检查前端文件"""
    print("\n🌐 检查前端文件...")
    
    results = []
    
    # 检查WebSocket API文件
    results.append(check_file_exists("websocket-api.js", "WebSocket API文件"))
    results.append(check_file_content("websocket-api.js", 
                                    ["WebSocketAPIClient", "connect", "sendChatMessage"], 
                                    "WebSocket API内容"))
    
    # 检查更新的API文件
    results.append(check_file_exists("api.js", "API文件"))
    results.append(check_file_content("api.js", 
                                    ["sendMessageToBackendWS", "checkWebSocketAvailability", "initializeAPIClient"], 
                                    "API文件内容"))
    
    # 检查更新的聊天文件
    results.append(check_file_exists("chat.js", "聊天文件"))
    results.append(check_file_content("chat.js", 
                                    ["initializeChatInterface", "WebSocket", "connection-status"], 
                                    "聊天文件内容"))
    
    # 检查HTML文件
    results.append(check_file_exists("sidepanel.html", "侧边栏HTML文件"))
    results.append(check_file_content("sidepanel.html", 
                                    ["websocket-api.js"], 
                                    "HTML WebSocket引用"))
    
    return all(results)

def check_backend_files():
    """检查后端文件"""
    print("\n🖥️ 检查后端文件...")
    
    results = []
    
    # 检查Docker配置
    results.append(check_file_exists("docker-compose.yml", "Docker Compose文件"))
    results.append(check_file_content("docker-compose.yml", 
                                    ["redis", "backend", "worker", "celery"], 
                                    "Docker Compose内容"))
    
    # 检查Dockerfile
    results.append(check_file_exists("server/Dockerfile", "Dockerfile"))
    
    # 检查主应用文件
    results.append(check_file_exists("server/main.py", "主应用文件"))
    results.append(check_file_content("server/main.py", 
                                    ["WebSocket", "ConnectionManager", "lifespan"], 
                                    "主应用WebSocket内容"))
    
    # 检查任务文件
    results.append(check_file_exists("server/tasks.py", "Celery任务文件"))
    results.append(check_file_content("server/tasks.py", 
                                    ["celery_app", "process_ai_message"], 
                                    "Celery任务内容"))
    
    # 检查依赖文件
    results.append(check_file_exists("server/pyproject.toml", "依赖配置文件"))
    results.append(check_file_content("server/pyproject.toml", 
                                    ["websockets", "celery", "redis"], 
                                    "新依赖包"))
    
    return all(results)

def check_test_files():
    """检查测试文件"""
    print("\n🧪 检查测试文件...")
    
    results = []
    
    # 检查架构测试
    results.append(check_file_exists("server/test_v2_architecture.py", "架构测试文件"))
    
    # 检查综合测试
    results.append(check_file_exists("test_chrome_plus_v2.py", "综合测试文件"))
    
    return all(results)

def check_scripts():
    """检查脚本文件"""
    print("\n📜 检查脚本文件...")
    
    results = []
    
    # 检查Docker启动脚本
    results.append(check_file_exists("scripts/docker-dev.sh", "Docker开发脚本"))
    
    return all(results)

def main():
    """主函数"""
    print("🚀 Chrome Plus V2.0 快速验证")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("manifest.json").exists() and not Path("docker-compose.yml").exists():
        print("❌ 请在Chrome Plus项目根目录运行此脚本")
        sys.exit(1)
    
    # 运行各项检查
    checks = [
        ("Manifest配置", check_manifest),
        ("前端文件", check_frontend_files),
        ("后端文件", check_backend_files),
        ("测试文件", check_test_files),
        ("脚本文件", check_scripts)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {check_name}检查失败: {str(e)}")
            results.append(False)
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 验证总结")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过检查: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 所有检查通过！Chrome Plus V2.0 升级成功！")
        print("\n📋 下一步:")
        print("1. 运行 'python test_chrome_plus_v2.py' 进行完整测试")
        print("2. 或运行 'scripts/docker-dev.sh' 启动开发环境")
        print("3. 在Chrome中加载扩展测试功能")
    else:
        failed = total - passed
        print(f"\n⚠️ {failed} 项检查失败，请检查上述问题")
        print("\n🔧 可能的解决方案:")
        print("1. 确保所有文件都已正确创建")
        print("2. 检查文件内容是否包含必要的代码")
        print("3. 重新运行升级脚本")

if __name__ == "__main__":
    main()
