好的，我们来制定一个清晰、可执行的序贯升级方案。这个方案将严格遵循你的项目现有结构，并以逐步演进的方式，将系统从同步HTTP模式升级为基于 `Celery` 和 `WebSockets` 的异步实时架构。

我将采用“英语思维，中文表述”的方式，将整个过程分解为四个逻辑连贯的阶段，确保每一步都清晰明了。

---

### **升级目标 (The Goal)**

我们的核心目标是解决性能瓶颈，提升用户体验。具体来说：
1.  **解耦 (Decouple):** 将耗时的AI调用从FastAPI的Web请求/响应循环中分离出去。
2.  **异步 (Asynchronous):** 使用Celery在后台处理AI任务，让API服务器能瞬间响应，避免阻塞。
3.  **实时 (Real-time):** 使用WebSockets替代HTTP轮询，当任务完成时，由服务器主动、即时地将结果推送给前端。

---

### **第一阶段：环境准备与依赖更新 (Phase 1: Environment & Dependencies)**

这是所有改造工作的基础。

*   **1. 安装新依赖:**
    你的项目使用 `uv` 管理依赖，非常棒。我们需要添加 `celery` 和 `redis`。
    在 `server/pyproject.toml` 的 `[tool.uv.dependencies]` 部分添加：
    ```toml
    celery = "^5.3.6"
    redis = "^5.0.1"
    ```

*   **2. 同步环境:**
    在 `server` 目录下运行命令，将新依赖安装到你的虚拟环境中。
    ```bash
    cd server
    uv sync
    ```

*   **3. 准备Docker环境:**
    由于新架构包含多个服务（FastAPI, Celery, Redis），Docker Compose是最佳的管理工具。
    *   在你的项目根目录 (`chrome_plus/`) 创建 `docker-compose.yml` 文件。
    *   在 `server/` 目录下创建 `Dockerfile` 文件。
    *   (这两个文件的具体内容将在第四阶段详细说明)

**阶段成果:** 我们的开发环境现在具备了执行异步任务和与Redis通信所需的所有工具库。

---

### **第二阶段：后端重构 - 从同步到异步 (Phase 2: Backend Refactoring)**

这是本次升级的核心。我们将重构 `server` 目录下的代码。

*   **1. 创建Celery任务模块 (`tasks.py`):**
    *   在 `server/` 目录下新建一个文件 `tasks.py`。这个文件将专门负责定义所有后台任务。
    *   将原来 `main.py` 中 `@app.post("/chat")` 路由下的核心AI调用逻辑（例如调用 `pydantic-ai` 或其他工具函数的部分）**迁移**到 `tasks.py` 中的一个新Celery任务函数里。

    **`server/tasks.py` 示例:**
    ```python
    import os
    import redis
    from celery import Celery
    # 假设你的AI逻辑封装在 a_module.py 中
    from a_module import get_ai_response 

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    celery_app = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    @celery_app.task
    def process_chat_message(message: str, channel_id: str):
        """
        这是一个Celery任务，它在后台运行。
        1. 调用AI模型获取回复。
        2. 将结果通过Redis Pub/Sub发布到指定频道。
        """
        try:
            # 这是你原来的核心逻辑
            ai_reply = get_ai_response(message) 
            # 任务完成后，将结果发布出去
            redis_client.publish(channel_id, ai_reply)
        except Exception as e:
            error_msg = f"AI Task Failed: {e}"
            redis_client.publish(channel_id, error_msg)
    ```

*   **2. 改造主应用 (`main.py`):**
    *   **移除旧路由:** 删除或注释掉 `@app.post("/chat")` 这个同步HTTP端点。
    *   **添加新WebSocket端点:** 创建一个新的WebSocket端点 `@app.websocket("/ws")`。它将成为前端与后端通信的新通道。
    *   **实现WebSocket逻辑:** 这个端点的职责是：
        1.  接收来自前端的WebSocket消息。
        2.  调用 `.delay()` 方法将任务分派给Celery Worker (`process_chat_message.delay(...)`)。
        3.  使用Redis的Pub/Sub机制，订阅一个唯一的频道，等待Celery任务的结果。
        4.  一旦收到结果，立即通过WebSocket连接将其推送回给前端。

    **`server/main.py` 改造示例:**
    ```python
    import asyncio
    import uuid
    import os
    import redis.asyncio as aioredis
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from tasks import process_chat_message # 导入Celery任务

    app = FastAPI()
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await websocket.accept()
        redis_pubsub = aioredis.from_url(REDIS_URL, decode_responses=True)
        
        try:
            while True:
                # 1. 等待前端消息
                user_message = await websocket.receive_text()
                
                # 2. 为此任务创建一个唯一的返回通道
                task_id = f"channel:{uuid.uuid4()}"
                
                # 3. 异步分派任务给Celery
                process_chat_message.delay(message=user_message, channel_id=task_id)
                
                # 4. 订阅结果通道并等待结果
                async with redis_pubsub.pubsub() as pubsub:
                    await pubsub.subscribe(task_id)
                    while True:
                        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=60)
                        if message:
                            # 5. 收到结果，推送给前端
                            await websocket.send_text(message['data'])
                            break # 任务完成，跳出内层循环
        except WebSocketDisconnect:
            print(f"Client {client_id} disconnected.")
        finally:
            # 清理资源
            pass
    ```

