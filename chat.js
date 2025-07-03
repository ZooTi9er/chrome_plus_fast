// chat.js - Chrome Plus V2.0 聊天界面
// 支持WebSocket实时通信和HTTP降级

// 全局状态
let connectionStatus = {
    mode: 'HTTP',
    connected: false,
    channelId: null
};

document.addEventListener('DOMContentLoaded', async () => {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const settingsButton = document.getElementById('settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const closeModal = document.querySelector('.close');
    const saveSettingsButton = document.getElementById('save-settings');
    const resetSettingsButton = document.getElementById('reset-settings');
    const testConnectionButton = document.getElementById('test-connection');

    // 新增的代理设置相关元素
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const proxyEnabledCheckbox = document.getElementById('proxy-enabled');
    const proxyConfigSection = document.getElementById('proxy-config');
    const proxyAuthEnabledCheckbox = document.getElementById('proxy-auth-enabled');
    const proxyAuthSection = document.getElementById('proxy-auth');
    const testProxyButton = document.getElementById('test-proxy');
    const proxyStatusIndicator = document.getElementById('proxy-status');
    const exportSettingsButton = document.getElementById('export-settings');
    const importSettingsButton = document.getElementById('import-settings');
    const importFileInput = document.getElementById('import-file');
    const proxyPresets = document.getElementById('proxy-presets');

    // 初始化highlight.js
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }

    // 初始化Chrome Plus V2.0
    await initializeChatInterface();

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // 设置模态框事件监听器
    settingsButton.addEventListener('click', function() {
        loadSettings();
        settingsModal.style.display = 'block';
    });

    closeModal.addEventListener('click', function() {
        settingsModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    saveSettingsButton.addEventListener('click', saveSettings);
    resetSettingsButton.addEventListener('click', resetSettings);
    testConnectionButton.addEventListener('click', testConnection);

    // 标签页切换事件
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            switchTab(targetTab);
        });
    });

    // 代理设置事件监听器
    proxyEnabledCheckbox.addEventListener('change', toggleProxyConfig);
    proxyAuthEnabledCheckbox.addEventListener('change', toggleProxyAuth);
    testProxyButton.addEventListener('click', testProxyConnection);
    exportSettingsButton.addEventListener('click', exportSettings);
    importSettingsButton.addEventListener('click', () => importFileInput.click());
    importFileInput.addEventListener('change', importSettings);
    proxyPresets.addEventListener('change', function() {
        applyProxyPreset(this.value);
    });

    // 初始化代理配置状态
    toggleProxyConfig();
    toggleProxyAuth();

    function appendMessage(sender, message) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-wrapper');

        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);

        if (sender === 'llm') {
            // 对于LLM消息，渲染Markdown
            try {
                // 配置marked选项
                marked.setOptions({
                    highlight: function(code, lang) {
                        if (lang && hljs.getLanguage(lang)) {
                            try {
                                return hljs.highlight(code, { language: lang }).value;
                            } catch (err) {}
                        }
                        return hljs.highlightAuto(code).value;
                    },
                    breaks: true, // 支持换行
                    gfm: true     // 支持GitHub风格的Markdown
                });

                messageElement.innerHTML = marked.parse(message);

                // 为代码块添加复制按钮
                addCopyButtonsToCodeBlocks(messageElement);
            } catch (error) {
                console.error('Markdown渲染错误:', error);
                messageElement.textContent = message; // 降级到纯文本
            }

            // 添加整个消息的复制按钮
            const copyButton = document.createElement('button');
            copyButton.className = 'message-copy-button';
            copyButton.innerHTML = '📋';
            copyButton.title = '复制消息';
            copyButton.onclick = () => {
                navigator.clipboard.writeText(message).then(() => {
                    copyButton.innerHTML = '✅';
                    setTimeout(() => {
                        copyButton.innerHTML = '📋';
                    }, 2000);
                });
            };

            messageWrapper.appendChild(messageElement);
            messageWrapper.appendChild(copyButton);
        } else {
            // 用户消息保持纯文本
            messageElement.textContent = message;
            messageWrapper.appendChild(messageElement);
        }

        chatBox.appendChild(messageWrapper);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }

    function addCopyButtonsToCodeBlocks(container) {
        const codeBlocks = container.querySelectorAll('pre code');
        codeBlocks.forEach(codeBlock => {
            const pre = codeBlock.parentElement;
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-button';
            copyButton.textContent = '复制';
            copyButton.onclick = () => {
                navigator.clipboard.writeText(codeBlock.textContent).then(() => {
                    copyButton.textContent = '已复制!';
                    setTimeout(() => {
                        copyButton.textContent = '复制';
                    }, 2000);
                });
            };
            pre.style.position = 'relative';
            pre.appendChild(copyButton);
        });
    }

    // 代理预设应用功能
    function applyProxyPreset(presetValue) {
        const presets = {
            'local-http': {
                type: 'http',
                host: '127.0.0.1',
                port: '8080',
                auth: false
            },
            'local-socks5': {
                type: 'socks5',
                host: '127.0.0.1',
                port: '1080',
                auth: false
            },
            'squid-default': {
                type: 'http',
                host: '127.0.0.1',
                port: '3128',
                auth: false
            }
        };

        if (presetValue && presets[presetValue]) {
            const preset = presets[presetValue];

            // 应用预设配置
            document.getElementById('proxy-type').value = preset.type;
            document.getElementById('proxy-host').value = preset.host;
            document.getElementById('proxy-port').value = preset.port;
            document.getElementById('proxy-auth-enabled').checked = preset.auth;

            // 如果不需要认证，清空认证信息
            if (!preset.auth) {
                document.getElementById('proxy-username').value = '';
                document.getElementById('proxy-password').value = '';
            }

            // 更新代理认证区域显示状态
            toggleProxyAuth();

            // 重置状态指示器
            proxyStatusIndicator.textContent = '';
            proxyStatusIndicator.className = 'status-indicator';
        }
    }

    // 标签页切换函数
    function switchTab(targetTab) {
        // 移除所有活动状态
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabContents.forEach(content => content.classList.remove('active'));

        // 激活目标标签页
        document.querySelector(`[data-tab="${targetTab}"]`).classList.add('active');
        document.getElementById(`${targetTab}-tab`).classList.add('active');
    }

    // 代理配置切换函数
    function toggleProxyConfig() {
        const isEnabled = proxyEnabledCheckbox.checked;
        if (isEnabled) {
            proxyConfigSection.classList.remove('disabled');
        } else {
            proxyConfigSection.classList.add('disabled');
        }
    }

    function toggleProxyAuth() {
        const isEnabled = proxyAuthEnabledCheckbox.checked;
        if (isEnabled) {
            proxyAuthSection.classList.remove('disabled');
        } else {
            proxyAuthSection.classList.add('disabled');
        }
    }

    // 设置管理函数
    function loadSettings() {
        chrome.storage.sync.get([
            'apiEndpoint', 'apiKey', 'modelName',
            'proxyEnabled', 'proxyType', 'proxyHost', 'proxyPort',
            'proxyAuthEnabled', 'proxyUsername', 'proxyPassword'
        ], function(result) {
            // API设置
            document.getElementById('api-endpoint').value = result.apiEndpoint || '';
            document.getElementById('api-key').value = result.apiKey || '';
            document.getElementById('model-name').value = result.modelName || '';

            // 代理设置
            document.getElementById('proxy-enabled').checked = result.proxyEnabled || false;
            document.getElementById('proxy-type').value = result.proxyType || 'http';
            document.getElementById('proxy-host').value = result.proxyHost || '';
            document.getElementById('proxy-port').value = result.proxyPort || '';
            document.getElementById('proxy-auth-enabled').checked = result.proxyAuthEnabled || false;
            document.getElementById('proxy-username').value = result.proxyUsername || '';
            document.getElementById('proxy-password').value = result.proxyPassword || '';

            // 更新UI状态
            toggleProxyConfig();
            toggleProxyAuth();
        });
    }

    function saveSettings() {
        const apiEndpoint = document.getElementById('api-endpoint').value.trim();
        const apiKey = document.getElementById('api-key').value.trim();
        const modelName = document.getElementById('model-name').value.trim();

        // 代理设置
        const proxyEnabled = document.getElementById('proxy-enabled').checked;
        const proxyType = document.getElementById('proxy-type').value;
        const proxyHost = document.getElementById('proxy-host').value.trim();
        const proxyPort = document.getElementById('proxy-port').value.trim();
        const proxyAuthEnabled = document.getElementById('proxy-auth-enabled').checked;
        const proxyUsername = document.getElementById('proxy-username').value.trim();
        const proxyPassword = document.getElementById('proxy-password').value.trim();

        // 验证代理设置
        if (proxyEnabled) {
            if (!proxyHost || !proxyPort) {
                alert('启用代理时，代理地址和端口不能为空！');
                return;
            }
            if (proxyAuthEnabled && (!proxyUsername || !proxyPassword)) {
                alert('启用代理身份验证时，用户名和密码不能为空！');
                return;
            }
        }

        chrome.storage.sync.set({
            apiEndpoint: apiEndpoint,
            apiKey: apiKey,
            modelName: modelName,
            proxyEnabled: proxyEnabled,
            proxyType: proxyType,
            proxyHost: proxyHost,
            proxyPort: proxyPort,
            proxyAuthEnabled: proxyAuthEnabled,
            proxyUsername: proxyUsername,
            proxyPassword: proxyPassword
        }, function() {
            alert('设置已保存！');
            settingsModal.style.display = 'none';
        });
    }

    function resetSettings() {
        if (confirm('确定要重置为默认设置吗？')) {
            chrome.storage.sync.clear(function() {
                // 重置API设置
                document.getElementById('api-endpoint').value = '';
                document.getElementById('api-key').value = '';
                document.getElementById('model-name').value = '';

                // 重置代理设置
                document.getElementById('proxy-enabled').checked = false;
                document.getElementById('proxy-type').value = 'http';
                document.getElementById('proxy-host').value = '';
                document.getElementById('proxy-port').value = '';
                document.getElementById('proxy-auth-enabled').checked = false;
                document.getElementById('proxy-username').value = '';
                document.getElementById('proxy-password').value = '';

                // 更新UI状态
                toggleProxyConfig();
                toggleProxyAuth();

                alert('设置已重置！');
            });
        }
    }

    async function testConnection() {
        const apiEndpoint = document.getElementById('api-endpoint').value.trim();
        const apiKey = document.getElementById('api-key').value.trim();
        const modelName = document.getElementById('model-name').value.trim();

        if (!apiEndpoint || !apiKey) {
            alert('请先填写API端点和API密钥！');
            return;
        }

        const originalText = testConnectionButton.textContent;
        testConnectionButton.textContent = '测试中...';
        testConnectionButton.disabled = true;

        try {
            // 获取代理设置信息用于显示
            const proxyEnabled = document.getElementById('proxy-enabled').checked;
            let proxyInfo = '';

            if (proxyEnabled) {
                const proxyHost = document.getElementById('proxy-host').value.trim();
                const proxyPort = document.getElementById('proxy-port').value.trim();
                const proxyType = document.getElementById('proxy-type').value;

                if (proxyHost && proxyPort) {
                    proxyInfo = `\n代理: ${proxyType.toUpperCase()}://${proxyHost}:${proxyPort}`;
                }
            }

            // 构建完整的API端点
            let endpoint = apiEndpoint;
            if (!endpoint.endsWith('/chat/completions') && !endpoint.endsWith('/v1/chat/completions')) {
                if (endpoint.endsWith('/')) {
                    endpoint = endpoint + 'v1/chat/completions';
                } else {
                    endpoint = endpoint + '/v1/chat/completions';
                }
            }

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: modelName || 'gpt-3.5-turbo',
                    messages: [
                        {
                            role: 'user',
                            content: '你好，这是一个连接测试。'
                        }
                    ],
                    max_tokens: 10
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.choices && data.choices[0]) {
                    alert(`✅ 连接测试成功！API配置正确。${proxyInfo}`);
                } else {
                    alert(`⚠️ 连接成功，但响应格式异常。请检查API兼容性。${proxyInfo}`);
                }
            } else {
                const errorData = await response.json().catch(() => ({}));
                let errorMsg = `❌ 连接失败 (${response.status})`;
                if (errorData.error) {
                    errorMsg += `\n错误信息: ${errorData.error.message || errorData.error}`;
                }
                errorMsg += proxyInfo;
                alert(errorMsg);
            }
        } catch (error) {
            alert(`❌ 连接测试失败: ${error.message}${proxyInfo}`);
        } finally {
            testConnectionButton.textContent = originalText;
            testConnectionButton.disabled = false;
        }
    }

    // 代理连接测试
    async function testProxyConnection() {
        const proxyEnabled = document.getElementById('proxy-enabled').checked;
        const proxyHost = document.getElementById('proxy-host').value.trim();
        const proxyPort = document.getElementById('proxy-port').value.trim();
        const proxyType = document.getElementById('proxy-type').value;
        const proxyAuthEnabled = document.getElementById('proxy-auth-enabled').checked;
        const proxyUsername = document.getElementById('proxy-username').value.trim();
        const proxyPassword = document.getElementById('proxy-password').value.trim();

        if (!proxyEnabled) {
            alert('请先启用代理！');
            return;
        }

        if (!proxyHost || !proxyPort) {
            alert('请先填写代理地址和端口！');
            return;
        }

        if (proxyAuthEnabled && (!proxyUsername || !proxyPassword)) {
            alert('启用认证时，用户名和密码不能为空！');
            return;
        }

        const originalText = testProxyButton.textContent;
        testProxyButton.textContent = '测试中...';
        testProxyButton.disabled = true;
        proxyStatusIndicator.textContent = '测试中...';
        proxyStatusIndicator.className = 'status-indicator testing';

        try {
            // 构建代理配置
            const proxyConfig = {
                enabled: true,
                type: proxyType,
                host: proxyHost,
                port: parseInt(proxyPort),
                auth: proxyAuthEnabled ? {
                    username: proxyUsername,
                    password: proxyPassword
                } : null
            };

            // 调用后端代理测试API
            const response = await fetch('http://127.0.0.1:5001/test-proxy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(proxyConfig)
            });

            const result = await response.json();

            if (response.ok && result.success) {
                proxyStatusIndicator.textContent = '连接成功';
                proxyStatusIndicator.className = 'status-indicator success';
                alert(`✅ 代理连接测试成功！\n${result.message}\n代理信息: ${result.proxy_info}`);
            } else {
                proxyStatusIndicator.textContent = '连接失败';
                proxyStatusIndicator.className = 'status-indicator error';
                const errorMsg = result.message || result.detail || '未知错误';
                alert(`❌ 代理连接测试失败:\n${errorMsg}`);
            }
        } catch (error) {
            proxyStatusIndicator.textContent = '测试失败';
            proxyStatusIndicator.className = 'status-indicator error';
            alert(`❌ 代理测试失败: ${error.message}\n请检查代理配置和网络连接。`);
        } finally {
            testProxyButton.textContent = originalText;
            testProxyButton.disabled = false;
        }
    }

    // 导出设置
    function exportSettings() {
        chrome.storage.sync.get(null, function(settings) {
            const exportData = {
                version: '1.0',
                timestamp: new Date().toISOString(),
                settings: settings
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ai-assistant-settings-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            alert('设置已导出！');
        });
    }

    // 导入设置
    function importSettings(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const importData = JSON.parse(e.target.result);

                if (!importData.settings) {
                    throw new Error('无效的配置文件格式');
                }

                if (confirm('确定要导入这些设置吗？这将覆盖当前的所有设置。')) {
                    chrome.storage.sync.set(importData.settings, function() {
                        loadSettings();
                        alert('设置已导入！');
                    });
                }
            } catch (error) {
                alert(`导入失败: ${error.message}`);
            }
        };

        reader.readAsText(file);
        // 清空文件输入，允许重复导入同一文件
        event.target.value = '';
    }

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            appendMessage('user', message);
            messageInput.value = ''; // Clear input

            // Call the backend API
            const llmResponse = await sendMessageToBackend(message);
            appendMessage('llm', llmResponse);
        }
    }

    // 显示初始欢迎消息
    showWelcomeMessage();
});

