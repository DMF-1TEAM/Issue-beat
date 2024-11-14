class IssuePulseChart {
    constructor() {
        // 기본 상태 초기화
        this.chart = null;
        this.groupBy = '1day';
        this.selectedDate = null;
        this.searchQuery = new URLSearchParams(window.location.search).get('query') || '';        
        this.initChart();
        this.setupEventListeners();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
        this.setupFilterEvent()
        // 이벤트 발생 시 데이터 전달을 위한 상태 추가
        this.currentState = {
            date: null,
            query: this.searchQuery
        }
    }

    
    // 초기화 처리를 위한 간단한 메서드 추가
    handleReset() {
        // URL에서 query만 유지하고 페이지 새로고침
        const searchParams = new URLSearchParams();
        searchParams.set('query', this.searchQuery);
        window.location.href = `${window.location.pathname}?${searchParams.toString()}`;
    }

    initChart() {
        const ctx = document.getElementById('timeline-chart').getContext('2d');
        if (this.chart) {
            this.chart.destroy();
            this.tooltipCache.clear();
            this.clearActiveTooltip();
        }

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
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: true,
                    mode: 'point'
                },
                onClick: this.handleChartClick.bind(this),
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false,
                        external: this.handleTooltip.bind(this)
                    }
                },
                scales: {
                    x: { 
                        grid: { display: false },
                        ticks: { font: { size: 12 } }
                    },
                    y: { 
                        beginAtZero: true,
                        ticks: { font: { size: 12 } }
                    }
                }
            }
        });
    }

    async handleChartClick(event, elements) {
        if (!elements || !elements.length) return;
        
        const element = elements[0];
        const date = this.chart.data.labels[element.index];
        const dateObj = new Date(date);
        
        // 날짜 범위 계산
        let startDate = new Date(date);
        let endDate = new Date(date);

        if (this.groupBy === '1week') {
            startDate.setDate(dateObj.getDate() - dateObj.getDay() + 1);
            endDate.setDate(startDate.getDate() + 6);
        } else if (this.groupBy === '1month') {
            startDate = new Date(dateObj.getFullYear(), dateObj.getMonth(), 1);
            endDate = new Date(dateObj.getFullYear(), dateObj.getMonth() + 1, 0);
        }

        // 이벤트 발생 및 URL 업데이트
        const clickEvent = new CustomEvent('chartDateClick', {
            detail: { 
                date,
                query: this.searchQuery,
                groupBy: this.groupBy,
                startDate: startDate.toISOString().split('T')[0],
                endDate: endDate.toISOString().split('T')[0]
            }
        });
        document.dispatchEvent(clickEvent);

        this.updateURL({
            date,
            startDate: startDate.toISOString().split('T')[0],
            endDate: endDate.toISOString().split('T')[0]
        });
    }

    async handleTooltip(context) {
        const { chart, tooltip } = context;
        
        if (tooltip.opacity === 0) {
            this.clearActiveTooltip();
            return;
        }

        fetch(`/api/v2/news/chart/?query=${encodeURIComponent(searchQuery)}&group_by=${this.groupBy}`)
            .then(response => response.json())
            .then(data => {
                console.log('차트 데이터:', data);
                if (Array.isArray(data)) {
                    const dates = data.map(item => item.date);
                    const counts = data.map(item => item.count);
                    
                    // 차트 업데이트
                    this.chart.data.labels = dates;
                    this.chart.data.datasets[0].data = counts;
                    this.chart.update();
                } else {
                    console.error("데이터 형식 오류:", data);
                }
            })
            .catch(error => console.error('차트 데이터 가져오기 오류:', error));
    }

    setupClickEvent() {
        let clickTimeout;

        this.chart.canvas.onclick = (evt) => {
            const points = this.chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);

            if (points.length) {          
                const firstPoint = points[0];
                const date = this.chart.data.labels[firstPoint.index];

                // 이전 상태와 비교
                if (this.currentState.date === date) {
                    return; // 같은 날짜 중복 클릭 방지
                }
                
                this.currentState.date = date;

                // 디바운싱 적용
                if (clickTimeout) {
                    clearTimeout(clickTimeout);
                }
                
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
        // 필터 html 요소 가져오기
        const filterSelect = document.getElementById('date_filter');
        console.log("add event")

        // #date_filter가 존재하는지 확인
        if (filterSelect) {
            filterSelect.addEventListener("change", (event) => {
                this.groupBy = event.target.value;  // 선택된 필터값을 groupBy에 저장
                this.fetchDataAndUpdateChart();     // 필터에 맞춰 차트 데이터를 업데이트
            });
        } else {
            console.error("#date_filter 요소를 찾을 수 없습니다.");
        }
    }
}