// api.js
const API_BASE_URL = 'http://localhost:5001';

async function sendMessageToBackend(message) {
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