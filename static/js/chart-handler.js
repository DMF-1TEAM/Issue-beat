class IssuePulseChart {
    constructor() {
        this.chart = null;
        this.groupBy = '1day';
        this.selectedDate = null;
        this.searchQuery = new URLSearchParams(window.location.search).get('query') || '';
        this.tooltipCache = new Map(); // 요약 데이터 캐시
        this.currentState = {
            date: null,
            query: this.searchQuery
        };
        
        this.initChart();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
        this.setupFilterEvent();
    }

    initChart() {
        const ctx = document.getElementById('timeline-chart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        Chart.defaults.font.family = 'Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif';

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: '기사 수',
                    data: [],
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointHitRadius: 10 // 클릭/호버 감지 영역 크기
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: true,  // 변경: 정확히 점과 교차할 때만 이벤트 발생
                    mode: 'point'     // 변경: point 모드로 설정
                },
                scales: {
                    x: { 
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: { 
                        beginAtZero: true,
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false,
                        external: async (context) => {
                            const {chart, tooltip} = context;
                            
                            // 툴팁이 표시되지 않아야 하는 경우
                            if (tooltip.opacity === 0) {
                                const tooltipEl = chart.canvas.parentNode.querySelector('div.chartjs-tooltip');
                                if (tooltipEl) {
                                    tooltipEl.style.opacity = '0';
                                }
                                return;
                            }

                            // 데이터 포인트가 없는 경우
                            if (!tooltip.dataPoints || !tooltip.dataPoints.length) {
                                return;
                            }

                            let tooltipEl = chart.canvas.parentNode.querySelector('div.chartjs-tooltip');

                            // 툴팁 요소 생성
                            if (!tooltipEl) {
                                tooltipEl = document.createElement('div');
                                tooltipEl.className = 'chartjs-tooltip';
                                tooltipEl.style.opacity = '0';
                                tooltipEl.style.position = 'fixed';
                                tooltipEl.style.pointerEvents = 'none';
                                tooltipEl.style.transition = 'all 0.15s ease';
                                tooltipEl.style.maxWidth = '300px';
                                tooltipEl.style.minWidth = '200px';
                                chart.canvas.parentNode.appendChild(tooltipEl);
                            }

                            const dataPoint = tooltip.dataPoints[0];
                            const date = dataPoint.label;
                            const count = dataPoint.raw;

                            // 캐시된 데이터 확인
                            const cachedData = this.tooltipCache.get(date);
                            if (cachedData) {
                                this.updateTooltipContent(tooltipEl, date, cachedData);
                                this.positionTooltip(tooltipEl, context);
                                return;
                            }

                            // 기본 로딩 상태 표시
                            tooltipEl.innerHTML = `
                                <div class="bg-white shadow-lg rounded-lg border border-gray-200 p-4">
                                    <div class="flex justify-between items-center mb-2">
                                        <span class="font-bold">${date}</span>
                                        <span class="text-blue-600">뉴스 ${count}건</span>
                                    </div>
                                    <div class="text-sm text-gray-500">로딩중...</div>
                                </div>
                            `;

                            this.positionTooltip(tooltipEl, context);
                            tooltipEl.style.opacity = '1';

                            // API 호출
                            try {
                                const response = await fetch(`/api/v2/news/hover-summary/${date}/?query=${encodeURIComponent(this.searchQuery)}`);
                                const summaryData = await response.json();
                                
                                this.tooltipCache.set(date, summaryData);
                                this.updateTooltipContent(tooltipEl, date, summaryData);
                            } catch (error) {
                                console.error('Error fetching summary:', error);
                            }
                        }
                    }
                }
            }
        });
    }

    positionTooltip(tooltipEl, context) {
        const position = context.chart.canvas.getBoundingClientRect();
        const mouseX = position.left + context.tooltip.caretX;
        const mouseY = position.top + context.tooltip.caretY;
        
        // 툴팁이 화면 오른쪽을 벗어나지 않도록 조정
        const tooltipWidth = tooltipEl.offsetWidth;
        const windowWidth = window.innerWidth;
        let xPosition = mouseX + 10;

        if (mouseX + tooltipWidth + 10 > windowWidth) {
            xPosition = mouseX - tooltipWidth - 10;
        }

        tooltipEl.style.left = `${xPosition}px`;
        tooltipEl.style.top = `${mouseY - tooltipEl.offsetHeight - 10}px`;
    }

    updateTooltipContent(tooltipEl, date, summaryData) {
        if (summaryData.title_summary && summaryData.title_summary !== '요약 없음') {
            tooltipEl.innerHTML = `
                <div class="bg-white shadow-lg rounded-lg border border-gray-200 p-4">
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-bold">${date}</span>
                        <span class="text-blue-600">뉴스 ${summaryData.news_count}건</span>
                    </div>
                    <div class="text-sm font-medium text-gray-900">
                        ${summaryData.title_summary}
                    </div>
                    <div class="text-sm text-gray-600 mt-1">
                        ${summaryData.content_summary}
                    </div>
                </div>
            `;
        }
    }

    async fetchDataAndUpdateChart() {
        if (!this.searchQuery) return;

        try {
            const response = await fetch(`/api/v2/news/chart/?query=${encodeURIComponent(this.searchQuery)}&group_by=${this.groupBy}`);
            const data = await response.json();

            if (Array.isArray(data)) {
                this.chart.data.labels = data.map(item => item.date);
                this.chart.data.datasets[0].data = data.map(item => item.count);
                this.chart.update('none'); // 성능 최적화
            }
        } catch (error) {
            console.error('Error fetching chart data:', error);
        }
    }

    setupClickEvent() {
        let clickTimeout;
        
        this.chart.canvas.onclick = (evt) => {
            const points = this.chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);

            if (points.length) {
                const firstPoint = points[0];
                const date = this.chart.data.labels[firstPoint.index];

                if (this.currentState.date === date) return;
                
                this.currentState.date = date;

                if (clickTimeout) clearTimeout(clickTimeout);
                
                clickTimeout = setTimeout(() => {
                    const clickEvent = new CustomEvent('chartDateClick', {
                        detail: { 
                            date,
                            query: this.searchQuery 
                        }
                    });
                    document.dispatchEvent(clickEvent);

                    const searchParams = new URLSearchParams(window.location.search);
                    searchParams.set('date', date);
                    const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
                    window.history.pushState({}, '', newUrl);
                }, 300);
            }
        };
    }

    setupFilterEvent() {
        const filterSelect = document.getElementById('date_filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', (event) => {
                this.groupBy = event.target.value;
                this.fetchDataAndUpdateChart();
            });
        }
    }
}

// DOM 로드 완료 후 차트 초기화
document.addEventListener('DOMContentLoaded', () => {
    new IssuePulseChart();
});