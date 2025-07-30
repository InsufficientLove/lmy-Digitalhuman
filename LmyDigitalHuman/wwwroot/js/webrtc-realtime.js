/**
 * WebRTC实时数字人通信模块
 * 支持单GPU和4GPU配置的自适应WebRTC通信
 */

class DigitalHumanWebRTC {
    constructor(config = {}) {
        this.config = {
            // 基础配置
            serverUrl: config.serverUrl || 'ws://localhost:5000/realtime',
            
            // WebRTC配置
            iceServers: config.iceServers || [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ],
            
            // 媒体配置 - 根据GPU配置自适应
            mediaConstraints: this.getMediaConstraints(config.gpuMode || 'single'),
            
            // 性能配置
            performanceMode: config.gpuMode || 'single', // 'single' | 'quad'
            enableStats: config.enableStats !== false,
            
            ...config
        };
        
        this.peerConnection = null;
        this.localStream = null;
        this.remoteStream = null;
        this.websocket = null;
        this.dataChannel = null;
        
        this.stats = {
            latency: 0,
            fps: 0,
            bitrate: 0,
            packetsLost: 0
        };
        
        this.callbacks = {
            onConnected: () => {},
            onDisconnected: () => {},
            onRemoteStream: () => {},
            onStats: () => {},
            onError: () => {}
        };
        
        this.init();
    }
    
    /**
     * 根据GPU模式获取媒体约束
     */
    getMediaConstraints(gpuMode) {
        const constraints = {
            single: {
                video: {
                    width: { ideal: 640, max: 1280 },
                    height: { ideal: 480, max: 720 },
                    frameRate: { ideal: 15, max: 25 }
                },
                audio: {
                    sampleRate: 16000,
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true
                }
            },
            quad: {
                video: {
                    width: { ideal: 1280, max: 1920 },
                    height: { ideal: 720, max: 1080 },
                    frameRate: { ideal: 25, max: 30 }
                },
                audio: {
                    sampleRate: 48000,
                    channelCount: 2,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            }
        };
        
        return constraints[gpuMode] || constraints.single;
    }
    
    /**
     * 初始化WebRTC连接
     */
    async init() {
        try {
            // 创建PeerConnection
            this.peerConnection = new RTCPeerConnection({
                iceServers: this.config.iceServers
            });
            
            // 设置事件监听器
            this.setupPeerConnectionEvents();
            
            // 连接WebSocket信令服务器
            await this.connectWebSocket();
            
            console.log('✅ WebRTC初始化完成');
        } catch (error) {
            console.error('❌ WebRTC初始化失败:', error);
            this.callbacks.onError(error);
        }
    }
    
    /**
     * 设置PeerConnection事件监听器
     */
    setupPeerConnectionEvents() {
        // ICE候选者事件
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.sendSignalingMessage({
                    type: 'ice-candidate',
                    candidate: event.candidate
                });
            }
        };
        
        // 远程流事件
        this.peerConnection.ontrack = (event) => {
            console.log('📺 接收到远程流');
            this.remoteStream = event.streams[0];
            this.callbacks.onRemoteStream(this.remoteStream);
        };
        
        // 连接状态变化
        this.peerConnection.onconnectionstatechange = () => {
            console.log('🔗 连接状态:', this.peerConnection.connectionState);
            
            switch (this.peerConnection.connectionState) {
                case 'connected':
                    this.callbacks.onConnected();
                    this.startStatsCollection();
                    break;
                case 'disconnected':
                case 'failed':
                case 'closed':
                    this.callbacks.onDisconnected();
                    break;
            }
        };
        