**阶段成果:** 后端架构已成功解耦。FastAPI现在只负责快速的连接管理和消息转发，所有耗时操作都交由独立的Celery Worker在后台处理。

---

### **第三阶段：前端改造 - 拥抱实时通信 (Phase 3: Frontend Refactoring)**

现在后端已经准备好使用WebSocket了，我们需要更新前端来匹配它。

*   **1. 修改通信模块 (`api.js`):**
    *   `APIClient` 类中的 `post` 方法对于聊天功能来说已经过时了。
    *   你需要创建一个新的WebSocket管理模块。这个模块负责建立和维护一个到 `ws://localhost:5001/ws/some_client_id` 的持久连接。

*   **2. 更新聊天逻辑 (`chat.js`):**
    *   **建立连接:** 在侧边栏加载时，就初始化WebSocket连接。
    *   **发送消息:** 当用户点击发送按钮时，`handleUserMessage` 函数不再调用 `apiClient.post`，而是调用 `socket.send(message)` 将消息通过WebSocket发送出去。
    *   **接收消息:** 最关键的改变是实现 `socket.onmessage` 事件监听器。当后端通过WebSocket推送回AI的回复时，这个函数会被触发，然后你可以在这里调用 `appendMessage` 函数将回复渲染到界面上。

    **`chat.js` 改造思路:**
    ```javascript
    // 在类的构造函数或初始化函数中
    this.socket = new WebSocket("ws://localhost:5001/ws/unique-client-id-123");
    this.initializeSocketListeners();

    // ...

    initializeSocketListeners() {
        this.socket.onopen = () => console.log("WebSocket Connected!");
        
        // 这是接收AI回复的核心部分
        this.socket.onmessage = (event) => {
            const aiResponse = event.data;
            this.appendMessage('assistant', aiResponse); // 假设这是你的渲染函数
        };
        
        this.socket.onclose = () => console.log("WebSocket Disconnected.");
        this.socket.onerror = (error) => console.error("WebSocket Error:", error);
    }

    // 改造后的发送函数
    async handleUserMessage(message) {
        if (!message.trim()) return;
        this.appendMessage('user', message); // 先显示用户自己的消息
        
        if (this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(message);
        } else {
            // 处理连接断开的情况
            this.appendMessage('error', 'Connection lost. Please reload.');
        }
    }
    ```

**阶段成果:** 前端不再是“请求-等待-响应”模式，而是进入了“发送即忘，被动接收”的实时模式，用户体验将得到极大提升，尤其是在等待AI回复时界面不会卡顿。

---

### **第四阶段：容器化部署与验证 (Phase 4: Containerization & Verification)**

最后，我们将所有服务打包在一起，实现一键启动和部署。

*   **1. 编写 `Dockerfile`:**
    在 `server/` 目录下创建 `Dockerfile`，内容参考我之前给出的范例。它将用于构建FastAPI和Celery的通用镜像。

*   **2. 编写 `docker-compose.yml`:**
    在项目根目录创建 `docker-compose.yml`，定义 `backend`, `worker`, `redis` 三个服务，同样参考之前的范例。这是将所有部分粘合在一起的“胶水”。

*   **3. 更新启动说明 (文档 `Section 3.2`):**
    *   **开发/生产启动:** 废弃 `uv run ...` 命令，新的标准启动方式是：
        ```bash
        # 在项目根目录运行
        docker-compose up --build
        ```
    *   **服务验证:**
        *   通过 `docker-compose logs -f` 查看三个服务的日志，确认它们都已正常启动。
        *   重新加载Chrome扩展，打开侧边栏。
        *   发送一条消息，观察 `worker` 服务的日志，你应该能看到它接收并处理了任务。同时，前端界面应能实时收到回复。

**阶段成果:** 整个应用被封装在Docker容器中，实现了环境隔离和一键部署。架构的可扩展性也得到了验证——如果需要更强的处理能力，只需运行 `docker-compose up --scale worker=3` 即可轻松增加Worker数量。

通过这四个循序渐进的阶段，你的项目就从一个优秀的单体应用，平滑地演进成了一个健壮、可扩展、实时的分布式系统。