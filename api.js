// api.js - Chrome Plus V2.0 API客户端
// 支持WebSocket实时通信和HTTP降级

const API_BASE_URL = 'http://localhost:5001';

// 通信模式配置
let USE_WEBSOCKET = true; // 默认使用WebSocket
let WEBSOCKET_AVAILABLE = false;

/**
 * 检查WebSocket是否可用
 */
async function checkWebSocketAvailability() {
    try {
        // 检查健康端点
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            timeout: 5000
        });

        if (response.ok) {
            const data = await response.json();
            WEBSOCKET_AVAILABLE = data.version === '2.0.0';
            console.log('WebSocket可用性检查:', WEBSOCKET_AVAILABLE);
            return WEBSOCKET_AVAILABLE;
        }
    } catch (error) {
        console.log('WebSocket可用性检查失败，将使用HTTP模式:', error.message);
        WEBSOCKET_AVAILABLE = false;
    }

    return false;
}

/**
 * 主要的消息发送函数 - 自动选择最佳通信方式
 */
async function sendMessageToBackend(message) {
    // 检查WebSocket可用性
    if (USE_WEBSOCKET && !WEBSOCKET_AVAILABLE) {
        await checkWebSocketAvailability();
    }

    // 根据可用性选择通信方式
    if (USE_WEBSOCKET && WEBSOCKET_AVAILABLE) {
        try {
            return await sendMessageToBackendWS(message);
        } catch (error) {
            console.warn('WebSocket通信失败，降级到HTTP:', error.message);
            // 降级到HTTP
            return await sendMessageToBackendHTTP(message);
        }
    } else {
        return await sendMessageToBackendHTTP(message);
    }
}

/**
 * HTTP方式发送消息 (原有实现，重命名)
 */
