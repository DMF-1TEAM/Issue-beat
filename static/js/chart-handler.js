class IssuePulseChart {
    constructor() {
        this.chart = null;
        this.currentDate = null;
        this.chartData = null;
        this.initialize();
    }

    async initialize() {
        try {
            await this.loadChartData();
            this.renderChart();
            this.setupEventListeners();
        } catch (error) {
            console.error('차트 초기화 중 오류:', error);
        }
    }

    async loadChartData() {
        const response = await fetch('/api/daily-stats/');
        const data = await response.json();
        this.chartData = data.daily_counts;
    }

    renderChart() {
        const ctx = document.getElementById('timeline-chart').getContext('2d');
        
        // 심박수 스타일의 라인 설정
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.chartData.map(d => this.formatDate(d.date)),
                datasets: [{
                    data: this.chartData.map(d => d.count),
                    borderColor: '#3B82F6',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#3B82F6',
                    pointHoverBackgroundColor: '#2563EB'
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
                        enabled: true,
                        backgroundColor: 'rgba(255, 255, 255, 0.9)',
                        titleColor: '#1F2937',
                        bodyColor: '#1F2937',
                        borderColor: '#E5E7EB',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            title: (context) => `${context[0].label} 기사현황`,
                            label: (context) => `${context.raw}건의 기사`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 0,
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            font: {
                                size: 12
                            }
                        }
                    }
                },
                hover: {
                    mode: 'index',
                    intersect: false
                }
            }
        });
    }

    setupEventListeners() {
        this.chart.canvas.addEventListener('click', this.handleChartClick.bind(this));
        this.chart.canvas.addEventListener('mousemove', this.handleChartHover.bind(this));
    }

    async handleChartClick(event) {
        const points = this.chart.getElementsAtEventForMode(event, 'index', { intersect: true });
        
        if (points.length > 0) {
            const index = points[0].index;
            const date = this.chartData[index].date;
            this.currentDate = date;

            try {
                await Promise.all([
                    this.updateSummary(date),
                    this.updateNewsList(date),
                    summarizeNewsData(date)
                ]);

                // 활성 포인트 스타일 변경
                this.updateChartStyle(index);
            } catch (error) {
                console.error('데이터 업데이트 중 오류:', error);
            }
        }
    }

    async handleChartHover(event) {
        const points = this.chart.getElementsAtEventForMode(event, 'index', { intersect: false });
        
        if (points.length > 0) {
            const index = points[0].index;
            const date = this.chartData[index].date;
            
            try {
                const response = await fetch(`/api/daily-summary/${date}/`);
                const data = await response.json();
                this.updateHoverSummary(data);
            } catch (error) {
                console.error('호버 요약 업데이트 중 오류:', error);
            }
        }
    }

    async updateSummary(date) {
        const response = await fetch(`/api/daily-summary/${date}/`);
        const data = await response.json();
        
        const summaryElement = document.getElementById('daily-summary');
        summaryElement.innerHTML = `
            <div class="space-y-4">
                <div class="text-sm text-gray-600">
                    ${this.formatDate(date)} 주요 이슈
                </div>
                <div class="prose">
                    ${data.headlines.map((headline, index) => 
                        `<div class="mb-2 text-sm">${index + 1}. ${headline}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }

    async updateNewsList(date) {
        const response = await fetch(`/api/news/${date}/`);
        const data = await response.json();
        
        const newsListElement = document.getElementById('news-list');
        newsListElement.innerHTML = data.news.map(news => `
            <div class="border-b border-gray-200 py-4">
                <div class="flex items-center justify-between">
                    <h3 class="text-lg font-medium">${news.title}</h3>
                    <span class="text-sm text-gray-500">${news.press}</span>
                </div>
                <div class="mt-2 text-sm text-gray-600">
                    <span>${news.author}</span>
                    <a href="${news.link}" target="_blank" 
                       class="ml-4 text-blue-600 hover:text-blue-800">
                        원문 보기 →
                    </a>
                </div>
            </div>
        `).join('');
    }

    updateHoverSummary(data) {
        const hoverSummaryElement = document.getElementById('hover-summary');
        if (!hoverSummaryElement) return;

        hoverSummaryElement.innerHTML = `
            <div class="absolute z-10 bg-white p-4 rounded-lg shadow-lg border border-gray-200">
                <div class="text-sm font-medium mb-2">
                    ${this.formatDate(data.date)} 주요 키워드
                </div>
                <div class="flex flex-wrap gap-2">
                    ${data.keywords.map(keyword => 
                        `<span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                            ${keyword}
                         </span>`
                    ).join('')}
                </div>
            </div>
        `;
    }

    updateChartStyle(activeIndex) {
        this.chart.data.datasets[0].pointBackgroundColor = this.chartData.map((_, index) => 
            index === activeIndex ? '#2563EB' : '#3B82F6'
        );
        this.chart.data.datasets[0].pointRadius = this.chartData.map((_, index) => 
            index === activeIndex ? 6 : 4
        );
        this.chart.update();
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('ko-KR', {
            month: 'long',
            day: 'numeric'
        }).format(date);
    }
}

// 페이지 로드 시 차트 초기화
document.addEventListener('DOMContentLoaded', () => {
    new NewsPulseChart();
});