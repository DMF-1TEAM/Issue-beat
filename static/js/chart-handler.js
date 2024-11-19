class IssuePulseChart {
    constructor() {
        // 기본 상태 초기화
        this.chart = null;
        this.searchQuery = new URLSearchParams(window.location.search).get('query') || '';
        this.groupBy = new URLSearchParams(window.location.search).get('group_by') || '1day';

        // 날짜 범위 초기화
        const today = new Date();
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        
        this.startDate = document.getElementById("start_date").value || oneYearAgo.toISOString().split('T')[0];
        this.endDate = document.getElementById("end_date").value || today.toISOString().split('T')[0];
        this.selectedDate = null;
        
        // 툴팁 관련 상태
        this.tooltipCache = new Map();
        this.activeTooltip = null;
        this.tooltipTimeout = null;

        // 컴포넌트 초기화
        this.initChart();
        this.setupEventListeners();
        this.fetchDataAndUpdateChart();
    }

    setupEventListeners() {
        // 필터 변경 이벤트
        const filterSelect = document.getElementById('date_filter');
        if (filterSelect) {
            filterSelect.value = this.groupBy;
            filterSelect.addEventListener('change', this.handleFilterChange.bind(this));
        }

        // 날짜 범위 이벤트
        const startDateInput = document.getElementById("start_date");
        const endDateInput = document.getElementById("end_date");
        const applyButton = document.getElementById("applyDateRange");
        
        if (startDateInput && endDateInput && applyButton) {
            startDateInput.value = this.startDate;
            endDateInput.value = this.endDate;

            startDateInput.addEventListener("change", this.handleStartDateChange.bind(this));
            endDateInput.addEventListener("change", this.handleEndDateChange.bind(this));
            applyButton.addEventListener("click", this.handleDateRangeApply.bind(this));
        }

         // 초기화 버튼 이벤트 리스너 추가
        const resetButton = document.getElementById('resetView');
        if (resetButton) {
            resetButton.addEventListener('click', this.handleReset.bind(this));
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

        if (!tooltip.dataPoints || !tooltip.dataPoints.length) return;

        const tooltipEl = this.createTooltipElement(chart);
        const dataPoint = tooltip.dataPoints[0];
        const date = dataPoint.label;

        // 로딩 상태 표시
        this.showTooltipLoading(tooltipEl, date);
        this.positionTooltip(tooltipEl, context);

        // API 호출 및 데이터 표시
        if (this.tooltipTimeout) {
            clearTimeout(this.tooltipTimeout);
        }

        this.tooltipTimeout = setTimeout(async () => {
            try {
                const summaryData = await this.fetchTooltipData(date);
                if (this.activeTooltip === tooltipEl) {
                    this.updateTooltipContent(tooltipEl, summaryData);
                }
            } catch (error) {
                console.error('Error fetching tooltip data:', error);
                this.showTooltipError(tooltipEl);
            }
        }, 200);
    }

    async fetchTooltipData(date) {
        const cacheKey = `${date}_${this.groupBy}_${this.searchQuery}`;
        if (this.tooltipCache.has(cacheKey)) {
            return this.tooltipCache.get(cacheKey);
        }

        const response = await fetch(
            `/api/v2/news/hover-summary/${date}/?query=${encodeURIComponent(this.searchQuery)}&group_by=${this.groupBy}`
        );
        
        if (!response.ok) {
            throw new Error('Failed to fetch summary');
        }

        const data = await response.json();
        this.tooltipCache.set(cacheKey, data);
        return data;
    }

    createTooltipElement(chart) {
        if (this.activeTooltip) {
            this.activeTooltip.remove();
        }

        const tooltipEl = document.createElement('div');
        tooltipEl.className = 'chartjs-tooltip';
        Object.assign(tooltipEl.style, {
            opacity: '0',
            position: 'fixed',
            pointerEvents: 'none',
            transition: 'all 0.2s ease',
            maxWidth: '300px',
            minWidth: '200px'
        });

        chart.canvas.parentNode.appendChild(tooltipEl);
        this.activeTooltip = tooltipEl;
        return tooltipEl;
    }

    updateTooltipContent(tooltipEl, data) {
        tooltipEl.innerHTML = `
            <div class="bg-white shadow-lg rounded-lg border border-gray-200 p-4">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold">${data.date || ''}</span>
                    <span class="text-blue-600">뉴스 ${data.news_count}건</span>
                </div>
                <div class="text-sm font-medium text-gray-900">
                    ${data.title_summary}
                </div>
                <div class="text-sm text-gray-600 mt-1">
                    ${data.content_summary}
                </div>
            </div>
        `;
        tooltipEl.style.opacity = '1';
    }

    showTooltipLoading(tooltipEl, date) {
        tooltipEl.innerHTML = `
            <div class="bg-white shadow-lg rounded-lg border border-gray-200 p-4">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold">${date}</span>
                    <span class="text-blue-600">로딩중...</span>
                </div>
                <div class="text-sm text-gray-500">
                    <div class="animate-pulse">요약을 불러오는 중입니다...</div>
                </div>
            </div>
        `;
        tooltipEl.style.opacity = '1';
    }

    showTooltipError(tooltipEl) {
        tooltipEl.innerHTML = `
            <div class="bg-white shadow-lg rounded-lg border border-gray-200 p-4">
                <div class="text-sm text-red-500">
                    요약을 불러오는데 실패했습니다.
                </div>
            </div>
        `;
    }

    positionTooltip(tooltipEl, context) {
        const position = context.chart.canvas.getBoundingClientRect();
        const mouseX = position.left + context.tooltip.caretX;
        const mouseY = position.top + context.tooltip.caretY;
        
        const tooltipWidth = tooltipEl.offsetWidth;
        const windowWidth = window.innerWidth;
        const xPosition = mouseX + tooltipWidth + 10 > windowWidth 
            ? mouseX - tooltipWidth - 10 
            : mouseX + 10;

        tooltipEl.style.left = `${xPosition}px`;
        tooltipEl.style.top = `${mouseY - tooltipEl.offsetHeight - 10}px`;
    }

    clearActiveTooltip() {
        if (this.tooltipTimeout) {
            clearTimeout(this.tooltipTimeout);
            this.tooltipTimeout = null;
        }
        if (this.activeTooltip) {
            this.activeTooltip.style.opacity = '0';
            setTimeout(() => {
                if (this.activeTooltip && this.activeTooltip.parentNode) {
                    this.activeTooltip.parentNode.removeChild(this.activeTooltip);
                }
                this.activeTooltip = null;
            }, 200);
        }
    }

    async fetchDataAndUpdateChart() {
        if (!this.searchQuery) return;

        try {
            const url = new URL('/api/v2/news/chart/', window.location.origin);
            const params = new URLSearchParams({
                query: this.searchQuery,
                group_by: this.groupBy,
                start_date: this.startDate,
                end_date: this.endDate
            });
            url.search = params.toString();

            const response = await fetch(url);
            const data = await response.json();

            if (!Array.isArray(data)) {
                throw new Error('Invalid data format');
            }

            if (data.length === 0) {
                this.showNoDataMessage();
                return;
            }

            this.chart.data.labels = data.map(item => item.date);
            this.chart.data.datasets[0].data = data.map(item => item.count);
            this.chart.update();
        } catch (error) {
            console.error('Error fetching chart data:', error);
            this.showErrorMessage();
        }
    }

    handleFilterChange(event) {
        this.groupBy = event.target.value;
        this.tooltipCache.clear();
        
        // URL 업데이트
        this.updateURL({ group_by: this.groupBy });
        
        // 차트 데이터 업데이트
        this.fetchDataAndUpdateChart();

        // 뉴스 리스트 업데이트
        if (window.newsListHandler) {
            window.newsListHandler.resetList();
            window.newsListHandler.fetchNews();
        }
    }

    handleStartDateChange(event) {
        const newStartDate = event.target.value;
        const endDate = new Date(this.endDate);
        
        if (new Date(newStartDate) > endDate) {
            alert('시작일이 종료일보다 늦을 수 없습니다.');
            event.target.value = this.startDate;
            return;
        }
        
        this.startDate = newStartDate;
    }

    handleEndDateChange(event) {
        const newEndDate = event.target.value;
        const startDate = new Date(this.startDate);
        
        if (startDate > new Date(newEndDate)) {
            alert('종료일이 시작일보다 빠를 수 없습니다.');
            event.target.value = this.endDate;
            return;
        }
        
        this.endDate = newEndDate;
    }

    handleDateRangeApply() {
        this.tooltipCache.clear();
        
        // URL 업데이트
        this.updateURL({
            start_date: this.startDate,
            end_date: this.endDate
        });
        
        // 데이터 새로고침
        this.fetchDataAndUpdateChart();
    }

    updateURL(params) {
        const searchParams = new URLSearchParams(window.location.search);
        
        // 기존 파라미터 유지하면서 새로운 파라미터 추가/수정
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                searchParams.set(key, value);
            }
        });

        const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
        window.history.pushState({}, '', newUrl);
    }

    showNoDataMessage() {
        const ctx = this.chart.ctx;
        this.chart.clear();
        
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '14px Pretendard';
        ctx.fillStyle = '#666';
        ctx.fillText('선택한 기간에 데이터가 없습니다.', this.chart.width / 2, this.chart.height / 2);
        ctx.restore();
    }

    showErrorMessage() {
        const ctx = this.chart.ctx;
        this.chart.clear();
        
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.font = '14px Pretendard';
        ctx.fillStyle = '#dc2626';
        ctx.fillText('데이터를 불러오는데 실패했습니다.', this.chart.width / 2, this.chart.height / 2);
        ctx.restore();
    }
}

// DOM 로드 완료 후 차트 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.issuePulseChart = new IssuePulseChart();
});