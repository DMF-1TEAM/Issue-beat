class IssuePulseChart {

    constructor() {
        this.chart = null;
        this.selectedDate = null; 
        this.groupBy = '1day';      // groupBy 추가
        this.initChart();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
        this.setupFilterEvent();
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

    // 차트 데이터 api 호출
    fetchDataAndUpdateChart() {
        // groupby 추가
        fetch(`/api/v2/news/chart/?query=${encodeURIComponent(searchQuery)}&group_by=${this.groupBy}`)
            .then(response => response.json())
            .then(data => {
                console.log(data);

                // 응답 데이터가 배열임을 확인 
                if (Array.isArray(data)) {
                    // 차트 처리 코드
                    const dates = data.map(item => item.date);
                    const counts = data.map(item => item.count);

                    // 차트 업데이트
                    this.chart.data.labels = dates;
                    this.chart.data.datasets[0].data = counts;
                    this.chart.update();
                } else {
                    console.error("Data irmsep s not an array:", data);
                }
                
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
    }
    
    // 필터링 이벤트 설정
    setupFilterEvent() {
        // 필터 html 요소 가져오기
        const filterSelect = document.getElementById('date_filter');
        
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