/**
 * 初始化聊天界面
 */
async function initializeChatInterface() {
    console.log('初始化Chrome Plus V2.0聊天界面...');

    // 添加连接状态指示器
    addConnectionStatusIndicator();

    // 初始化API客户端
    try {
        await initializeAPIClient();
        updateConnectionStatus();

        // 设置WebSocket事件监听器
        setupWebSocketEventListeners();

        console.log('聊天界面初始化完成');
    } catch (error) {
        console.error('聊天界面初始化失败:', error);
        updateConnectionStatus();
    }
}

/**
 * 添加连接状态指示器
 */
function addConnectionStatusIndicator() {
    const header = document.querySelector('.header');
    if (header && !document.getElementById('connection-status')) {
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'connection-status';
        statusIndicator.className = 'connection-status';
        statusIndicator.innerHTML = `
            <span class="status-dot"></span>
            <span class="status-text">连接中...</span>
            <span class="status-mode"></span>
        `;

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            .connection-status {
                display: flex;
                align-items: center;
                gap: 5px;
                font-size: 12px;
                color: #666;
            }
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #ffa500;
                animation: pulse 2s infinite;
            }
            .status-dot.connected {
                background-color: #4caf50;
                animation: none;
            }
            .status-dot.disconnected {
                background-color: #f44336;
                animation: none;
            }
            .status-mode {
                font-weight: bold;
                color: #2196f3;
            }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        header.appendChild(statusIndicator);
    }
}

