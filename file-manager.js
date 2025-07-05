// file-manager.js - Chrome Plus V2.1.1 文件管理器
// 文件夹管理功能实现

// 全局状态
let fileManagerState = {
    currentPath: '.',
    selectedItem: null,
    folderTree: null,
    expandedFolders: new Set()
};

// 初始化文件管理器
document.addEventListener('DOMContentLoaded', function() {
    initializeFileManager();
});

function initializeFileManager() {
    console.log('初始化文件管理器...');
    
    // 绑定主标签页切换事件
    bindMainTabEvents();
    
    // 绑定文件管理器事件
    bindFileManagerEvents();
    
    // 绑定模态框事件
    bindModalEvents();
    
    // 绑定右键菜单事件
    bindContextMenuEvents();
    
    console.log('文件管理器初始化完成');
}

// 绑定主标签页事件
function bindMainTabEvents() {
    const tabButtons = document.querySelectorAll('.main-tab-button');
    const tabContents = document.querySelectorAll('.main-tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // 移除所有活动状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // 激活当前标签页
            this.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
            
            // 如果切换到文件管理标签页，加载文件夹树
            if (targetTab === 'files') {
                loadFolderTree();
            }
        });
    });
}

// 绑定文件管理器事件
function bindFileManagerEvents() {
    // 刷新按钮
    document.getElementById('refresh-tree').addEventListener('click', function() {
        loadFolderTree();
    });
    
    // 新建文件夹按钮
    document.getElementById('create-folder').addEventListener('click', function() {
        showCreateFolderModal();
    });
    
    // 上传文件按钮
    document.getElementById('upload-file').addEventListener('click', function() {
        // TODO: 实现文件上传功能
        alert('文件上传功能即将推出！');
    });
}

// 绑定模态框事件
function bindModalEvents() {
    const modal = document.getElementById('folder-modal');
    const closeBtn = document.getElementById('folder-modal-close');
    const cancelBtn = document.getElementById('folder-modal-cancel');
    const confirmBtn = document.getElementById('folder-modal-confirm');
    
    // 关闭模态框
    [closeBtn, cancelBtn].forEach(btn => {
        btn.addEventListener('click', function() {
            hideFolderModal();
        });
    });
    
    // 点击模态框外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            hideFolderModal();
        }
    });
    
    // 确认按钮
    confirmBtn.addEventListener('click', function() {
        handleModalConfirm();
    });
}

// 绑定右键菜单事件
function bindContextMenuEvents() {
    const contextMenu = document.getElementById('context-menu');
    
    // 隐藏右键菜单
    document.addEventListener('click', function() {
        contextMenu.style.display = 'none';
    });
    
    // 右键菜单项点击事件
    contextMenu.addEventListener('click', function(e) {
        e.stopPropagation();
        const action = e.target.getAttribute('data-action');
        if (action && fileManagerState.selectedItem) {
            handleContextMenuAction(action, fileManagerState.selectedItem);
        }
        contextMenu.style.display = 'none';
    });
}

