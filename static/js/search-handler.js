class SearchHandler {
    constructor() {
        console.log('SearchHandler initialized');
        this.searchForm = document.getElementById('search-form');
        this.searchInput = document.getElementById('search-input');
        this.summarySection = document.getElementById('summary-section');
        this.chart = null;
        this.issueListHandler = new IssueListHandler();

        this.initialize();
    }

    initialize() {
        console.log('Initializing search handler...');
        if (searchQuery) {  // 전역 변수로 전달받은 검색어
            console.log('Search query found:', searchQuery);
            this.handleSearch(searchQuery);
        }
    }

    async handleSearch(query) {
        try {
            // console.log(query)
            this.issueListHandler.searchQuery = query

            console.log('Handling search for:', query);
            this.showLoading();
            const response = await fetch(`/api/news/search/?query=${encodeURIComponent(query)}`);
            console.log('Search response:', response);
            const data = await response.json();
            console.log('Search data:', data);
            
            if (!response.ok) {
                throw new Error(data.error || '검색 중 오류가 발생했습니다.');
            }

            // // 요약 업데이트
            // if (data.summary) {
            //     this.updateSummary(data.summary);
            // }

            // // 차트 업데이트
            // if (data.daily_counts) {
            //     this.initializeChart(data.daily_counts);
            // }
            
            // 뉴스 목록 업데이트
            if (this.issueListHandler) {
                await this.issueListHandler.handleSearch(query);
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }


    async handleChartClick(event, elements) {
        console.log("=====click!!!!!!!!!!=====")
        if (!elements || elements.length === 0) return;

        const index = elements[0].index;
        const date = this.chart.data.labels[index];

        try {
            const response = await fetch(`/api/news/summary/${date}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '데이터를 불러오는 중 오류가 발생했습니다.');
            }

            this.updateSummary(data.summary);
            await this.issueListHandler.handleDateClick(date);

        } catch (error) {
            this.showError(error.message);
        }
    }

    updateSummary(summary) {
        if (!this.summarySection) {
            console.log('Summary section not found');
            return;
        }
    
        // summary가 undefined인 경우 처리
        if (!summary) {
            summary = {
                background: '요약 정보를 불러오는데 실패했습니다.',
                core_content: '요약 정보를 불러오는데 실패했습니다.',
                conclusion: '요약 정보를 불러오는데 실패했습니다.'
            };
        }
    
        console.log('Updating summary section with:', summary);
        
        // HTML 업데이트
        const backgroundElem = document.getElementById('summary-level-1');
        const mainContentElem = document.getElementById('summary-level-2');
        const currentStatusElem = document.getElementById('summary-level-3');
    
        if (backgroundElem) {
            backgroundElem.textContent = summary.background || '정보 없음';
        }
        if (mainContentElem) {
            mainContentElem.textContent = summary.core_content || '정보 없음';
        }
        if (currentStatusElem) {
            currentStatusElem.textContent = summary.conclusion || '정보 없음';
        }
    }

    initializeChart(dailyCounts) {
        const ctx = document.getElementById('timeline-chart');
        if (!ctx) {
            console.log('Chart context not found');
            return;
        }
    
        if (this.chart) {
            this.chart.destroy();
        }
    
        // 데이터 정렬
        const sortedDates = Object.keys(dailyCounts).sort();
        const counts = sortedDates.map(date => dailyCounts[date]);
    
        console.log('Chart data:', { dates: sortedDates, counts });
    
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sortedDates,
                datasets: [{
                    data: counts,
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
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10 // x축 레이블 수 제한
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0 // 정수로 표시
                        }
                    }
                }
            }
        });
    }


    showLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        setTimeout(() => errorDiv.remove(), 3000);
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    const searchHandler = new SearchHandler();
});