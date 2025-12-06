// Dashboard Logic

// Charts Instances
let pieChart, barChart, mapChart;
let currentMapType = '2d'; // '2d' or '3d'

document.addEventListener('DOMContentLoaded', function() {
    initClock();
    initCharts();
    loadData();
    
    // Resize listener
    window.addEventListener('resize', function() {
        pieChart && pieChart.resize();
        barChart && barChart.resize();
        mapChart && mapChart.resize();
    });

    // AI Button
    document.getElementById('refresh-ai').addEventListener('click', loadAIReport);
});

function initClock() {
    const clock = document.getElementById('clock');
    setInterval(() => {
        const now = new Date();
        clock.innerText = now.toLocaleTimeString('zh-CN', { hour12: false });
    }, 1000);
}

function initCharts() {
    // Pie Chart
    pieChart = echarts.init(document.getElementById('pieChart'));
    pieChart.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: '0%', left: 'center', textStyle: { color: '#ccc' } },
        series: [{
            name: '来源',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '45%'],
            itemStyle: { borderRadius: 5 },
            label: { show: false },
            data: [] // To be filled
        }]
    });

    // Bar Chart
    barChart = echarts.init(document.getElementById('barChart'));
    barChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { top: '10%', bottom: '15%', left: '10%', right: '5%' },
        xAxis: { 
            type: 'category', 
            data: [], 
            axisLine: { lineStyle: { color: '#555' } },
            axisLabel: { color: '#ccc' }
        },
        yAxis: { 
            type: 'value', 
            splitLine: { lineStyle: { color: '#333' } },
            axisLabel: { color: '#ccc' }
        },
        series: [{
            data: [],
            type: 'bar',
            itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#3b82f6' },
                    { offset: 1, color: '#1d4ed8' }
                ])
            }
        }]
    });

    // Map Chart
    mapChart = echarts.init(document.getElementById('mapContainer'));
    render2DMap([]);
}

function render2DMap(data) {
    mapChart.clear();
    const option = {
        tooltip: { trigger: 'item' },
        visualMap: {
            min: 0,
            max: 500, // Adjust dynamically if needed
            left: 'left',
            top: 'bottom',
            text: ['高', '低'],
            calculable: true,
            inRange: {
                color: ['#1e3a8a', '#3b82f6', '#60a5fa', '#93c5fd']
            },
            textStyle: { color: '#fff' }
        },
        geo: {
            map: 'china',
            roam: true,
            label: { emphasis: { show: true, color: '#fff' } },
            itemStyle: {
                normal: {
                    areaColor: '#1e293b',
                    borderColor: '#3b82f6'
                },
                emphasis: {
                    areaColor: '#2563eb'
                }
            }
        },
        series: [{
            name: '舆情热度',
            type: 'map',
            geoIndex: 0,
            data: data
        }]
    };
    mapChart.setOption(option);
}

function render3DEarth(data) {
    mapChart.clear();
    
    // Local Assets Path
    var ASSET_PATH = '/plugins/dashboard/static/assets/';
    
    const option = {
        backgroundColor: '#000',
        globe: {
            baseTexture: ASSET_PATH + 'world.topo.bathy.200401.jpg',
            heightTexture: ASSET_PATH + 'bathymetry_bw_composite_4k.jpg',
            displacementScale: 0.2,
            shading: 'realistic',
            environment: ASSET_PATH + 'starfield.jpg',
            // realisticMaterial: {
            //     roughness: ASSET_PATH + 'roughness.jpg',
            //     metalness: ASSET_PATH + 'metalness.jpg',
            //     textureTiling: [8, 4]
            // },
            postEffect: {
                enable: true
            },
            viewControl: {
                autoRotate: true,
                autoRotateSpeed: 5
            },
            light: {
                main: {
                    intensity: 2,
                    shadow: true
                },
                ambientCubemap: {
                    texture: ASSET_PATH + 'pisa.hdr',
                    exposure: 2,
                    diffuseIntensity: 2,
                    specularIntensity: 2
                }
            }
        },
        series: []
    };

    mapChart.setOption(option);
}

function switchMap(type) {
    currentMapType = type;
    fetch('/plugins/dashboard/api/map_data')
        .then(res => res.json())
        .then(data => {
            if (type === '2d') {
                render2DMap(data);
            } else {
                render3DEarth(data);
            }
        });
}

let scrollInterval;
let newsData = [];

function refreshNews() {
    const btn = document.getElementById('refresh-news-btn');
    const icon = btn.querySelector('i');
    const keywordInput = document.getElementById('ai-keyword');
    const keyword = keywordInput ? keywordInput.value.trim() : '';
    
    // Animate button
    icon.classList.add('fa-spin');
    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    
    // Trigger crawl first
    fetch('/plugins/dashboard/api/refresh_news', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ keyword: keyword })
    })
    .then(res => res.json())
    .then(data => {
        console.log('Crawl result:', data);
        // Then fetch stats
        return fetchStats(keyword);
    })
    .catch(err => {
        console.error('Network error:', err);
    })
    .finally(() => {
        setTimeout(() => {
            icon.classList.remove('fa-spin');
            btn.disabled = false;
            btn.classList.remove('opacity-50', 'cursor-not-allowed');
        }, 500);
    });
}

