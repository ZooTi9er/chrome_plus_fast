// websocket-api.js
// Chrome Plus V2.0 WebSocket API客户端

class WebSocketAPIClient {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.channelId = null;
        this.messageHandlers = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1秒
        this.heartbeatInterval = null;
        this.heartbeatTimeout = 30000; // 30秒
        
        // 事件监听器
        this.onConnectionChange = null;
        this.onMessage = null;
        this.onError = null;
    }

    /**
     * 连接到WebSocket服务器
     */
    async connect() {
        if (this.isConnected) {
            console.log('WebSocket已连接');
            return true;
        }

        try {
            const wsUrl = 'ws://localhost:5001/ws';
            console.log('正在连接WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            return new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('WebSocket连接超时'));
                }, 10000);

                this.ws.onopen = () => {
                    clearTimeout(timeout);
                    console.log('WebSocket连接已建立');
                    this.reconnectAttempts = 0;
                    this.startHeartbeat();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        this.handleMessage(data);
                        
                        // 处理连接确认消息
                        if (data.type === 'connection' && data.data.status === 'connected') {
                            this.isConnected = true;
                            this.channelId = data.data.channel_id;
                            console.log('WebSocket连接确认，频道ID:', this.channelId);
                            
                            if (this.onConnectionChange) {
                                this.onConnectionChange(true, this.channelId);
                            }
                            
                            clearTimeout(timeout);
                            resolve(true);
                        }
                    } catch (error) {
                        console.error('解析WebSocket消息失败:', error);
                    }
                };

                this.ws.onclose = (event) => {
                    clearTimeout(timeout);
                    this.handleDisconnection(event);
                    
                    if (!this.isConnected) {
                        reject(new Error(`WebSocket连接失败: ${event.code} ${event.reason}`));
                    }
                };

                this.ws.onerror = (error) => {
                    clearTimeout(timeout);
                    console.error('WebSocket错误:', error);
                    
                    if (this.onError) {
                        this.onError(error);
                    }
                    
                    reject(error);
                };
            });
        } catch (error) {
            console.error('WebSocket连接异常:', error);
            throw error;
        }
    }

    /**
     * 断开WebSocket连接
     */
    disconnect() {
        if (this.ws) {
            this.isConnected = false;
            this.stopHeartbeat();
            this.ws.close(1000, '主动断开连接');
            this.ws = null;
            this.channelId = null;
            
            if (this.onConnectionChange) {
                this.onConnectionChange(false, null);
            }
        }
    }

    /**
     * 处理消息
     */
    handleMessage(data) {
        console.log('收到WebSocket消息:', data);
        
        const messageType = data.type;
        
        // 调用注册的消息处理器
        if (this.messageHandlers.has(messageType)) {
            const handler = this.messageHandlers.get(messageType);
            try {
                handler(data);
            } catch (error) {
                console.error(`处理${messageType}消息失败:`, error);
            }
        }
        
        // 调用通用消息处理器
        if (this.onMessage) {
            this.onMessage(data);
        }
    }

    /**
     * 处理断开连接
     */
    handleDisconnection(event) {
        console.log('WebSocket连接断开:', event.code, event.reason);
        
        this.isConnected = false;
        this.stopHeartbeat();
        
        if (this.onConnectionChange) {
            this.onConnectionChange(false, null);
        }
        
        // 自动重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连...`);
            
            setTimeout(() => {
                this.connect().catch(error => {
                    console.error('重连失败:', error);
                });
            }, delay);
        } else {
            console.error('达到最大重连次数，停止重连');
        }
    }

    /**
     * 发送消息
     */
    async sendMessage(type, data) {
        if (!this.isConnected || !this.ws) {
            throw new Error('WebSocket未连接');
        }

        const message = {
            type: type,
            data: data,
            timestamp: new Date().toISOString()
        };

        try {
            this.ws.send(JSON.stringify(message));
            console.log('发送WebSocket消息:', message);
        } catch (error) {
            console.error('发送WebSocket消息失败:', error);
            throw error;
        }
    }

    /**
     * 发送聊天消息
     */
    async sendChatMessage(message, options = {}) {
        const chatData = {
            message: message,
            user_id: options.userId || 'chrome_extension_user',
            proxy_config: options.proxyConfig || null,
            api_config: options.apiConfig || null
        };

        await this.sendMessage('chat', chatData);
    }

    /**
     * 注册消息处理器
     */
    onMessageType(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    /**
     * 移除消息处理器
     */
    offMessageType(type) {
        this.messageHandlers.delete(type);
    }

    /**
     * 开始心跳
     */
    startHeartbeat() {
        this.stopHeartbeat();
        
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected && this.ws) {
                this.sendMessage('ping', { timestamp: Date.now() }).catch(error => {
                    console.error('发送心跳失败:', error);
                });
            }
        }, this.heartbeatTimeout);
    }

    /**
     * 停止心跳
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * 获取连接状态
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            channelId: this.channelId,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// 全局WebSocket客户端实例
let wsClient = null;

/**
 * 获取WebSocket客户端实例
 */