        // 数据通道
        this.peerConnection.ondatachannel = (event) => {
            const channel = event.channel;
            channel.onmessage = (event) => {
                this.handleDataChannelMessage(JSON.parse(event.data));
            };
        };
    }
    
    /**
     * 连接WebSocket信令服务器
     */
    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            this.websocket = new WebSocket(this.config.serverUrl);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket连接成功');
                
                // 发送配置信息
                this.sendSignalingMessage({
                    type: 'config',
                    performanceMode: this.config.performanceMode,
                    mediaConstraints: this.config.mediaConstraints
                });
                
                resolve();
            };
            
            this.websocket.onmessage = async (event) => {
                const message = JSON.parse(event.data);
                await this.handleSignalingMessage(message);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket错误:', error);
                reject(error);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket连接关闭');
                this.callbacks.onDisconnected();
            };
        });
    }
    
    /**
     * 处理信令消息
     */
    async handleSignalingMessage(message) {
        try {
            switch (message.type) {
                case 'offer':
                    await this.handleOffer(message.offer);
                    break;
                    
                case 'answer':
                    await this.handleAnswer(message.answer);
                    break;
                    
                case 'ice-candidate':
                    await this.handleIceCandidate(message.candidate);
                    break;
                    
                case 'stats':
                    this.updateStats(message.stats);
                    break;
                    
                default:
                    console.warn('🤷 未知信令消息类型:', message.type);
            }
        } catch (error) {
            console.error('❌ 处理信令消息失败:', error);
            this.callbacks.onError(error);
        }
    }
    
    /**
     * 开始通话
     */
    async startCall() {
        try {
            // 获取本地媒体流
            this.localStream = await navigator.mediaDevices.getUserMedia(
                this.config.mediaConstraints
            );
            
            // 添加本地流到PeerConnection
            this.localStream.getTracks().forEach(track => {
                this.peerConnection.addTrack(track, this.localStream);
            });
            
            // 创建数据通道
            this.dataChannel = this.peerConnection.createDataChannel('digitalHuman', {
                ordered: true
            });
            
            // 创建Offer
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);
            
            // 发送Offer
            this.sendSignalingMessage({
                type: 'offer',
                offer: offer
            });
            
            console.log('📞 开始通话');
        } catch (error) {
            console.error('❌ 开始通话失败:', error);
            this.callbacks.onError(error);
        }
    }
    
    /**
     * 处理Offer
     */
    async handleOffer(offer) {
        await this.peerConnection.setRemoteDescription(offer);
        
        // 创建Answer
        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);
        
        // 发送Answer
        this.sendSignalingMessage({
            type: 'answer',
            answer: answer
        });
    }
    
    /**
     * 处理Answer
     */
    async handleAnswer(answer) {
        await this.peerConnection.setRemoteDescription(answer);
    }
    
    /**
     * 处理ICE候选者
     */
    async handleIceCandidate(candidate) {
        await this.peerConnection.addIceCandidate(candidate);
    }
    
    /**
     * 发送信令消息
     */
    sendSignalingMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }
    
    /**
     * 发送文本消息给数字人
     */
    sendTextMessage(text) {
        if (this.dataChannel && this.dataChannel.readyState === 'open') {
            this.dataChannel.send(JSON.stringify({
                type: 'text',
                content: text,
                timestamp: Date.now()
            }));
        }
    }
    
    /**
     * 处理数据通道消息
     */
    handleDataChannelMessage(message) {
        switch (message.type) {
            case 'response':
                console.log('🤖 数字人响应:', message.content);
                break;
                
            case 'status':
                console.log('📊 系统状态:', message.status);
                break;
                
            default:
                console.log('📨 收到消息:', message);
        }
    }
    
    /**
     * 开始统计信息收集
     */
    startStatsCollection() {
        if (!this.config.enableStats) return;
        
        setInterval(async () => {
            try {
                const stats = await this.peerConnection.getStats();
                this.processStats(stats);
            } catch (error) {
                console.warn('⚠️ 获取统计信息失败:', error);
            }
        }, 1000);
    }
    
    /**
     * 处理统计信息
     */
    processStats(stats) {
        let inboundRtp = null;
        let outboundRtp = null;
        
        stats.forEach(report => {
            if (report.type === 'inbound-rtp' && report.kind === 'video') {
                inboundRtp = report;
            } else if (report.type === 'outbound-rtp' && report.kind === 'video') {
                outboundRtp = report;
            }
        });
        
        // 计算延迟
        if (inboundRtp) {
            this.stats.latency = inboundRtp.jitter || 0;
            this.stats.fps = inboundRtp.framesPerSecond || 0;
            this.stats.packetsLost = inboundRtp.packetsLost || 0;
        }
        
        // 计算比特率
        if (outboundRtp) {
            this.stats.bitrate = outboundRtp.bytesSent || 0;
        }
        
        this.callbacks.onStats(this.stats);
    }
    
    /**
     * 更新统计信息
     */
    updateStats(serverStats) {
        this.stats = { ...this.stats, ...serverStats };
        this.callbacks.onStats(this.stats);
    }
    
    /**
     * 设置回调函数
     */
    on(event, callback) {
        if (this.callbacks.hasOwnProperty(`on${event.charAt(0).toUpperCase() + event.slice(1)}`)) {
            this.callbacks[`on${event.charAt(0).toUpperCase() + event.slice(1)}`] = callback;
        }
    }
    
    /**
     * 结束通话
     */
    endCall() {
        // 关闭本地流
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        
        // 关闭PeerConnection
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }
        
        // 关闭WebSocket
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        
        console.log('📞 通话结束');
    }
    
    /**
     * 获取当前统计信息
     */
    getStats() {
        return { ...this.stats };
    }
    
    /**
     * 切换性能模式
     */
    async switchPerformanceMode(mode) {
        if (mode === this.config.performanceMode) return;
        
        this.config.performanceMode = mode;
        this.config.mediaConstraints = this.getMediaConstraints(mode);
        
        // 发送配置更新
        this.sendSignalingMessage({
            type: 'config-update',
            performanceMode: mode,
            mediaConstraints: this.config.mediaConstraints
        });
        
        console.log(`🔄 切换到${mode === 'quad' ? '4GPU' : '单GPU'}模式`);
    }
}

