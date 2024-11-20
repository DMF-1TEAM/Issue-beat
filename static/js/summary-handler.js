class SummaryHandler {
    constructor() {
        this.summaryContainers = {
            background: document.getElementById('summary-level-1'),
            mainContent: document.getElementById('summary-level-2'),
            currentStatus: document.getElementById('summary-level-3')
        };

        // 상태 관리를 위한 속성들
        this.query = new URLSearchParams(window.location.search).get('query') || '';
        this.date = new URLSearchParams(window.location.search).get('date') || null;
        this.startDate = new URLSearchParams(window.location.search).get('startDate') || null;
        this.endDate = new URLSearchParams(window.location.search).get('endDate') || null;
        this.groupBy = new URLSearchParams(window.location.search).get('group_by') || '1day';
        

        // 캐시 초기화
        this.summaryCache = new Map();

        // 현재 상태 객체 - 상태 비교를 위해 사용
        this.currentState = {
            query: this.query,
            date: this.date,
            startDate: this.startDate,
            endDate: this.endDate,
            groupBy: this.groupBy
        };

        // DOM 요소 확인
        Object.entries(this.summaryContainers).forEach(([key, element]) => {
            if (!element) {
                console.error(`${key} 컨테이너를 찾을 수 없습니다.`);
            }
        });

        // 이벤트 리스너 등록
        this.setupEventListeners();

        // 초기 데이터가 있으면 로드
        if (this.query) {
            this.loadInitialSummary();
        }
    }

    setupEventListeners() {
        document.addEventListener('chartDateClick', this.handleChartDateClick.bind(this));
        window.addEventListener('popstate', this.handlePopState.bind(this));
    }


    async loadInitialSummary() {
        try {
            await this.updateSummary(this.currentState.query, this.currentState.date);
        } catch (error) {
            console.error('초기 요약 로드 오류:', error);
        }
    }

    async handleChartDateClick(e) {
        const { date, query, groupBy, startDate, endDate } = e.detail;
        
        // 상태가 변경되었는지 확인
        if (this.isStateUnchanged(date, query, groupBy, startDate, endDate)) {
            return;
        }
        
        // 상태 업데이트
        this.updateState(date, query, groupBy, startDate, endDate);
        
        const cacheKey = this.getCacheKey();
        if (this.summaryCache.has(cacheKey)) {
            this.displaySummary(this.summaryCache.get(cacheKey));
        } else {
            await this.fetchAndUpdateSummary();
        }
    }

    isStateUnchanged(date, query, groupBy, startDate, endDate) {
        return this.currentState.date === date &&
               this.currentState.query === query &&
               this.currentState.groupBy === groupBy &&
               this.currentState.startDate === startDate &&
               this.currentState.endDate === endDate;
    }

    updateState(date, query, groupBy, startDate, endDate) {
        this.date = date;
        this.query = query;
        this.groupBy = groupBy;
        this.startDate = startDate;
        this.endDate = endDate;

        this.currentState = {
            date: this.date,
            query: this.query,
            groupBy: this.groupBy,
            startDate: this.startDate,
            endDate: this.endDate
        };
    }

    handlePopState(e) {
        const searchParams = new URLSearchParams(window.location.search);
        const newState = {
            date: searchParams.get('date'),
            query: searchParams.get('query'),
            groupBy: searchParams.get('group_by'),
            startDate: searchParams.get('startDate'),
            endDate: searchParams.get('endDate')
        };

        if (!this.isStateUnchanged(
            newState.date,
            newState.query,
            newState.groupBy,
            newState.startDate,
            newState.endDate
        )) {
            this.updateState(
                newState.date,
                newState.query,
                newState.groupBy,
                newState.startDate,
                newState.endDate
            );
            
            const cacheKey = this.getCacheKey();
            if (this.summaryCache.has(cacheKey)) {
                this.displaySummary(this.summaryCache.get(cacheKey));
            } else {
                this.fetchAndUpdateSummary();
            }
        }
    }

    getCacheKey() {
        return `${this.query}-${this.date || 'overall'}-${this.startDate}-${this.endDate}-${this.groupBy}`;
    }

    async loadInitialSummary() {
        try {
            await this.fetchAndUpdateSummary();
        } catch (error) {
            console.error('초기 요약 로드 오류:', error);
            this.showError('요약을 불러오는데 실패했습니다.');
        }
    }

    async fetchAndUpdateSummary() {
        if (!this.query) return;
        
        try {
            this.showLoading('요약을 생성하고 있습니다...');
            
            const url = new URL('/api/v2/news/summary/', window.location.origin);
            const params = new URLSearchParams({
                query: this.query,
                group_by: this.groupBy
            });

            if (this.startDate && this.endDate) {
                params.append('start_date', this.startDate);
                params.append('end_date', this.endDate);
            } else if (this.date) {
                params.append('date', this.date);
            }

            url.search = params.toString();

            const summary = await this.fetchSummaryWithRetry(url);
            
            if (summary) {
                const cacheKey = this.getCacheKey();
                this.summaryCache.set(cacheKey, summary);
                this.displaySummary(summary);
            } else {
                this.showError('요약 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
        } catch (error) {
            console.error('요약 업데이트 오류:', error);
            this.showError('요약을 불러오는데 실패했습니다.');
        }
    }

    async fetchSummaryWithRetry(url, maxRetries = 3) {
        let retryCount = 0;
        
        while (retryCount < maxRetries) {
            try {
                const response = await fetch(url);
                const data = await response.json();

                if (response.ok && !data.is_error) {
                    return data;
                }
            } catch (error) {
                console.error(`Retry ${retryCount + 1} failed:`, error);
            }

            retryCount++;
            if (retryCount < maxRetries) {
                this.showLoading(`요약 생성 중입니다... (${retryCount}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }
        
        return null;
    }

    displaySummary(summaryData) {
        if (!summaryData) {
            console.error('요약 데이터가 없습니다.');
            return;
        }
    
        // 배경 정보 표시 (내용만)
        this.summaryContainers.background.innerHTML = this.formatSummaryText(summaryData.background);
    
        // 핵심 내용 표시 (내용만)
        this.summaryContainers.mainContent.innerHTML = this.formatSummaryText(summaryData.core_content);
    
        // 결론 표시 (내용만)
        this.summaryContainers.currentStatus.innerHTML = this.formatSummaryText(summaryData.conclusion);
    }

    formatSummaryText(text) {
        return text.replace(/\n/g, '<br>');
    }

    showLoading() {
        Object.values(this.summaryContainers).forEach(container => {
            container.innerHTML = `
                <div class="flex justify-center items-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            `;
        });
    }
    
    showError(message) {
        Object.values(this.summaryContainers).forEach(container => {
            container.innerHTML = `
                <div class="text-red-500 text-center py-4">${message}</div>
            `;
        });
    }

    retryLastUpdate() {
        if (this.currentState.query) {
            this.updateSummary(this.currentState.query, this.currentState.date);
        }
    }
}

// DOM이 로드된 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.summaryHandler = new SummaryHandler();
});