/**
 * 更新连接状态显示
 */
function updateConnectionStatus() {
    const statusIndicator = document.getElementById('connection-status');
    if (!statusIndicator) return;

    const statusDot = statusIndicator.querySelector('.status-dot');
    const statusText = statusIndicator.querySelector('.status-text');
    const statusMode = statusIndicator.querySelector('.status-mode');

    const status = getConnectionStatus();
    connectionStatus = {
        mode: status.currentMode,
        connected: status.webSocketAvailable && status.useWebSocket,
        channelId: null
    };

    // 更新WebSocket连接状态
    if (status.currentMode === 'WebSocket') {
        const wsClient = getWebSocketClient();
        if (wsClient) {
            const wsStatus = wsClient.getConnectionStatus();
            connectionStatus.connected = wsStatus.isConnected;
            connectionStatus.channelId = wsStatus.channelId;
        }
    }

    // 更新UI
    if (connectionStatus.connected) {
        statusDot.className = 'status-dot connected';
        statusText.textContent = '已连接';
    } else if (status.currentMode === 'HTTP') {
        statusDot.className = 'status-dot connected';
        statusText.textContent = 'HTTP模式';
    } else {
        statusDot.className = 'status-dot disconnected';
        statusText.textContent = '未连接';
    }

    statusMode.textContent = status.currentMode;
}

