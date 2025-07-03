#!/usr/bin/env python3
"""
Chrome Plus V2.0 综合测试脚本
测试整个系统的功能完整性和性能表现
"""

import asyncio
import json
import time
import subprocess
import sys
import os
from pathlib import Path

# 添加server目录到Python路径
sys.path.append(str(Path(__file__).parent / "server"))

try:
    from test_v2_architecture import ArchitectureTest
except ImportError:
    print("❌ 无法导入架构测试模块，请确保server/test_v2_architecture.py存在")
    sys.exit(1)

class ChromePlusV2TestSuite:
    """Chrome Plus V2.0 测试套件"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.docker_running = False
    
    def log_test(self, test_name: str, success: bool, message: str, details: dict = None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            for key, value in details.items():
                print(f"    {key}: {value}")
    
    def check_prerequisites(self):
        """检查测试前置条件"""
        print("🔍 检查测试前置条件...")
        
        # 检查Docker
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_test("Docker检查", True, "Docker已安装", 
                            {"version": result.stdout.strip()})
            else:
                self.log_test("Docker检查", False, "Docker未正确安装")
                return False
        except Exception as e:
            self.log_test("Docker检查", False, f"Docker检查失败: {str(e)}")
            return False
        
        # 检查Docker Compose
        try:
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_test("Docker Compose检查", True, "Docker Compose已安装",
                            {"version": result.stdout.strip()})
            else:
                self.log_test("Docker Compose检查", False, "Docker Compose未正确安装")
                return False
        except Exception as e:
            self.log_test("Docker Compose检查", False, f"Docker Compose检查失败: {str(e)}")
            return False
        
        # 检查必要文件
        required_files = [
            "docker-compose.yml",
            "server/Dockerfile",
            "server/main.py",
            "server/tasks.py",
            "websocket-api.js",
            "api.js",
            "chat.js",
            "manifest.json"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log_test("文件检查", False, "缺少必要文件", 
                        {"missing_files": missing_files})
            return False
        else:
            self.log_test("文件检查", True, "所有必要文件存在")
        
        return True
    
    def start_docker_services(self):
        """启动Docker服务"""
        print("🐳 启动Docker服务...")
        
        try:
            # 停止现有服务
            subprocess.run(['docker-compose', 'down'], 
                         capture_output=True, timeout=30)
            
            # 启动服务
            result = subprocess.run(['docker-compose', 'up', '-d', '--build'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.docker_running = True
                self.log_test("Docker服务启动", True, "Docker服务启动成功")
                
                # 等待服务就绪
                print("⏳ 等待服务启动...")
                time.sleep(15)
                
                return True
            else:
                self.log_test("Docker服务启动", False, "Docker服务启动失败",
                            {"stderr": result.stderr})
                return False
                
        except Exception as e:
            self.log_test("Docker服务启动", False, f"Docker服务启动异常: {str(e)}")
            return False
    
    def stop_docker_services(self):
        """停止Docker服务"""
        if self.docker_running:
            print("🛑 停止Docker服务...")
            try:
                subprocess.run(['docker-compose', 'down'], 
                             capture_output=True, timeout=60)
                self.docker_running = False
                print("Docker服务已停止")
            except Exception as e:
                print(f"停止Docker服务失败: {e}")
    
    async def run_architecture_tests(self):
        """运行架构测试"""
        print("🏗️ 运行架构测试...")
        
        try:
            arch_tester = ArchitectureTest()
            await arch_tester.run_all_tests()
            
            # 统计架构测试结果
            arch_passed = sum(1 for result in arch_tester.test_results if result["success"])
            arch_total = len(arch_tester.test_results)
            
            if arch_passed == arch_total:
                self.log_test("架构测试", True, f"所有架构测试通过 ({arch_passed}/{arch_total})")
            else:
                self.log_test("架构测试", False, f"部分架构测试失败 ({arch_passed}/{arch_total})")
            
            # 合并测试结果
            self.test_results.extend(arch_tester.test_results)
            
            return arch_passed == arch_total
            
        except Exception as e:
            self.log_test("架构测试", False, f"架构测试异常: {str(e)}")
            return False
    
    def test_chrome_extension_files(self):
        """测试Chrome扩展文件"""
        print("🔧 测试Chrome扩展文件...")
        
        # 测试manifest.json
        try:
            with open("manifest.json", "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # 检查版本
            if manifest.get("version") == "2.0.0":
                self.log_test("Manifest版本", True, "版本号正确")
            else:
                self.log_test("Manifest版本", False, f"版本号错误: {manifest.get('version')}")
            
            # 检查权限
            permissions = manifest.get("permissions", [])
            required_permissions = ["sidePanel", "storage"]
            missing_permissions = [p for p in required_permissions if p not in permissions]
            
            if not missing_permissions:
                self.log_test("Manifest权限", True, "权限配置正确")
            else:
                self.log_test("Manifest权限", False, "缺少必要权限", 
                            {"missing": missing_permissions})
            
            # 检查主机权限
            host_permissions = manifest.get("host_permissions", [])
            if "ws://localhost:5001/*" in host_permissions:
                self.log_test("WebSocket权限", True, "WebSocket权限配置正确")
            else:
                self.log_test("WebSocket权限", False, "缺少WebSocket权限")
                
        except Exception as e:
            self.log_test("Manifest解析", False, f"Manifest解析失败: {str(e)}")
        
        # 测试JavaScript文件
        js_files = ["websocket-api.js", "api.js", "chat.js"]
        for js_file in js_files:
            try:
                with open(js_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if len(content) > 100:  # 基本的内容检查
                    self.log_test(f"{js_file}文件", True, "文件内容正常",
                                {"size": len(content)})
                else:
                    self.log_test(f"{js_file}文件", False, "文件内容过少")
                    
            except Exception as e:
                self.log_test(f"{js_file}文件", False, f"文件读取失败: {str(e)}")
    
    def test_performance(self):
        """性能测试"""
        print("⚡ 运行性能测试...")
        
        # 测试启动时间
        startup_time = time.time() - self.start_time
        if startup_time < 60:  # 60秒内启动
            self.log_test("启动性能", True, f"启动时间: {startup_time:.2f}秒")
        else:
            self.log_test("启动性能", False, f"启动时间过长: {startup_time:.2f}秒")
        
        # 测试内存使用
        try:
            result = subprocess.run(['docker', 'stats', '--no-stream', '--format', 
                                   'table {{.Container}}\t{{.MemUsage}}'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_test("内存使用", True, "内存使用情况获取成功",
                            {"stats": result.stdout})
            else:
                self.log_test("内存使用", False, "无法获取内存使用情况")
                
        except Exception as e:
            self.log_test("内存使用", False, f"内存测试失败: {str(e)}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        
        print("🚀 Chrome Plus V2.0 综合测试开始")
        print("=" * 60)
        
        try:
            # 1. 检查前置条件
            if not self.check_prerequisites():
                print("\n❌ 前置条件检查失败，终止测试")
                return
            
            # 2. 启动Docker服务
            if not self.start_docker_services():
                print("\n❌ Docker服务启动失败，终止测试")
                return
            
            # 3. 运行架构测试
            await self.run_architecture_tests()
            
            # 4. 测试Chrome扩展文件
            self.test_chrome_extension_files()
            
            # 5. 性能测试
            self.test_performance()
            
        finally:
            # 清理
            self.stop_docker_services()
        
        # 输出测试总结
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Chrome Plus V2.0 测试总结")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if self.start_time:
            total_time = time.time() - self.start_time
            print(f"总耗时: {total_time:.2f}秒")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！Chrome Plus V2.0 升级成功！")
            print("\n📋 下一步操作:")
            print("1. 在Chrome中加载扩展 (chrome://extensions/)")
            print("2. 开启开发者模式")
            print("3. 点击'加载已解压的扩展程序'")
            print("4. 选择项目根目录")
            print("5. 享受Chrome Plus V2.0的新功能！")
        else:
            print(f"\n⚠️ {failed_tests} 个测试失败，请检查系统配置")

async def main():
    """主函数"""
    test_suite = ChromePlusV2TestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
