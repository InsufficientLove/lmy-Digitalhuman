// 数字人模板管理系统 - JavaScript
const API_BASE = '';

// 全局变量
let currentFile = null;
let currentTab = 'upload';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initUpload();
    initForm();
    loadTemplates();
    loadStatistics();
});

// 标签页切换
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // 更新标签页样式
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // 更新内容区域
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    currentTab = tabName;
    
    // 刷新数据
    if (tabName === 'list') {
        loadTemplates();
    } else if (tabName === 'stats') {
        loadStatistics();
    }
}

// 上传功能
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const resourceType = document.getElementById('resourceType');
    const removePreview = document.getElementById('removePreview');
    
    // 点击上传区域
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // 文件选择
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelect(file);
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
    });
    
    // 资源类型切换
    resourceType.addEventListener('change', () => {
        updateFileAccept();
        clearPreview();
    });
    
    // 移除预览
    removePreview.addEventListener('click', (e) => {
        e.stopPropagation();
        clearPreview();
    });
}

function updateFileAccept() {
    const resourceType = document.getElementById('resourceType').value;
    const fileInput = document.getElementById('fileInput');
    const uploadHint = document.querySelector('.upload-hint');
    
    if (resourceType === 'image') {
        fileInput.accept = 'image/jpeg,image/png,image/jpg';
        uploadHint.textContent = '支持 JPG, PNG 格式';
    } else {
        fileInput.accept = 'video/mp4';
        uploadHint.textContent = '支持 MP4 格式，建议 3-10 秒，512x512 以上分辨率';
    }
}

function handleFileSelect(file) {
    const resourceType = document.getElementById('resourceType').value;
    
    // 验证文件类型
    const validTypes = resourceType === 'image' 
        ? ['image/jpeg', 'image/png', 'image/jpg']
        : ['video/mp4'];
    
    if (!validTypes.includes(file.type)) {
        showNotification(`请选择正确的${resourceType === 'image' ? '图片' : '视频'}格式`, 'error');
        return;
    }
    
    currentFile = file;
    showPreview(file);
}

function showPreview(file) {
    const previewArea = document.getElementById('previewArea');
    const previewContainer = document.getElementById('previewContainer');
    const resourceType = document.getElementById('resourceType').value;
    
    // 清除旧预览
    const oldMedia = previewContainer.querySelector('img, video');
    if (oldMedia) oldMedia.remove();
    
    const reader = new FileReader();
    reader.onload = (e) => {
        if (resourceType === 'image') {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'preview-image';
            previewContainer.insertBefore(img, previewContainer.firstChild);
        } else {
            const video = document.createElement('video');
            video.src = e.target.result;
            video.className = 'preview-video';
            video.controls = true;
            video.autoplay = true;
            video.loop = true;
            video.muted = true;
            previewContainer.insertBefore(video, previewContainer.firstChild);
        }
        
        previewArea.classList.add('active');
    };
    
    reader.readAsDataURL(file);
}

function clearPreview() {
    const previewArea = document.getElementById('previewArea');
    const previewContainer = document.getElementById('previewContainer');
    const fileInput = document.getElementById('fileInput');
    
    const media = previewContainer.querySelector('img, video');
    if (media) media.remove();
    
    previewArea.classList.remove('active');
    fileInput.value = '';
    currentFile = null;
}

// 表单处理
function initForm() {
    const form = document.getElementById('templateForm');
    const resetBtn = document.getElementById('resetBtn');
    
    form.addEventListener('submit', handleSubmit);
    resetBtn.addEventListener('click', resetForm);
}