/**
 * 数字人WebRTC管理器
 */
class DigitalHumanManager {
    constructor() {
        this.webrtc = null;
        this.isConnected = false;
        this.currentMode = 'single';
        
        this.ui = {
            videoElement: null,
            statsElement: null,
            controlsElement: null
        };
    }
    
    /**
     * 初始化管理器
     */
    async init(config = {}) {
        try {
            // 检测GPU配置
            this.currentMode = await this.detectGPUMode();
            
            // 创建WebRTC实例
            this.webrtc = new DigitalHumanWebRTC({
                gpuMode: this.currentMode,
                ...config
            });
            
            // 设置事件监听器
            this.setupEventHandlers();
            
            // 初始化UI
            this.initUI();
            
            console.log(`🚀 数字人管理器初始化完成 (${this.currentMode}模式)`);
        } catch (error) {
            console.error('❌ 管理器初始化失败:', error);
            throw error;
        }
    }
    
    /**
     * 检测GPU模式
     */
    async detectGPUMode() {
        try {
            const response = await fetch('/api/system/gpu-info');
            const gpuInfo = await response.json();
            
            return gpuInfo.count >= 4 ? 'quad' : 'single';
        } catch (error) {
            console.warn('⚠️ 无法检测GPU配置，使用单GPU模式');
            return 'single';
        }
    }
    
    /**
     * 设置事件处理器
     */
    setupEventHandlers() {
        this.webrtc.on('connected', () => {
            this.isConnected = true;
            this.updateUI();
            console.log('✅ 数字人连接成功');
        });
        
        this.webrtc.on('disconnected', () => {
            this.isConnected = false;
            this.updateUI();
            console.log('❌ 数字人连接断开');
        });
        
        this.webrtc.on('remoteStream', (stream) => {
            if (this.ui.videoElement) {
                this.ui.videoElement.srcObject = stream;
            }
        });
        
        this.webrtc.on('stats', (stats) => {
            this.updateStats(stats);
        });
        
        this.webrtc.on('error', (error) => {
            console.error('❌ WebRTC错误:', error);
            this.showError(error.message);
        });
    }
    
    /**
     * 初始化UI
     */
    initUI() {
        // 查找UI元素
        this.ui.videoElement = document.getElementById('remoteVideo');
        this.ui.statsElement = document.getElementById('stats');
        this.ui.controlsElement = document.getElementById('controls');
        
        // 创建控制按钮
        this.createControls();
        
        // 创建统计面板
        this.createStatsPanel();
    }
    