async function sendMessageToBackendHTTP(message) {
    try {
        // 检查是否有自定义配置（包括代理设置）
        const settings = await new Promise((resolve) => {
            chrome.storage.sync.get([
                'apiEndpoint', 'apiKey', 'modelName',
                'proxyEnabled', 'proxyType', 'proxyHost', 'proxyPort',
                'proxyAuthEnabled', 'proxyUsername', 'proxyPassword'
            ], resolve);
        });

        let url, headers, body;

        if (settings.apiEndpoint && settings.apiKey) {
            // 使用自定义配置直接调用API
            // 确保API端点包含完整路径
            let endpoint = settings.apiEndpoint.trim();
            if (!endpoint.endsWith('/chat/completions') && !endpoint.endsWith('/v1/chat/completions')) {
                // 如果端点不包含路径，添加标准的OpenAI路径
                if (endpoint.endsWith('/')) {
                    endpoint = endpoint + 'v1/chat/completions';
                } else {
                    endpoint = endpoint + '/v1/chat/completions';
                }
            }

            url = endpoint;
            headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${settings.apiKey}`
            };
            body = JSON.stringify({
                model: settings.modelName || 'gpt-3.5-turbo',
                messages: [
                    {
                        role: 'user',
                        content: message
                    }
                ],
                stream: false
            });
        } else {
            // 使用默认的后端服务
            url = `${API_BASE_URL}/chat`;
            headers = {
                'Content-Type': 'application/json; charset=utf-8'
            };

            // 如果启用了代理，将代理信息传递给后端
            const requestBody = { message: message };
            if (settings.proxyEnabled && settings.proxyHost && settings.proxyPort) {
                requestBody.proxyConfig = {
                    enabled: true,
                    type: settings.proxyType,
                    host: settings.proxyHost,
                    port: parseInt(settings.proxyPort),
                    auth: settings.proxyAuthEnabled ? {
                        username: settings.proxyUsername,
                        password: settings.proxyPassword
                    } : null
                };
            }

            body = JSON.stringify(requestBody);
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: body
        });

        if (!response.ok) {
            let errorDetail = response.statusText;
            try {
                // Try to read as JSON first
                const errorData = await response.json();
                if (errorData.error) {
                    if (typeof errorData.error === 'string') {
                        errorDetail = errorData.error;
                    } else if (errorData.error.message) {
                        errorDetail = errorData.error.message;
                    }
                } else if (errorData.message) {
                    errorDetail = errorData.message;
                }
            } catch (jsonError) {
                // If JSON parsing fails, we can't read the response again
                // So just use the status text
                errorDetail = `${response.statusText} (Status: ${response.status})`;
            }

            // 提供更友好的错误信息
            if (response.status === 404) {
                errorDetail = `API端点不存在 (404)。请检查API端点是否正确。当前请求URL: ${url}`;
            } else if (response.status === 401) {
                errorDetail = `API密钥无效 (401)。请检查API密钥是否正确。`;
            } else if (response.status === 403) {
                errorDetail = `访问被拒绝 (403)。请检查API密钥权限。`;
            }

            throw new Error(`HTTP error! status: ${response.status}, message: ${errorDetail}`);
        }

        try {
            const data = await response.json();

            // 处理不同API的响应格式
            if (settings.apiEndpoint && settings.apiKey) {
                // OpenAI格式的响应
                if (data.choices && data.choices[0] && data.choices[0].message) {
                    return data.choices[0].message.content;
                } else if (data.error) {
                    throw new Error(data.error.message || 'API Error');
                } else {
                    return 'No response received from API';
                }
            } else {
                // 默认后端格式
                return data.response || 'No response received';
            }
        } catch (jsonParseError) {
            console.error('Error parsing JSON response:', jsonParseError);
            return `Error: Invalid JSON response from server. Details: ${jsonParseError.message}`;
        }
    } catch (error) {
        console.error('Error sending message to backend:', error);
        return `Error: ${error.message}`;
    }
}

// 代理配置验证函数
function validateProxyConfig(proxyConfig) {
    if (!proxyConfig || !proxyConfig.enabled) {
        return { valid: true };
    }

    const errors = [];

    if (!proxyConfig.host || !proxyConfig.host.trim()) {
        errors.push('代理地址不能为空');
    }

    if (!proxyConfig.port || proxyConfig.port < 1 || proxyConfig.port > 65535) {
        errors.push('代理端口必须在1-65535之间');
    }

    if (!['http', 'https', 'socks5'].includes(proxyConfig.type)) {
        errors.push('不支持的代理类型');
    }

    if (proxyConfig.auth) {
        if (!proxyConfig.auth.username || !proxyConfig.auth.username.trim()) {
            errors.push('代理用户名不能为空');
        }
        if (!proxyConfig.auth.password || !proxyConfig.auth.password.trim()) {
            errors.push('代理密码不能为空');
        }
    }

    return {
        valid: errors.length === 0,
        errors: errors
    };
}

// 获取代理配置的显示信息
function getProxyDisplayInfo(settings) {
    if (!settings.proxyEnabled) {
        return '未启用代理';
    }

    const authInfo = settings.proxyAuthEnabled ? ' (需要认证)' : '';
    return `${settings.proxyType.toUpperCase()}代理: ${settings.proxyHost}:${settings.proxyPort}${authInfo}`;
}

// 测试API连接（包括代理）
async function testAPIConnection(settings) {
    try {
        const testMessage = '测试连接';
        const response = await sendMessageToBackend(testMessage);

        if (response && !response.startsWith('Error:')) {
            return {
                success: true,
                message: '连接测试成功',
                proxyInfo: getProxyDisplayInfo(settings)
            };
        } else {
            return {
                success: false,
                message: response || '连接测试失败',
                proxyInfo: getProxyDisplayInfo(settings)
            };
        }
    } catch (error) {
        return {
            success: false,
            message: `连接测试失败: ${error.message}`,
            proxyInfo: getProxyDisplayInfo(settings)
        };
    }
}

/**
 * 设置通信模式
 */
function setWebSocketMode(enabled) {
    USE_WEBSOCKET = enabled;
    console.log('通信模式设置为:', enabled ? 'WebSocket' : 'HTTP');
}

/**
 * 获取通信状态
 */
function getConnectionStatus() {
    return {
        useWebSocket: USE_WEBSOCKET,
        webSocketAvailable: WEBSOCKET_AVAILABLE,
        currentMode: (USE_WEBSOCKET && WEBSOCKET_AVAILABLE) ? 'WebSocket' : 'HTTP'
    };
}

/**
 * 初始化API客户端
 */
async function initializeAPIClient() {
    console.log('初始化Chrome Plus V2.0 API客户端...');

    // 检查WebSocket可用性
    await checkWebSocketAvailability();

    // 如果WebSocket可用，预连接
    if (USE_WEBSOCKET && WEBSOCKET_AVAILABLE) {
        try {
            await initializeWebSocket();
            console.log('WebSocket预连接成功');
        } catch (error) {
            console.warn('WebSocket预连接失败，将在需要时重试:', error.message);
        }
    }

    console.log('API客户端初始化完成，当前模式:', getConnectionStatus().currentMode);
}

/**
 * 测试连接 (支持WebSocket和HTTP)
 */
async function testConnection(settings) {
    try {
        const status = getConnectionStatus();
        console.log('测试连接，当前模式:', status.currentMode);

        if (status.currentMode === 'WebSocket') {
            // 测试WebSocket连接
            try {
                const client = getWebSocketClient();
                if (!client.isConnected) {
                    await client.connect();
                }

                // 发送测试消息
                const testResponse = await sendMessageToBackendWS('连接测试');

                return {
                    success: true,
                    message: 'WebSocket连接测试成功',
                    mode: 'WebSocket',
                    response: testResponse.substring(0, 100) + (testResponse.length > 100 ? '...' : '')
                };
            } catch (error) {
                console.warn('WebSocket测试失败，尝试HTTP:', error.message);
                // 降级到HTTP测试
            }
        }

        // HTTP连接测试
        const httpResult = await testAPIConnection(settings);
        return {
            ...httpResult,
            mode: 'HTTP'
        };

    } catch (error) {
        return {
            success: false,
            message: `连接测试失败: ${error.message}`,
            mode: 'Unknown'
        };
    }
}

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sendMessageToBackend,
        sendMessageToBackendHTTP,
        testAPIConnection,
        testConnection,
        getProxyDisplayInfo,
        setWebSocketMode,
        getConnectionStatus,
        initializeAPIClient
    };
}