// 加载文件夹树
async function loadFolderTree(path = '.') {
    const treeContainer = document.getElementById('folder-tree');
    treeContainer.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/folders/tree?path=${encodeURIComponent(path)}&max_depth=3`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        fileManagerState.folderTree = data;
        fileManagerState.currentPath = path;
        
        // 更新当前路径显示
        document.getElementById('current-path').textContent = path || './';
        
        // 渲染文件夹树
        renderFolderTree(data.tree, treeContainer);
        
        console.log('文件夹树加载成功:', data);
    } catch (error) {
        console.error('加载文件夹树失败:', error);
        treeContainer.innerHTML = `<div class="error">加载失败: ${error.message}</div>`;
    }
}

// 渲染文件夹树
function renderFolderTree(node, container) {
    container.innerHTML = '';
    
    const treeElement = createTreeNode(node, 0);
    container.appendChild(treeElement);
}

// 创建树节点
function createTreeNode(node, depth) {
    const nodeElement = document.createElement('div');
    nodeElement.className = 'tree-node';
    nodeElement.style.paddingLeft = `${depth * 20}px`;
    
    // 节点内容
    const nodeContent = document.createElement('div');
    nodeContent.className = 'tree-node-content';
    
    // 展开/折叠图标
    const expandIcon = document.createElement('span');
    expandIcon.className = 'expand-icon';
    
    if (node.type === 'folder' && node.children && node.children.length > 0) {
        expandIcon.textContent = node.expanded ? '📂' : '📁';
        expandIcon.style.cursor = 'pointer';
        expandIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleFolder(node, nodeElement);
        });
    } else if (node.type === 'folder') {
        expandIcon.textContent = '📁';
    } else {
        expandIcon.textContent = '📄';
    }
    
    // 文件/文件夹名称
    const nameSpan = document.createElement('span');
    nameSpan.className = 'node-name';
    nameSpan.textContent = node.name;
    
    // 文件大小和修改时间
    const infoSpan = document.createElement('span');
    infoSpan.className = 'node-info';
    if (node.type === 'file') {
        infoSpan.textContent = ` (${formatFileSize(node.size)}, ${node.modified})`;
    } else {
        infoSpan.textContent = ` (${node.modified})`;
    }
    
    nodeContent.appendChild(expandIcon);
    nodeContent.appendChild(nameSpan);
    nodeContent.appendChild(infoSpan);
    
    // 绑定点击事件
    nodeContent.addEventListener('click', function() {
        selectNode(node, nodeElement);
    });
    
    // 绑定右键菜单
    nodeContent.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        showContextMenu(e, node);
    });
    
    nodeElement.appendChild(nodeContent);
    
    // 子节点容器
    if (node.type === 'folder' && node.children) {
        const childrenContainer = document.createElement('div');
        childrenContainer.className = 'tree-children';
        childrenContainer.style.display = node.expanded ? 'block' : 'none';
        
        node.children.forEach(child => {
            const childElement = createTreeNode(child, depth + 1);
            childrenContainer.appendChild(childElement);
        });
        
        nodeElement.appendChild(childrenContainer);
    }
    
    return nodeElement;
}

// 切换文件夹展开/折叠
function toggleFolder(node, nodeElement) {
    node.expanded = !node.expanded;
    
    const expandIcon = nodeElement.querySelector('.expand-icon');
    const childrenContainer = nodeElement.querySelector('.tree-children');
    
    if (node.expanded) {
        expandIcon.textContent = '📂';
        if (childrenContainer) {
            childrenContainer.style.display = 'block';
        }
        fileManagerState.expandedFolders.add(node.path);
    } else {
        expandIcon.textContent = '📁';
        if (childrenContainer) {
            childrenContainer.style.display = 'none';
        }
        fileManagerState.expandedFolders.delete(node.path);
    }
}

// 选择节点
function selectNode(node, nodeElement) {
    // 移除之前的选中状态
    document.querySelectorAll('.tree-node-content.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    // 添加选中状态
    nodeElement.querySelector('.tree-node-content').classList.add('selected');
    fileManagerState.selectedItem = node;
    
    // 显示文件详情
    showFileDetails(node);
}

// 显示文件详情
async function showFileDetails(node) {
    const detailsContent = document.querySelector('.details-content');
    detailsContent.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        // 获取详细信息
        const response = await fetch(`${API_BASE_URL}/api/folders/info?path=${encodeURIComponent(node.path)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const info = await response.json();
        
        // 渲染详情
        let detailsHTML = `
            <div class="detail-item">
                <strong>名称:</strong> ${info.name}
            </div>
            <div class="detail-item">
                <strong>路径:</strong> ${info.path || './'}
            </div>
            <div class="detail-item">
                <strong>类型:</strong> ${info.type === 'folder' ? '文件夹' : '文件'}
            </div>
            <div class="detail-item">
                <strong>修改时间:</strong> ${info.modified}
            </div>
            <div class="detail-item">
                <strong>创建时间:</strong> ${info.created}
            </div>
        `;
        
        if (info.type === 'file') {
            detailsHTML += `
                <div class="detail-item">
                    <strong>大小:</strong> ${formatFileSize(info.size)}
                </div>
            `;
        } else {
            detailsHTML += `
                <div class="detail-item">
                    <strong>总大小:</strong> ${formatFileSize(info.total_size)}
                </div>
                <div class="detail-item">
                    <strong>文件数量:</strong> ${info.file_count}
                </div>
                <div class="detail-item">
                    <strong>文件夹数量:</strong> ${info.folder_count}
                </div>
            `;
        }
        
        detailsContent.innerHTML = detailsHTML;
    } catch (error) {
        console.error('获取文件详情失败:', error);
        detailsContent.innerHTML = `<div class="error">获取详情失败: ${error.message}</div>`;
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 显示右键菜单
function showContextMenu(event, node) {
    const contextMenu = document.getElementById('context-menu');
    fileManagerState.selectedItem = node;
    
    contextMenu.style.display = 'block';
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
}

// 处理右键菜单操作
function handleContextMenuAction(action, node) {
    switch (action) {
        case 'open':
            if (node.type === 'folder') {
                loadFolderTree(node.path);
            }
            break;
        case 'rename':
            showRenameFolderModal(node);
            break;
        case 'delete':
            showDeleteConfirmModal(node);
            break;
        case 'info':
            showFileDetails(node);
            break;
    }
}

// 显示创建文件夹模态框
function showCreateFolderModal() {
    const modal = document.getElementById('folder-modal');
    const title = document.getElementById('folder-modal-title');
    const content = document.getElementById('folder-modal-content');
    
    title.textContent = '新建文件夹';
    content.innerHTML = `
        <div class="form-group">
            <label for="folder-name">文件夹名称:</label>
            <input type="text" id="folder-name" placeholder="请输入文件夹名称">
        </div>
        <div class="form-group">
            <label for="folder-path">创建位置:</label>
            <input type="text" id="folder-path" value="${fileManagerState.currentPath}" readonly>
        </div>
    `;
    
    modal.style.display = 'block';
    modal.setAttribute('data-action', 'create');
    
    // 聚焦到输入框
    setTimeout(() => {
        document.getElementById('folder-name').focus();
    }, 100);
}

// 显示重命名模态框
function showRenameFolderModal(node) {
    const modal = document.getElementById('folder-modal');
    const title = document.getElementById('folder-modal-title');
    const content = document.getElementById('folder-modal-content');
    
    title.textContent = '重命名';
    content.innerHTML = `
        <div class="form-group">
            <label for="new-name">新名称:</label>
            <input type="text" id="new-name" value="${node.name}">
        </div>
        <div class="form-group">
            <label>当前路径:</label>
            <span>${node.path}</span>
        </div>
    `;
    
    modal.style.display = 'block';
    modal.setAttribute('data-action', 'rename');
    modal.setAttribute('data-path', node.path);
    
    // 选中文件名（不包括扩展名）
    setTimeout(() => {
        const input = document.getElementById('new-name');
        input.focus();
        const lastDot = node.name.lastIndexOf('.');
        if (lastDot > 0) {
            input.setSelectionRange(0, lastDot);
        } else {
            input.select();
        }
    }, 100);
}

// 显示删除确认模态框
function showDeleteConfirmModal(node) {
    const modal = document.getElementById('folder-modal');
    const title = document.getElementById('folder-modal-title');
    const content = document.getElementById('folder-modal-content');
    
    title.textContent = '确认删除';
    content.innerHTML = `
        <div class="warning">
            <p>⚠️ 您确定要删除以下${node.type === 'folder' ? '文件夹' : '文件'}吗？</p>
            <p><strong>${node.name}</strong></p>
            <p>路径: ${node.path}</p>
            ${node.type === 'folder' ? '<p class="danger">注意：文件夹及其所有内容将被永久删除！</p>' : ''}
        </div>
    `;
    
    modal.style.display = 'block';
    modal.setAttribute('data-action', 'delete');
    modal.setAttribute('data-path', node.path);
}

// 隐藏模态框
function hideFolderModal() {
    const modal = document.getElementById('folder-modal');
    modal.style.display = 'none';
    modal.removeAttribute('data-action');
    modal.removeAttribute('data-path');
}

// 处理模态框确认
async function handleModalConfirm() {
    const modal = document.getElementById('folder-modal');
    const action = modal.getAttribute('data-action');
    
    try {
        switch (action) {
            case 'create':
                await handleCreateFolder();
                break;
            case 'rename':
                await handleRenameFolder();
                break;
            case 'delete':
                await handleDeleteFolder();
                break;
        }
        
        hideFolderModal();
        loadFolderTree(fileManagerState.currentPath); // 刷新树
    } catch (error) {
        alert(`操作失败: ${error.message}`);
    }
}

// 处理创建文件夹
async function handleCreateFolder() {
    const folderName = document.getElementById('folder-name').value.trim();
    const folderPath = document.getElementById('folder-path').value.trim();
    
    if (!folderName) {
        throw new Error('请输入文件夹名称');
    }
    
    const response = await fetch(`${API_BASE_URL}/api/folders/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            path: folderPath,
            name: folderName
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '创建文件夹失败');
    }
    
    const result = await response.json();
    console.log('文件夹创建成功:', result);
}

// 处理重命名
async function handleRenameFolder() {
    const newName = document.getElementById('new-name').value.trim();
    const oldPath = document.getElementById('folder-modal').getAttribute('data-path');
    
    if (!newName) {
        throw new Error('请输入新名称');
    }
    
    const response = await fetch(`${API_BASE_URL}/api/folders/rename`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            old_path: oldPath,
            new_name: newName
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '重命名失败');
    }
    
    const result = await response.json();
    console.log('重命名成功:', result);
}

// 处理删除
async function handleDeleteFolder() {
    const path = document.getElementById('folder-modal').getAttribute('data-path');
    
    const response = await fetch(`${API_BASE_URL}/api/folders/delete`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            path: path
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '删除失败');
    }
    
    const result = await response.json();
    console.log('删除成功:', result);
}