    /**
     * 创建控制按钮
     */
    createControls() {
        if (!this.ui.controlsElement) return;
        
        const controls = `
            <div class="webrtc-controls">
                <button id="startCall" class="btn btn-success">开始通话</button>
                <button id="endCall" class="btn btn-danger" disabled>结束通话</button>
                <button id="switchMode" class="btn btn-info">切换模式</button>
                <input type="text" id="messageInput" placeholder="输入消息..." class="form-control" style="display:inline-block; width:300px; margin:0 10px;">
                <button id="sendMessage" class="btn btn-primary">发送</button>
            </div>
        `;
        
        this.ui.controlsElement.innerHTML = controls;
        
        // 绑定事件
        document.getElementById('startCall').onclick = () => this.startCall();
        document.getElementById('endCall').onclick = () => this.endCall();
        document.getElementById('switchMode').onclick = () => this.switchMode();
        document.getElementById('sendMessage').onclick = () => this.sendMessage();
    }
    
    /**
     * 创建统计面板
     */
    createStatsPanel() {
        if (!this.ui.statsElement) return;
        
        const statsPanel = `
            <div class="stats-panel">
                <h5>实时统计</h5>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">延迟:</span>
                        <span id="latencyStat">0ms</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">帧率:</span>
                        <span id="fpsStat">0fps</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">比特率:</span>
                        <span id="bitrateStat">0kbps</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">模式:</span>
                        <span id="modeStat">${this.currentMode === 'quad' ? '4GPU' : '单GPU'}</span>
                    </div>
                </div>
            </div>
        `;
        
        this.ui.statsElement.innerHTML = statsPanel;
    }
    
    /**
     * 开始通话
     */
    async startCall() {
        try {
            await this.webrtc.startCall();
            this.updateUI();
        } catch (error) {
            this.showError('开始通话失败: ' + error.message);
        }
    }
    
    /**
     * 结束通话
     */
    endCall() {
        this.webrtc.endCall();
        this.updateUI();
    }
    
    /**
     * 切换模式
     */
    async switchMode() {
        const newMode = this.currentMode === 'single' ? 'quad' : 'single';
        
        try {
            await this.webrtc.switchPerformanceMode(newMode);
            this.currentMode = newMode;
            this.updateUI();
        } catch (error) {
            this.showError('切换模式失败: ' + error.message);
        }
    }
    
    /**
     * 发送消息
     */
    sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (message) {
            this.webrtc.sendTextMessage(message);
            input.value = '';
        }
    }
    
    /**
     * 更新统计信息
     */
    updateStats(stats) {
        const elements = {
            latencyStat: `${Math.round(stats.latency)}ms`,
            fpsStat: `${Math.round(stats.fps)}fps`,
            bitrateStat: `${Math.round(stats.bitrate / 1000)}kbps`,
            modeStat: this.currentMode === 'quad' ? '4GPU' : '单GPU'
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }
    
    /**
     * 更新UI状态
     */
    updateUI() {
        const startBtn = document.getElementById('startCall');
        const endBtn = document.getElementById('endCall');
        
        if (startBtn && endBtn) {
            startBtn.disabled = this.isConnected;
            endBtn.disabled = !this.isConnected;
        }
    }
    
    /**
     * 显示错误信息
     */
    showError(message) {
        console.error('❌', message);
        // 这里可以添加UI错误提示
        alert('错误: ' + message);
    }
}

// 全局实例
window.digitalHumanManager = new DigitalHumanManager();

// 自动初始化（暂时禁用，等WebSocket端点实现后再启用）
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 暂时跳过WebRTC初始化，避免WebSocket连接错误
        console.log('⚠️ WebRTC功能暂时禁用，等待WebSocket端点实现');
        // await window.digitalHumanManager.init();
        // console.log('🎉 数字人WebRTC系统就绪');
    } catch (error) {
        console.error('💥 数字人系统初始化失败:', error);
    }
});