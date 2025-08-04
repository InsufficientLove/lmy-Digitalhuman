// 改进视频播放器的JavaScript代码
// 将此代码添加到您的前端页面中

function improveVideoPlayer() {
    console.log('🎬 改进视频播放器...');
    
    // 1. 放大视频播放区域
    const videoElement = document.querySelector('video');
    if (videoElement) {
        // 设置更大的视频尺寸
        videoElement.style.width = '640px';
        videoElement.style.height = '480px';
        videoElement.style.maxWidth = '100%';
        videoElement.style.border = '2px solid #007bff';
        videoElement.style.borderRadius = '8px';
        videoElement.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        
        // 添加视频加载事件监听
        videoElement.addEventListener('loadstart', function() {
            console.log('📹 视频开始加载...');
        });
        
        videoElement.addEventListener('loadeddata', function() {
            console.log('✅ 视频数据已加载');
        });
        
        videoElement.addEventListener('canplay', function() {
            console.log('▶️ 视频可以播放');
        });
        
        videoElement.addEventListener('error', function(e) {
            console.error('❌ 视频加载错误:', e);
            console.error('视频源:', videoElement.src);
            
            // 显示错误信息
            const errorDiv = document.createElement('div');
            errorDiv.innerHTML = `
                <div style="color: red; padding: 10px; border: 1px solid red; margin: 10px;">
                    <h4>视频加载失败</h4>
                    <p>视频路径: ${videoElement.src}</p>
                    <p>错误类型: ${e.type}</p>
                    <button onclick="retryVideoLoad()">重试加载</button>
                </div>
            `;
            videoElement.parentNode.insertBefore(errorDiv, videoElement.nextSibling);
        });
    }
    
    // 2. 创建视频容器改进
    const videoContainer = document.querySelector('.video-container') || 
                          document.querySelector('#videoContainer') ||
                          videoElement?.parentElement;
    
    if (videoContainer) {
        videoContainer.style.textAlign = 'center';
        videoContainer.style.padding = '20px';
        videoContainer.style.backgroundColor = '#f8f9fa';
        videoContainer.style.borderRadius = '12px';
        videoContainer.style.margin = '20px auto';
        videoContainer.style.maxWidth = '800px';
    }
    
    // 3. 添加加载状态指示器
    function showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'video-loading';
        loadingDiv.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div style="border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
                <p style="margin-top: 20px; color: #666;">正在生成数字人视频...</p>
            </div>
            <style>
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            </style>
        `;
        
        if (videoContainer) {
            videoContainer.appendChild(loadingDiv);
        }
    }
    
    function hideLoadingIndicator() {
        const loadingDiv = document.getElementById('video-loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }
    
    // 4. 重试加载函数
    window.retryVideoLoad = function() {
        console.log('🔄 重试加载视频...');
        if (videoElement && videoElement.src) {
            // 添加时间戳避免缓存
            const originalSrc = videoElement.src.split('?')[0];
            videoElement.src = originalSrc + '?t=' + Date.now();
            videoElement.load();
        }
    };
    
    // 5. 检查视频文件是否存在
    window.checkVideoExists = function(videoUrl) {
        return fetch(videoUrl, { method: 'HEAD' })
            .then(response => {
                console.log(`视频文件检查: ${videoUrl} - ${response.status}`);
                return response.ok;
            })
            .catch(error => {
                console.error('视频文件检查失败:', error);
                return false;
            });
    };
    
    // 6. 改进的视频设置函数
    window.setVideoSource = function(videoUrl) {
        console.log('🎬 设置视频源:', videoUrl);
        
        if (!videoElement) {
            console.error('❌ 未找到视频元素');
            return;
        }
        
        showLoadingIndicator();
        
        // 检查视频文件是否存在
        checkVideoExists(videoUrl).then(exists => {
            if (exists) {
                videoElement.src = videoUrl;
                videoElement.load();
                hideLoadingIndicator();
                
                // 尝试自动播放
                setTimeout(() => {
                    videoElement.play().catch(e => {
                        console.log('自动播放失败，需要用户交互:', e);
                    });
                }, 500);
            } else {
                hideLoadingIndicator();
                console.error('❌ 视频文件不存在:', videoUrl);
                
                // 显示文件不存在的错误
                const errorDiv = document.createElement('div');
                errorDiv.innerHTML = `
                    <div style="color: red; padding: 15px; border: 2px solid red; margin: 10px; border-radius: 8px; background: #ffe6e6;">
                        <h4>❌ 视频文件未找到</h4>
                        <p><strong>请求的视频:</strong> ${videoUrl}</p>
                        <p><strong>可能原因:</strong></p>
                        <ul style="text-align: left;">
                            <li>视频生成失败</li>
                            <li>文件路径不正确</li>
                            <li>服务器文件未正确复制到Web目录</li>
                        </ul>
                        <button onclick="location.reload()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">刷新页面重试</button>
                    </div>
                `;
                
                if (videoContainer) {
                    videoContainer.appendChild(errorDiv);
                }
            }
        });
    };
    
    console.log('✅ 视频播放器改进完成');
}

// 页面加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', improveVideoPlayer);
} else {
    improveVideoPlayer();
}

// 导出函数供全局使用
window.improveVideoPlayer = improveVideoPlayer;