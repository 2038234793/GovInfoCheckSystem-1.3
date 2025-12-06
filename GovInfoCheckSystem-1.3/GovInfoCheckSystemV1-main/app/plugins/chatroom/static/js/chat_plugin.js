class ChatClient {
    constructor(socket, nickname) {
        this.socket = socket;
        this.nickname = nickname;
        this.elements = {
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            aiBtn: document.getElementById('ai-btn'),
            onlineUsersContainer: document.getElementById('online-users-container'),
            onlineCount: document.getElementById('online-count'),
            notification: document.getElementById('notification'),
            notificationMessage: document.getElementById('notification-message')
        };
        
        this.initEvents();
        this.initSocket();
    }
    
    initEvents() {
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        this.elements.aiBtn.addEventListener('click', () => {
            const input = this.elements.messageInput;
            if (!input.value.startsWith('@AI ')) {
                input.value = '@AI ' + input.value;
            }
            input.focus();
        });
    }
    
    getAvatarHtml(name, bg = '1A3A5F', classes = 'w-8 h-8 rounded-full') {
        const initial = name ? name.charAt(0).toUpperCase() : '?';
        return `<div class="${classes} flex items-center justify-center text-white font-bold shrink-0" style="background-color: #${bg};">${initial}</div>`;
    }
    
    initSocket() {
        this.socket.on('connect', () => {
            console.log('Connected');
            this.socket.emit('join_room', { nickname: this.nickname });
        });
        
        this.socket.on('message', (data) => this.addMessage(data));
        
        this.socket.on('update_users', (data) => {
            this.updateUsers(data.users);
        });
        
        this.socket.on('history', (data) => {
            if (data.messages) {
                this.elements.chatMessages.innerHTML = ''; // Clear first
                data.messages.forEach(msg => this.addMessage(msg));
                this.scrollToBottom();
            }
        });

        // AI Streaming Events
        this.socket.on('ai_stream_chunk', (data) => {
            this.appendAiChunk(data);
        });
    }
    
    sendMessage() {
        const msg = this.elements.messageInput.value.trim();
        if (!msg) return;
        
        this.socket.emit('send_message', {
            nickname: this.nickname,
            message: msg
        });
        
        this.elements.messageInput.value = '';
    }
    
    addMessage(data) {
        // If this is an AI stream start message, create the bubble with ID
        if (data.type === 'ai_stream_start') {
            this.createAiBubble(data);
            return;
        }

        const div = document.createElement('div');
        
        if (data.type === 'system') {
            div.className = 'flex justify-center';
            div.innerHTML = `<span class="text-xs bg-dark text-muted px-3 py-1 rounded-full">${data.content} (${data.time})</span>`;
        } else if (data.type === 'music_card') {
            const cardId = `music-${Date.now()}`;
            div.className = 'flex items-end space-x-3';
            div.id = `msg-${cardId}`;
            div.innerHTML = `
                ${this.getAvatarHtml('Music', 'FF5722')}
                <div class="max-w-[70%]">
                    <div class="flex items-center mb-1">
                        <span class="text-xs text-white mr-2">音乐助手</span>
                        <span class="text-xs text-muted">${data.time}</span>
                    </div>
                    <div class="bg-card-hover rounded-t-lg rounded-br-lg p-3 overflow-hidden relative group">
                        <button onclick="document.getElementById('msg-${cardId}').remove()" class="absolute top-2 right-2 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <div class="flex flex-col gap-3">
                            <div class="flex items-center gap-3">
                                <img src="${data.content.image}" class="w-16 h-16 rounded object-cover bg-dark" onerror="this.src='https://ui-avatars.com/api/?name=Music&background=FF5722&color=fff'">
                                <div class="flex flex-col overflow-hidden">
                                    <span class="text-sm font-bold text-white truncate" title="${data.content.name}">${data.content.name}</span>
                                    <span class="text-xs text-gray-400 truncate" title="${data.content.singer}">${data.content.singer}</span>
                                </div>
                            </div>
                            <audio controls src="${data.content.url}" class="w-full h-8 rounded opacity-90 hover:opacity-100 transition-opacity"></audio>
                        </div>
                    </div>
                </div>
            `;
        } else if (data.type === 'chart_card') {
            const cardId = `chart-${Date.now()}`;
            div.className = 'flex items-end space-x-3';
            div.id = `msg-${cardId}`;
            div.innerHTML = `
                ${this.getAvatarHtml('Data', '00C48C')}
                <div class="max-w-[90%] w-[500px]">
                    <div class="flex items-center mb-1">
                        <span class="text-xs text-white mr-2">数据助手</span>
                        <span class="text-xs text-muted">${data.time}</span>
                    </div>
                    <div class="bg-card-hover rounded-t-lg rounded-br-lg p-4 border border-success/30 relative group">
                        <button onclick="document.getElementById('msg-${cardId}').remove()" class="absolute top-2 right-2 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity z-10">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <h4 class="text-sm font-bold text-white mb-3">${data.content.title}</h4>
                        <div id="chart-${cardId}" class="w-full h-64"></div>
                    </div>
                </div>
            `;
            // Render chart after insertion
            setTimeout(() => {
                const chartDom = document.getElementById(`chart-${cardId}`);
                if (chartDom) {
                    const myChart = echarts.init(chartDom);
                    const chartData = data.content.data;
                    let option = {};
                    
                    if (data.content.type === 'pie') {
                        option = {
                            tooltip: { trigger: 'item' },
                            legend: { top: '5%', left: 'center', textStyle: { color: '#ccc' } },
                            series: [{
                                name: '数据统计',
                                type: 'pie',
                                radius: ['40%', '70%'],
                                avoidLabelOverlap: false,
                                itemStyle: { borderRadius: 10, borderColor: '#2A2A40', borderWidth: 2 },
                                label: { show: false, position: 'center' },
                                emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold', color: '#fff' } },
                                labelLine: { show: false },
                                data: chartData
                            }]
                        };
                    } else {
                        option = {
                            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                            xAxis: { 
                                type: 'category', 
                                data: chartData.categories, 
                                axisTick: { alignWithLabel: true },
                                axisLabel: { color: '#ccc' }
                            },
                            yAxis: { 
                                type: 'value',
                                axisLabel: { color: '#ccc' },
                                splitLine: { lineStyle: { color: '#333' } }
                            },
                            series: [{
                                name: '数量',
                                type: 'bar',
                                barWidth: '60%',
                                data: chartData.values,
                                itemStyle: { color: '#00A3FF' }
                            }]
                        };
                    }
                    myChart.setOption(option);
                    
                    // Resize observer
                    new ResizeObserver(() => myChart.resize()).observe(chartDom);
                }
            }, 100);
        } else if (data.type === 'video_card') {
            const cardId = `video-${Date.now()}`;
            div.className = 'flex items-end space-x-3';
            div.id = `msg-${cardId}`;
            div.innerHTML = `
                ${this.getAvatarHtml('Movie', 'E91E63')}
                <div class="max-w-[80%]">
                    <div class="flex items-center mb-1">
                        <span class="text-xs text-white mr-2">影视助手</span>
                        <span class="text-xs text-muted">${data.time}</span>
                    </div>
                    <div class="bg-card-hover rounded-t-lg rounded-br-lg p-2 overflow-hidden relative group">
                        <button onclick="document.getElementById('msg-${cardId}').remove()" class="absolute top-2 right-2 text-gray-400 hover:text-white z-10 bg-black/50 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                        <iframe src="${data.content}" width="400" height="400" frameborder="0" allowfullscreen class="rounded bg-black"></iframe>
                    </div>
                </div>
            `;
        } else {
            const isMe = data.nickname === this.nickname;
            if (isMe) {
                div.className = 'flex items-end justify-end space-x-3';
                div.innerHTML = `
                    <div class="max-w-[70%]">
                        <div class="flex justify-end items-center mb-1">
                            <span class="text-xs text-muted">${data.time}</span>
                            <span class="text-xs text-accent ml-2">我</span>
                        </div>
                        <div class="bg-accent rounded-t-lg rounded-bl-lg p-3">
                            <p class="text-sm break-all">${data.content}</p>
                        </div>
                    </div>
                    ${this.getAvatarHtml(this.nickname, '0D8ABC')}
                `;
            } else {
                div.className = 'flex items-end space-x-3';
                div.innerHTML = `
                    ${this.getAvatarHtml(data.nickname, '1A3A5F')}
                    <div class="max-w-[70%]">
                        <div class="flex items-center mb-1">
                            <span class="text-xs text-white mr-2">${data.nickname}</span>
                            <span class="text-xs text-muted">${data.time}</span>
                        </div>
                        <div class="bg-card-hover rounded-t-lg rounded-br-lg p-3">
                            <p class="text-sm break-all">${data.content}</p>
                        </div>
                    </div>
                `;
            }
        }
        
        this.elements.chatMessages.appendChild(div);
        this.scrollToBottom();
    }

    createAiBubble(data) {
        const div = document.createElement('div');
        div.id = `msg-${data.id}`;
        div.className = 'flex items-end space-x-3';
        div.innerHTML = `
            ${this.getAvatarHtml('AI', '10B981')}
            <div class="max-w-[70%]">
                <div class="flex items-center mb-1">
                    <span class="text-xs text-white mr-2">AI助手</span>
                    <span class="text-xs text-muted">${data.time}</span>
                </div>
                <div class="bg-card-hover rounded-t-lg rounded-br-lg p-3">
                    <p class="text-sm break-all stream-content">正在思考...</p>
                </div>
            </div>
        `;
        this.elements.chatMessages.appendChild(div);
        this.scrollToBottom();
    }

    appendAiChunk(data) {
        const bubble = document.getElementById(`msg-${data.id}`);
        if (bubble) {
            const contentP = bubble.querySelector('.stream-content');
            if (contentP) {
                if (contentP.textContent === '正在思考...') {
                    contentP.textContent = '';
                }
                contentP.textContent += data.content;
                this.scrollToBottom();
            }
        }
    }
    
    updateUsers(users) {
        this.elements.onlineCount.textContent = `${users.length}人在线`;
        this.elements.onlineUsersContainer.innerHTML = users.map(user => `
            <div class="flex items-center space-x-3 p-2 hover:bg-card-hover rounded cursor-pointer transition-colors">
                <div class="relative">
                    ${this.getAvatarHtml(user, '1A3A5F')}
                    <span class="absolute bottom-0 right-0 w-2 h-2 bg-success rounded-full border border-dark"></span>
                </div>
                <span class="text-sm text-gray-300">${user}</span>
            </div>
        `).join('');
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    const nickname = document.getElementById('message-input').dataset.nickname;
    // Note: Connecting to namespace /chat
    const socket = io('/chat');
    new ChatClient(socket, nickname);
});
