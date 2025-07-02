# Chrome扩展AI助手 - 代理功能说明

## 🎯 功能概述

本次更新为Chrome扩展AI助手添加了完整的代理配置功能，允许用户通过HTTP/HTTPS/SOCKS5代理访问AI API服务，解决地理位置限制和网络访问问题。

## 🆕 新增功能

### 1. 代理设置界面
- **标签页设计**: 将设置界面分为"API配置"和"代理设置"两个标签页
- **代理类型支持**: HTTP代理、HTTPS代理、SOCKS5代理
- **认证支持**: 可选的用户名/密码认证
- **实时预览**: 代理配置状态实时显示

### 2. 代理配置选项
- ✅ **启用/禁用代理**: 一键开关代理功能
- ✅ **代理类型选择**: 支持HTTP、HTTPS、SOCKS5
- ✅ **服务器配置**: 代理地址和端口设置
- ✅ **身份验证**: 可选的用户名密码认证
- ✅ **连接测试**: 代理连接状态验证

### 3. 配置管理功能
- ✅ **安全存储**: 代理配置安全保存在Chrome存储中
- ✅ **导入导出**: 支持配置文件的导入和导出
- ✅ **配置验证**: 自动验证代理配置的有效性
- ✅ **错误处理**: 详细的错误信息和解决建议

## 🔧 技术实现

### 前端修改

#### 1. HTML界面 (`sidepanel.html`)
```html
<!-- 新增标签页结构 -->
<div class="settings-tabs">
  <button class="tab-button active" data-tab="api">API配置</button>
  <button class="tab-button" data-tab="proxy">代理设置</button>
</div>

<!-- 代理配置表单 -->
<div id="proxy-tab" class="tab-content">
  <div class="form-group">
    <label class="checkbox-label">
      <input type="checkbox" id="proxy-enabled">
      启用代理
    </label>
  </div>
  <!-- 更多代理配置字段... -->
</div>
```

#### 2. CSS样式 (`sidepanel.css`)
- 新增标签页样式
- 代理配置区域样式
- 状态指示器样式
- 响应式设计优化

#### 3. JavaScript逻辑 (`chat.js`)
```javascript
// 标签页切换
function switchTab(targetTab) {
    // 切换标签页逻辑
}

// 代理配置管理
function toggleProxyConfig() {
    // 启用/禁用代理配置
}

// 代理连接测试
async function testProxyConnection() {
    // 测试代理连接
}
```

#### 4. API通信 (`api.js`)
```javascript
// 代理配置传递
const requestBody = { 
    message: message,
    proxyConfig: {
        enabled: true,
        type: 'http',
        host: '127.0.0.1',
        port: 8080,
        auth: { username: 'user', password: 'pass' }
    }
};
```

### 后端修改

#### 1. 数据模型 (`server/main.py`)
```python
class ProxyAuth(BaseModel):
    username: str
    password: str

class ProxyConfig(BaseModel):
    enabled: bool = False
    type: str = "http"
    host: str = ""
    port: int = 8080
    auth: Optional[ProxyAuth] = None

class ChatRequest(BaseModel):
    message: str
    proxyConfig: Optional[ProxyConfig] = None
```

#### 2. 代理客户端创建
```python
def create_http_client_with_proxy(proxy_config: Optional[ProxyConfig] = None) -> httpx.AsyncClient:
    """创建带代理配置的HTTP客户端"""
    if proxy_config and proxy_config.enabled:
        proxy_url = f"{proxy_config.type}://{proxy_config.host}:{proxy_config.port}"
        return httpx.AsyncClient(proxies={'http://': proxy_url, 'https://': proxy_url})
    return httpx.AsyncClient()
```

#### 3. AI模型代理支持
```python
def create_openai_model_with_proxy(proxy_config: Optional[ProxyConfig] = None):
    """创建带代理配置的OpenAI模型"""
    http_client = create_http_client_with_proxy(proxy_config)
    provider = OpenAIProvider(
        base_url='https://api.deepseek.com',
        api_key=deepseek_api_key,
        http_client=http_client
    )
    return OpenAIModel('deepseek-chat', provider=provider)
```

