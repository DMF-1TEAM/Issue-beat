// chart-handler.js

class IssuePulseChart {
    constructor() {
        this.chart = null;
        this.hoverTimeout = null;
        this.initialize();
    }

    async initialize() {
        try {
            await this.loadChartData();
            this.renderChart();
            this.setupEventListeners();  // 이벤트 리스너 설정 추가
            console.log('Chart initialized successfully');
        } catch (error) {
            console.error('Chart initialization error:', error);
        }
    }

    async loadChartData() {
        try {
            const response = await fetch('/api/stats/daily/');
            const data = await response.json();
            this.chartData = data.daily_counts;
            console.log('Chart data loaded:', this.chartData);
        } catch (error) {
            console.error('Error loading chart data:', error);
        }
    }

    setupEventListeners() {
        const canvas = document.getElementById('timeline-chart');
        if (!canvas) return;

        canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        canvas.addEventListener('mouseout', () => this.hideHoverSummary());
    }

    handleMouseMove(event) {
        if (this.hoverTimeout) {
            clearTimeout(this.hoverTimeout);
        }

        this.hoverTimeout = setTimeout(() => {
            const points = this.chart.getElementsAtEventForMode(
                event, 
                'nearest', 
                { intersect: true },
                false
            );

            if (points.length) {
                const point = points[0];
                const date = this.chartData[point.index].date;
                this.fetchAndShowSummary(date, event);
            } else {
                this.hideHoverSummary();
            }
        }, 100);
    }

    async fetchAndShowSummary(date, event) {
        try {
            console.log('Fetching summary for date:', date);
            const response = await fetch(`/api/news/hover-summary/${date}/`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Hover summary data:', data);
            this.showHoverSummary(data, event);
        } catch (error) {
            console.error('Error fetching summary:', error);
        }
    }

    renderChart() {
        const ctx = document.getElementById('timeline-chart');
        if (!ctx) return;

        const config = {
            type: 'line',
            data: {
                labels: this.chartData.map(d => d.date),
                datasets: [{
                    data: this.chartData.map(d => d.count),
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false  // 기본 툴팁 비활성화
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                }
            }
        };

        this.chart = new Chart(ctx, config);
    }

    showHoverSummary(data, event) {
        this.hideHoverSummary();

        const popup = document.createElement('div');
        popup.id = 'hover-summary';
        popup.className = 'fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-4 max-w-md w-80';
        
        popup.innerHTML = `
            <div class="space-y-4">
                ${data.image_url ? `
                    <div class="relative h-40 bg-gray-100 rounded overflow-hidden">
                        <img src="${data.image_url}" 
                             alt="뉴스 이미지" 
                             class="w-full h-full object-cover"
                             onerror="this.parentElement.style.display='none'"
                        />
                    </div>
                ` : ''}
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-semibold text-gray-900">
                            ${this.formatDate(data.date)}
                        </span>
                        <span class="text-sm text-gray-500">
                            ${data.news_count}건의 뉴스
                        </span>
                    </div>
                    <div class="space-y-2">
                        <p class="text-sm font-medium text-gray-900">
                            ${data.title_summary}
                        </p>
                        <p class="text-sm text-gray-600">
                            ${data.content_summary}
                        </p>
                    </div>
                    ${data.top_keywords?.length ? `
                        <div class="flex flex-wrap gap-1 pt-2">
                            ${data.top_keywords.map(keyword => `
                                <span class="px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded-full">
                                    ${keyword}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        document.body.appendChild(popup);
        this.positionPopup(popup, event);
    }

    hideHoverSummary() {
        const existing = document.getElementById('hover-summary');
        if (existing) {
            existing.remove();
        }
    }

    positionPopup(popup, event) {
        const padding = 16;
        const rect = popup.getBoundingClientRect();
        
        let left = event.clientX + padding;
        let top = event.clientY + padding;

        // 화면 경계 체크
        if (left + rect.width > window.innerWidth) {
            left = event.clientX - rect.width - padding;
        }
        if (top + rect.height > window.innerHeight) {
            top = event.clientY - rect.height - padding;
        }

        // 최소 여백 확보
        left = Math.max(padding, left);
        top = Math.max(padding, top);

        popup.style.left = `${left}px`;
        popup.style.top = `${top}px`;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing IssuePulseChart...');
    window.issuePulseChart = new IssuePulseChart();
});