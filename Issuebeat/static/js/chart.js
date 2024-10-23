document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('dataCountChart').getContext('2d');

    // 변수들은 HTML 파일에서 할당
    const dateLabels = window.dateLabels; 
    const dataCounts = window.dataCounts;  

    const dataCountChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dateLabels,
            datasets: [{
                label: '뉴스 데이터 수',
                data: dataCounts,
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: true,
                tension: 0.6
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '날짜'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '데이터 수'
                    },
                    beginAtZero: true
                }
            }
        }});
});