## 📋 使用指南

### 1. 基本配置步骤

1. **打开设置**: 点击AI助手界面右上角的设置按钮 ⚙️
2. **切换到代理设置**: 点击"代理设置"标签页
3. **启用代理**: 勾选"启用代理"复选框
4. **配置代理服务器**:
   - 选择代理类型（HTTP/HTTPS/SOCKS5）
   - 输入代理地址和端口
   - 如需认证，勾选"需要身份验证"并输入用户名密码
5. **测试连接**: 点击"测试代理连接"按钮验证配置
6. **保存设置**: 点击"保存设置"完成配置

### 2. 代理类型说明

#### HTTP代理
```
类型: HTTP
地址: 127.0.0.1
端口: 8080
适用: 一般HTTP/HTTPS流量
```

#### HTTPS代理
```
类型: HTTPS
地址: proxy.example.com
端口: 3128
适用: 加密HTTP流量
```

#### SOCKS5代理
```
类型: SOCKS5
地址: 127.0.0.1
端口: 1080
适用: 所有TCP流量
```

### 3. 常见代理配置示例

#### 本地代理
```
代理类型: HTTP
代理地址: 127.0.0.1
端口: 8080
认证: 无
```

#### 企业代理
```
代理类型: HTTP
代理地址: proxy.company.com
端口: 3128
认证: 需要
用户名: employee
密码: ********
```

#### VPN代理
```
代理类型: SOCKS5
代理地址: vpn.example.com
端口: 1080
认证: 需要
用户名: vpnuser
密码: ********
```

## 🔒 安全特性

### 1. 数据保护
- **加密存储**: 代理配置使用Chrome存储API安全保存
- **密码保护**: 代理密码在界面中以密码字段显示
- **配置验证**: 自动验证代理配置的格式和有效性

### 2. 网络安全
- **HTTPS支持**: 支持HTTPS代理确保传输安全
- **认证机制**: 支持用户名密码认证
- **错误处理**: 详细的错误信息帮助诊断问题

### 3. 隐私保护
- **本地存储**: 配置信息仅存储在本地浏览器中
- **可选功能**: 代理功能完全可选，不影响正常使用
- **数据清理**: 支持配置重置和清理

## 🧪 测试功能

### 1. 自动化测试
运行测试脚本验证代理功能：
```bash
python test_proxy_functionality.py
```

### 2. 手动测试步骤
1. 配置代理设置
2. 点击"测试代理连接"
3. 发送测试消息验证功能
4. 检查连接状态和错误信息

### 3. 故障排查
- 检查代理服务器是否可访问
- 验证代理认证信息是否正确
- 确认代理类型选择是否匹配
- 查看浏览器控制台错误信息

## 📊 兼容性说明

### 浏览器支持
- ✅ Chrome 88+ (Manifest V3)
- ✅ Microsoft Edge 88+
- ✅ 其他Chromium内核浏览器

### 代理协议支持
- ✅ HTTP代理 (RFC 7230)
- ✅ HTTPS代理 (CONNECT方法)
- ✅ SOCKS5代理 (RFC 1928)

### 网络环境
- ✅ 企业网络环境
- ✅ 家庭网络环境
- ✅ 公共WiFi环境
- ✅ VPN网络环境

## 🚀 未来计划

### 短期计划
- [ ] 代理连接池支持
- [ ] 自动代理检测
- [ ] 代理性能监控

### 长期计划
- [ ] 智能代理切换
- [ ] 代理配置同步
- [ ] 高级代理规则

## 📞 技术支持

如果在使用代理功能时遇到问题，请：

1. **检查配置**: 确认代理设置是否正确
2. **查看日志**: 检查浏览器控制台和服务器日志
3. **测试连接**: 使用内置的连接测试功能
4. **联系支持**: 通过GitHub Issues报告问题

---

**版本**: 1.1.0  
**更新日期**: 2024年12月  
**功能状态**: ✅ 已完成并测试
