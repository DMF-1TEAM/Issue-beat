class IssuePulseChart {

    constructor() {
        this.chart = null;
        this.selectedDate = null;
        this.searchQuery = new URLSearchParams(window.location.search).get('query') || '';        
        this.initChart();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
        this.setupFilterEvent()
        // 이벤트 발생 시 데이터 전달을 위한 상태 추가
        this.currentState = {
            date: null,
            query: this.searchQuery
        }
    }

    // 차트 초기화
    initChart() {
        const ctx = document.getElementById('timeline-chart').getContext('2d');
        this.chart = new Chart(ctx, {
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
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'Count' } }
                }, 
            
            }
        });
    }

    fetchDataAndUpdateChart() {
        if (!this.searchQuery) {
            console.warn('검색어가 없습니다.');
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