/**
 * 设置WebSocket事件监听器
 */
function setupWebSocketEventListeners() {
    const wsClient = getWebSocketClient();
    if (!wsClient) return;

    // 连接状态变化
    wsClient.onConnectionChange = (connected, channelId) => {
        connectionStatus.connected = connected;
        connectionStatus.channelId = channelId;
        updateConnectionStatus();

        if (connected) {
            console.log('WebSocket连接已建立，频道ID:', channelId);
        } else {
            console.log('WebSocket连接已断开');
        }
    };

    // 消息处理
    wsClient.onMessage = (data) => {
        handleWebSocketMessage(data);
    };

    // 错误处理
    wsClient.onError = (error) => {
        console.error('WebSocket错误:', error);
        appendMessage('system', `⚠️ WebSocket连接错误: ${error.message}`);
    };
}

/**
 * 处理WebSocket消息
 */
function handleWebSocketMessage(data) {
    const messageType = data.type;

    switch (messageType) {
        case 'status':
            handleStatusMessage(data);
            break;
        case 'result':
            handleResultMessage(data);
            break;
        case 'error':
            handleErrorMessage(data);
            break;
        case 'pong':
            // 心跳响应，无需处理
            break;
        default:
            console.log('收到未知类型的WebSocket消息:', data);
    }
}