function fetchStats(keyword = '') {
    return fetch(`/plugins/dashboard/api/stats?keyword=${encodeURIComponent(keyword)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) return;
            updateDashboardUI(data);
        });
}

function updateDashboardUI(data) {
    // Update Stats
    if(document.getElementById('stat-total')) document.getElementById('stat-total').innerText = data.total;
    if(document.getElementById('stat-today')) document.getElementById('stat-today').innerText = Math.floor(Math.random() * 50); // Mock
    if(document.getElementById('stat-warning')) document.getElementById('stat-warning').innerText = Math.floor(Math.random() * 10); // Mock
    if(document.getElementById('stat-provinces')) document.getElementById('stat-provinces').innerText = 34;

    // Update Charts
    if(pieChart) pieChart.setOption({ series: [{ data: data.pie_data }] });
    
    if(barChart) {
        barChart.setOption({
            xAxis: { data: data.bar_data.categories },
            series: [{ data: data.bar_data.values }]
        });
    }

    // Update List with Scroll
    newsData = data.list_data;
    renderNewsList();
    startScroll();
    
    // Update timer
    const timer = document.getElementById('refresh-timer');
    if(timer) {
        const now = new Date();
        timer.innerText = `更新于 ${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;
    }
}

function loadData() {
    fetchStats();
        
    // Load initial map data
    switchMap('2d');
}

function renderNewsList() {
    const listEl = document.getElementById('newsList');
    if (!listEl) return;
    
    if (!newsData || newsData.length === 0) {
        listEl.innerHTML = '<div class="text-gray-500 text-center py-4 text-sm">暂无实时资讯<br><span class="text-xs opacity-60">点击右上角刷新按钮采集</span></div>';
        return;
    }

    listEl.innerHTML = newsData.map((item, index) => `
        <div class="p-3 mb-2 bg-white/5 rounded hover:bg-white/10 transition cursor-pointer border-l-2 border-blue-500/0 hover:border-blue-500"
             onclick="showNewsDetail(${index})">
            <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span class="px-2 py-0.5 bg-blue-900/50 rounded text-blue-300 truncate max-w-[100px]">${item.source}</span>
                <span>${item.time}</span>
            </div>
            <div class="text-sm line-clamp-2 font-medium text-gray-200">${item.title}</div>
        </div>
    `).join('');
}

function startScroll() {
    const container = document.getElementById('newsList');
    const parent = document.getElementById('news-scroll-container');
    if (!container || !parent) return;

    // Reset
    clearInterval(scrollInterval);
    container.style.transform = 'translateY(0)';
    
    // Clone items if not enough to scroll
    if (container.scrollHeight <= parent.clientHeight) return;

    // Infinite Scroll Logic
    let currentY = 0;
    scrollInterval = setInterval(() => {
        currentY -= 0.5; // Speed
        if (Math.abs(currentY) >= container.scrollHeight / 2) {
             // Logic for seamless loop would require cloning items. 
             // For simplicity, just reset when bottom reached or use a simpler approach:
             // Let's duplicate list content once for seamless effect
        }
        container.style.transform = `translateY(${currentY}px)`;
        
        // Reset when end reached (simple loop)
        if (Math.abs(currentY) >= (container.scrollHeight - parent.clientHeight)) {
            currentY = 0;
             // Pause briefly at top?
        }
    }, 50);

    // Pause on hover
    parent.addEventListener('mouseenter', () => clearInterval(scrollInterval));
    parent.addEventListener('mouseleave', () => {
        // Restart logic needs careful state management, simplified here:
        // Just restart the interval
        scrollInterval = setInterval(() => {
             currentY -= 0.5;
             if (Math.abs(currentY) >= (container.scrollHeight - parent.clientHeight)) currentY = 0;
             container.style.transform = `translateY(${currentY}px)`;
        }, 50);
    });
}

function showNewsDetail(index) {
    const item = newsData[index];
    if (!item) return;
    
    document.getElementById('modal-title').innerText = item.title;
    document.getElementById('modal-source').innerText = item.source;
    document.getElementById('modal-time').innerText = item.time;
    document.getElementById('modal-content').innerText = item.content || '暂无详细内容';
    document.getElementById('modal-link').href = item.url;
    
    document.getElementById('news-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('news-modal').classList.add('hidden');
}

// Auto Refresh
setInterval(() => {
    const timer = document.getElementById('refresh-timer');
    if(timer) timer.innerText = '刷新中...';
    
    fetchStats();
}, 60000); // Every 60s


function loadAIReport() {
    const container = document.getElementById('ai-content');
    const btn = document.getElementById('refresh-ai');
    const keywordInput = document.getElementById('ai-keyword');
    const keyword = keywordInput ? keywordInput.value.trim() : '';
    
    container.innerHTML = '<div class="flex items-center justify-center h-full text-blue-400"><i class="fas fa-spinner fa-spin mr-2"></i> 分析中...</div>';
    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    btn.classList.remove('animate-pulse'); // Stop pulsing while loading

    fetch('/plugins/dashboard/api/ai_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keyword: keyword })
    })
    .then(res => res.json())
    .then(data => {
        if (data.report) {
            container.innerHTML = data.report;
        } else if (data.error) {
            container.innerHTML = `<div class="text-red-400 p-4 text-center"><p class="font-bold mb-2">生成失败</p><p class="text-xs opacity-80">${data.error}</p></div>`;
        } else {
            container.innerHTML = '<div class="text-red-400 text-center">生成报告失败：未知错误</div>';
        }
    })
    .catch(err => {
        console.error(err);
        container.innerHTML = `<div class="text-red-400 text-center"><p>网络请求错误</p><p class="text-xs opacity-80">${err.message}</p></div>`;
    })
    .finally(() => {
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
        btn.classList.add('animate-pulse');
    });
}