function getWebSocketClient() {
    if (!wsClient) {
        wsClient = new WebSocketAPIClient();
    }
    return wsClient;
}

/**
 * 初始化WebSocket连接
 */
async function initializeWebSocket() {
    const client = getWebSocketClient();
    
    if (!client.isConnected) {
        try {
            await client.connect();
            return true;
        } catch (error) {
            console.error('WebSocket初始化失败:', error);
            return false;
        }
    }
    
    return true;
}

/**
 * 发送消息到后端 (WebSocket版本)
 */
async function sendMessageToBackendWS(message) {
    try {
        // 获取用户设置
        const settings = await new Promise((resolve) => {
            chrome.storage.sync.get([
                'apiEndpoint', 'apiKey', 'modelName',
                'proxyEnabled', 'proxyType', 'proxyHost', 'proxyPort',
                'proxyAuthEnabled', 'proxyUsername', 'proxyPassword'
            ], resolve);
        });

        // 初始化WebSocket连接
        const connected = await initializeWebSocket();
        if (!connected) {
            throw new Error('无法建立WebSocket连接');
        }

        const client = getWebSocketClient();
        
        // 构建配置
        const options = {};
        
        // 代理配置
        if (settings.proxyEnabled && settings.proxyHost && settings.proxyPort) {
            options.proxyConfig = {
                enabled: true,
                type: settings.proxyType || 'http',
                host: settings.proxyHost,
                port: parseInt(settings.proxyPort),
                auth: settings.proxyAuthEnabled ? {
                    username: settings.proxyUsername,
                    password: settings.proxyPassword
                } : null
            };
        }

        // API配置
        if (settings.apiEndpoint && settings.apiKey) {
            options.apiConfig = {
                endpoint: settings.apiEndpoint,
                api_key: settings.apiKey,
                model: settings.modelName || 'gpt-3.5-turbo'
            };
        }

        // 发送聊天消息
        await client.sendChatMessage(message, options);
        
        // 返回Promise，等待响应
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('消息处理超时'));
            }, 60000); // 60秒超时

            // 监听结果消息
            const handleResult = (data) => {
                if (data.type === 'result') {
                    clearTimeout(timeout);
                    client.offMessageType('result');
                    client.offMessageType('error');
                    
                    if (data.success) {
                        resolve(data.response);
                    } else {
                        reject(new Error(data.error || '处理失败'));
                    }
                } else if (data.type === 'error') {
                    clearTimeout(timeout);
                    client.offMessageType('result');
                    client.offMessageType('error');
                    
                    const errorMsg = data.data?.message || '未知错误';
                    reject(new Error(errorMsg));
                }
            };

            client.onMessageType('result', handleResult);
            client.onMessageType('error', handleResult);
        });

    } catch (error) {
        console.error('WebSocket发送消息失败:', error);
        throw error;
    }
}
