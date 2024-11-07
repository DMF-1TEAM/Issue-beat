class IssuePulseChart {

    constructor() {
        this.chart = null;
<<<<<<< HEAD
        this.selectedDate = null; 
        this.initChart();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
    }

    // 차트 초기화
    initChart() {
        const ctx = document.getElementById('timeline-chart').getContext('2d');
        this.chart = new Chart(ctx, {
=======
        this.hoverTimeout = null;
        this.chartData = null;
        this.initialize();
    }

    async initialize() {
        try {
            console.log('Initializing IssuePulseChart...');
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
        if (!canvas) {
            console.error('Chart canvas not found');
            return;
        }

        // 마우스 이벤트 리스너 추가
        canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        canvas.addEventListener('mouseout', () => this.hideHoverSummary());
    }

    handleMouseMove(event) {
        // 디바운싱 처리
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
        }, 100); // 100ms 딜레이
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
>>>>>>> master
            type: 'line',
            data: {
                labels: [], // 일자
                datasets: [{
                    label: '기사 수',
                    data: [], // 기사 수 데이터
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
                scales: {
<<<<<<< HEAD
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'Count' } }
                }, 
            
            }
        });
    }

    // 차트 데이터 api 호출
    fetchDataAndUpdateChart() {
        fetch(`/api/v2/news/chart/?query=${encodeURIComponent(searchQuery)}`)
            .then(response => response.json())
            .then(data => {

                console.log(data);
                if (Array.isArray(data)) {
                    const chartData = data.map(item => item.count);
                    // 차트 처리 코드
                } else {
                    console.error("Data is not an array:", data);
=======
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
>>>>>>> master
                }
                
                const dates = data.map(item => item.date);
                const counts = data.map(item => item.count);

  
                // 차트 업데이트
                this.chart.data.labels = dates;
                this.chart.data.datasets[0].data = counts;
                this.chart.update();
            })
            .catch(error => console.error('Error fetching chart data:', error));
    }

    // 클릭 이벤트 설정
    setupClickEvent() {
        this.chart.canvas.onclick = (evt) => {

            // 클릭 위치와 가장 가까운 데이터 포인트 찾음.
            const points = this.chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
            console.log(points)

            // 포인터가 있으면
            if (points.length) {          
                const firstPoint = points[0];
                console.log(firstPoint)
                const date = this.chart.data.labels[firstPoint.index];
                
                // 커스텀 이벤트 발생시키기만 함
                const clickEvent = new CustomEvent('chartDateClick', {
                    detail: { date }
                });
                document.dispatchEvent(clickEvent);    // 다른 스크립트에서 document.addEventListener를 통해 실행
                
                // URL 업데이트
                const searchParams = new URLSearchParams(window.location.search);       // 현재 url 쿼리를 문자열을 객체화
                searchParams.set('date', date);                                         // url 쿼리에 date를 붙임 ex) /?query=의대&date=2024-11-07
                const newUrl = `${window.location.pathname}?${searchParams.toString()}`;  // 새로운 url 쿼리 형성  
                window.history.pushState({}, '', newUrl);                                 // 새로고침 없이 url 동적 변경
            }
        };
<<<<<<< HEAD
    
=======

        this.chart = new Chart(ctx, config);
    }

    showHoverSummary(data, event) {
        this.hideHoverSummary(); // 기존 팝업 제거

        const popup = document.createElement('div');
        popup.id = 'hover-summary';
        popup.className = 'fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 p-4 max-w-sm';
        
        popup.innerHTML = `
            <div class="space-y-4">
                ${data.image_url ? `
                    <div class="relative h-32 bg-gray-100 rounded overflow-hidden">
                        <img src="${data.image_url}" 
                             alt="뉴스 이미지" 
                             class="w-full h-full object-cover"
                             onerror="this.parentElement.style.display='none'"
                        />
                    </div>
                ` : ''}
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="text-sm font-medium text-gray-900">
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
>>>>>>> master
    }
}