/**
 * 处理状态消息
 */
function handleStatusMessage(data) {
    const status = data.data.status;
    const message = data.data.message;

    if (status === 'processing') {
        appendMessage('system', `🔄 ${message}`);
    } else if (status === 'queued') {
        appendMessage('system', `📋 ${message}`);
    }
}

/**
 * 处理结果消息
 */
function handleResultMessage(data) {
    if (data.success) {
        appendMessage('llm', data.response);
    } else {
        const errorMsg = data.error || '处理失败';
        appendMessage('system', `❌ 错误: ${errorMsg}`);
    }
}

/**
 * 处理错误消息
 */
function handleErrorMessage(data) {
    const errorMsg = data.data?.message || '未知错误';
    appendMessage('system', `❌ ${errorMsg}`);
}

/**
 * 显示欢迎消息
 */
function showWelcomeMessage() {
    const version = connectionStatus.mode === 'WebSocket' ? 'V2.0 (WebSocket)' : 'V2.0 (HTTP)';

    appendMessage('llm', `# 欢迎使用 Chrome Plus ${version}！

你好！我是你的智能助手，现在支持实时通信，可以帮助你：

- 📝 **文件操作**：创建、读取、修改文件
- 🗂️ **目录管理**：浏览、创建、管理目录结构
- 💻 **代码编写**：提供代码示例和解决方案
- 🔍 **问题解答**：回答各种技术问题
- ⚡ **实时响应**：${connectionStatus.mode === 'WebSocket' ? 'WebSocket实时通信' : 'HTTP兼容模式'}

${connectionStatus.connected ? '🟢 连接状态：已连接' : '🟡 连接状态：HTTP模式'}

有什么可以帮助你的吗？`);
}