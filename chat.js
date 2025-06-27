// chat.js
document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const settingsButton = document.getElementById('settings-button');
    const settingsModal = document.getElementById('settings-modal');
    const closeModal = document.querySelector('.close');
    const saveSettingsButton = document.getElementById('save-settings');
    const resetSettingsButton = document.getElementById('reset-settings');
    const testConnectionButton = document.getElementById('test-connection');

    // 初始化highlight.js
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }

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

    // 设置管理函数
    function loadSettings() {
        chrome.storage.sync.get(['apiEndpoint', 'apiKey', 'modelName'], function(result) {
            document.getElementById('api-endpoint').value = result.apiEndpoint || '';
            document.getElementById('api-key').value = result.apiKey || '';
            document.getElementById('model-name').value = result.modelName || '';
        });
    }

    function saveSettings() {
        const apiEndpoint = document.getElementById('api-endpoint').value.trim();
        const apiKey = document.getElementById('api-key').value.trim();
        const modelName = document.getElementById('model-name').value.trim();

        chrome.storage.sync.set({
            apiEndpoint: apiEndpoint,
            apiKey: apiKey,
            modelName: modelName
        }, function() {
            alert('设置已保存！');
            settingsModal.style.display = 'none';
        });
    }

    function resetSettings() {
        if (confirm('确定要重置为默认设置吗？')) {
            chrome.storage.sync.clear(function() {
                document.getElementById('api-endpoint').value = '';
                document.getElementById('api-key').value = '';
                document.getElementById('model-name').value = '';
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
                    alert('✅ 连接测试成功！API配置正确。');
                } else {
                    alert('⚠️ 连接成功，但响应格式异常。请检查API兼容性。');
                }
            } else {
                const errorData = await response.json().catch(() => ({}));
                let errorMsg = `❌ 连接失败 (${response.status})`;
                if (errorData.error) {
                    errorMsg += `\n错误信息: ${errorData.error.message || errorData.error}`;
                }
                alert(errorMsg);
            }
        } catch (error) {
            alert(`❌ 连接测试失败: ${error.message}`);
        } finally {
            testConnectionButton.textContent = originalText;
            testConnectionButton.disabled = false;
        }
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

    // Initial message or welcome
    appendMessage('llm', `# 欢迎使用 LLM 助手！

你好！我是你的智能助手，可以帮助你：

- 📝 **文件操作**：创建、读取、修改文件
- 🗂️ **目录管理**：浏览、创建、管理目录结构
- 💻 **代码编写**：提供代码示例和解决方案
- 🔍 **问题解答**：回答各种技术问题

有什么可以帮助你的吗？`);
});