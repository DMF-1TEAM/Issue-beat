class IssuePulseChart {
    constructor() {

        // 객체가 처음 생성될 때 가져오는 초기값
        this.chart = null;
        this.startDate = document.getElementById("start_date").value;        // 날짜 범위 생성
        this.endDate = document.getElementById("end_date").value;            // 날짜 범위 생성
        this.groupBy="1day";                                                // 날짜 기준 집계
        this.selectedDate = null;                                           // 특정 일자 클릭
        this.searchQuery = new URLSearchParams(window.location.search).get('query') || '';        
        
        this.initChart();
        this.fetchDataAndUpdateChart();
        this.setupClickEvent();
        this.setupFilterEvent();
        this.setupDateRangeEvent();
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

    // chart api에 데이터 요청
    fetchDataAndUpdateChart() {
        if (!this.searchQuery) {
            console.warn('검색어가 없습니다.');
            return;
        }

        // 변화된 새로운 값으로 업데이트
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;
        const groupBy = document.getElementById('group_by').value;

        // URL 로그 출력
        const url = `/api/v2/news/chart/?query=${encodeURIComponent(this.searchQuery)}&group_by=${this.groupBy}&start_date=${this.startDate}&end_date=${this.endDate}`;
        console.log("API 호출 URL:", url);

        // 날짜 범위 관련 파라미터 추가
        fetch(`/api/v2/news/chart/?query=${encodeURIComponent(this.searchQuery)}&group_by=${this.groupBy}&start_date=${this.startDate}&end_date=${this.endDate}`)
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

    // 날짜 범위 필터
    setupDateRangeEvent(){
        const startDateInput = document.getElementById("start_date");
        const endDateInput = document.getElementById("end_date");
        
        if (startDateInput && endDateInput){
            // 사용자가 시작날짜 변경 시 이벤트 발생
            startDateInput.addEventListener("change", (event) => {
                // 새로운 값으로 업데이트
                this.startDate = event.target.value;
                this.fetchDataAndUpdateChart();
            });

            endDateInput.addEventListener("change", (event) => {
                this.endDate = event.target.value;
                this.fetchDataAndUpdateChart();
            });
        } else {
            console.error("날짜 범위 필터 요소를 찾을 수 없습니다.")
        }
        
    }

    // 특정 날짜 클릭 
    setupClickEvent() {
        let clickTimeout;

        this.chart.canvas.onclick = (evt) => {
            const points = this.chart.getElementsAtEventForMode(evt, 'nearest', { intersect: true }, true);
            console.log(points)
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
  
    // 날짜 집계 기준(일/주/월) 필터
    setupFilterEvent() {
        // 필터 html 요소 가져오기
        const filterSelect = document.getElementById('group_by');
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