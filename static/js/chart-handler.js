class IssuePulseChart {
    constructor() {
        this.chart = null;
        this.initChart();
        this.fetchDataAndUpdateChart();
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
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    fill: false,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: 'Date' } },
                    y: { title: { display: true, text: 'Count' } }
                }
            }
        });
    }

    // API에서 데이터 가져오기
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
}

// 페이지가 로드되면 IssuePulseChart 초기화
document.addEventListener('DOMContentLoaded', () => {
    new IssuePulseChart();
});