async function handleSubmit(e) {
    e.preventDefault();
    
    if (!currentFile) {
        showNotification('请先选择文件', 'error');
        return;
    }
    
    const formData = new FormData();
    const resourceType = document.getElementById('resourceType').value;
    
    // 添加文件
    if (resourceType === 'image') {
        formData.append('ImageFile', currentFile);
    } else {
        formData.append('VideoFile', currentFile);
    }
    
    // 添加其他字段
    formData.append('TemplateName', document.getElementById('displayName').value);
    formData.append('SystemName', document.getElementById('systemName').value);
    formData.append('ResourceType', resourceType);
    formData.append('Description', document.getElementById('description').value);
    formData.append('Gender', document.getElementById('gender').value);
    formData.append('AgeRange', document.getElementById('ageRange').value);
    formData.append('Style', document.getElementById('style').value);
    formData.append('EnableEmotion', true);
    
    try {
        showLoading('正在上传和预处理...');
        
        const response = await fetch('/api/DigitalHumanTemplate/create', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            showNotification('模板创建成功！', 'success');
            resetForm();
            // 切换到列表页
            setTimeout(() => switchTab('list'), 1500);
        } else {
            showNotification(`创建失败: ${result.message}`, 'error');
        }
    } catch (error) {
        hideLoading();
        showNotification(`创建失败: ${error.message}`, 'error');
        console.error('Error:', error);
    }
}

function resetForm() {
    document.getElementById('templateForm').reset();
    clearPreview();
    document.getElementById('resourceType').value = 'image';
    updateFileAccept();
}

// 加载模板列表
async function loadTemplates() {
    const grid = document.getElementById('templatesGrid');
    
    try {
        const response = await fetch('/api/DigitalHumanTemplate/list?page=1&pageSize=100');
        const result = await response.json();
        
        if (result.success && result.templates && result.templates.length > 0) {
            grid.innerHTML = result.templates.map(template => createTemplateCard(template)).join('');
            
            // 绑定删除按钮
            grid.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', () => deleteTemplate(btn.dataset.id));
            });
        } else {
            grid.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">暂无模板，请先创建</p>';
        }
    } catch (error) {
        grid.innerHTML = '<p style="text-align: center; color: var(--error-color); padding: 40px;">加载失败</p>';
        console.error('Error:', error);
    }
}

function createTemplateCard(template) {
    const statusClass = {
        'ready': 'status-ready',
        'processing': 'status-processing',
        'error': 'status-error'
    }[template.status] || 'status-ready';
    
    const statusText = {
        'ready': '就绪',
        'processing': '处理中',
        'error': '错误'
    }[template.status] || '未知';
    
    const mediaHtml = template.resourceType === 'video' && template.videoUrl
        ? `<video class="template-preview" src="${template.videoUrl}" muted loop autoplay></video>`
        : `<img class="template-preview" src="${template.imageUrl || template.imageUrl || '/images/default-avatar.svg'}" alt="${template.displayName}">`;
    
    return `
        <div class="template-card">
            <div class="template-status ${statusClass}">${statusText}</div>
            ${mediaHtml}
            <div class="template-info">
                <div class="template-name">${template.displayName || template.templateName}</div>
                <div class="template-desc">${template.description || '暂无描述'}</div>
                <div class="template-meta">
                    <span class="template-tag">${template.resourceType === 'video' ? '📹 视频' : '🖼️ 图片'}</span>
                    <span class="template-tag">${getGenderText(template.gender)}</span>
                    <span class="template-tag">${getStyleText(template.style)}</span>
                    <span class="template-tag">使用 ${template.usageCount || 0} 次</span>
                </div>
                <div class="template-actions">
                    <button class="btn btn-small btn-secondary" onclick="testTemplate('${template.templateId}')">
                        🧪 测试
                    </button>
                    <button class="btn btn-small btn-danger btn-delete" data-id="${template.templateId}">
                        🗑️ 删除
                    </button>
                </div>
            </div>
        </div>
    `;
}

function getGenderText(gender) {
    const map = {
        'male': '👨 男性',
        'female': '👩 女性',
        'neutral': '⚧ 中性'
    };
    return map[gender] || gender;
}

function getStyleText(style) {
    const map = {
        'professional': '💼 专业',
        'friendly': '😊 友好',
        'casual': '👕 休闲'
    };
    return map[style] || style;
}

