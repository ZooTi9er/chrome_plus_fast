// Chrome Plus V2.1.1 配置文件
// 用于配置服务器连接地址

const CONFIG = {
    // 服务器配置
    SERVER: {
        // 开发环境：使用localhost
        // 生产环境：可以修改为实际的服务器地址
        HOST: 'localhost',  // 或者 '0.0.0.0', '192.168.1.100' 等
        PORT: 5001,
        
        // 自动构建URL
        get HTTP_URL() {
            return `http://${this.HOST}:${this.PORT}`;
        },
        
        get WS_URL() {
            return `ws://${this.HOST}:${this.PORT}/ws`;
        }
    },
    
    // 通信模式配置
    COMMUNICATION: {
        // 优先使用WebSocket，失败时降级到HTTP
        PREFER_WEBSOCKET: true,
        
        // 重连配置
        RECONNECT: {
            MAX_ATTEMPTS: 5,
            DELAY: 1000,
            BACKOFF_FACTOR: 1.5
        }
    },
    
    // 调试配置
    DEBUG: {
        ENABLED: true,
        LOG_LEVEL: 'info' // 'debug', 'info', 'warn', 'error'
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
}