// 删除模板
async function deleteTemplate(templateId) {
    if (!confirm('确定要删除这个模板吗？')) {
        return;
    }
    
    try {
        showLoading('删除中...');
        
        const response = await fetch(`/api/DigitalHumanTemplate/${templateId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            showNotification('删除成功', 'success');
            loadTemplates();
        } else {
            showNotification('删除失败', 'error');
        }
    } catch (error) {
        hideLoading();
        showNotification('删除失败', 'error');
        console.error('Error:', error);
    }
}

// 测试模板
function testTemplate(templateId) {
    const text = prompt('请输入测试文本：', '你好，我是数字人助手');
    if (!text) return;
    
    showLoading('生成测试视频中...');
    
    fetch('/api/DigitalHumanTemplate/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            templateId: templateId,
            text: text,
            quality: 'medium'
        })
    })
    .then(res => res.json())
    .then(result => {
        hideLoading();
        if (result.success && result.videoUrl) {
            // 创建预览弹窗
            showVideoPreview(result.videoUrl);
            showNotification('生成成功！', 'success');
        } else {
            showNotification('生成失败', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showNotification('生成失败', 'error');
        console.error('Error:', error);
    });
}

function showVideoPreview(videoUrl) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(10, 14, 39, 0.95);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    
    modal.innerHTML = `
        <div style="max-width: 800px; width: 90%; background: var(--card-bg); padding: 30px; border-radius: 15px; border: 1px solid var(--border-color);">
            <h3 style="color: var(--accent-color); margin-bottom: 20px;">生成结果</h3>
            <video controls autoplay style="width: 100%; border-radius: 10px; border: 2px solid var(--accent-color);">
                <source src="${videoUrl}" type="video/mp4">
            </video>
            <button onclick="this.closest('div').parentElement.remove()" class="btn btn-primary" style="width: 100%; margin-top: 20px;">关闭</button>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// 加载统计信息
async function loadStatistics() {
    const statsContent = document.getElementById('statsContent');
    
    try {
        const response = await fetch('/api/DigitalHumanTemplate/statistics');
        const result = await response.json();
        
        if (result.success && result.statistics) {
            const stats = result.statistics;
            statsContent.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
                    <div class="stat-card">
                        <div class="stat-value">${stats.totalTemplates || 0}</div>
                        <div class="stat-label">总模板数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.activeTemplates || 0}</div>
                        <div class="stat-label">活跃模板</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.totalUsage || 0}</div>
                        <div class="stat-label">总使用次数</div>
                    </div>
                </div>
                
                ${stats.mostUsedTemplates && stats.mostUsedTemplates.length > 0 ? `
                    <h3 style="margin-top: 40px; margin-bottom: 20px; color: var(--accent-color);">最常用模板</h3>
                    <div class="templates-grid">
                        ${stats.mostUsedTemplates.map(t => createTemplateCard(t)).join('')}
                    </div>
                ` : ''}
            `;
            
            // 添加统计卡片样式
            const style = document.createElement('style');
            style.textContent = `
                .stat-card {
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    transition: all 0.3s ease;
                }
                .stat-card:hover {
                    border-color: var(--accent-color);
                    box-shadow: 0 0 20px rgba(0, 243, 255, 0.3);
                    transform: translateY(-5px);
                }
                .stat-value {
                    font-size: 48px;
                    font-weight: bold;
                    background: linear-gradient(90deg, var(--accent-color), #8a2be2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }
                .stat-label {
                    font-size: 14px;
                    color: var(--text-secondary);
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
            `;
            if (!document.querySelector('#stats-style')) {
                style.id = 'stats-style';
                document.head.appendChild(style);
            }
        } else {
            statsContent.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">暂无统计数据</p>';
        }
    } catch (error) {
        statsContent.innerHTML = '<p style="text-align: center; color: var(--error-color); padding: 40px;">加载失败</p>';
        console.error('Error:', error);
    }
}

// UI 辅助函数
function showLoading(text = '处理中...') {
    const overlay = document.getElementById('loadingOverlay');
    const loadingText = document.getElementById('loadingText');
    loadingText.textContent = text;
    overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
