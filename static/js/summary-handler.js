class SummaryHandler {
    constructor() {
        this.summaryContainers = {
            background: document.getElementById('summary-level-1'),
            mainContent: document.getElementById('summary-level-2'),
            currentStatus: document.getElementById('summary-level-3')
        };

        // 상태 초기화
        const urlParams = new URLSearchParams(window.location.search);
        this.query = urlParams.get('query') || '';
        this.date = urlParams.get('date') || null;
        this.startDate = urlParams.get('startDate') || null;
        this.endDate = urlParams.get('endDate') || null;
        this.groupBy = urlParams.get('group_by') || '1day';
        
        this.isLoading = false;
        this.currentRequest = null;
        this.summaryCache = new Map();
        this.initialLoadComplete = false;

        this.setupEventListeners();
        
        // 초기 로드는 requestAnimationFrame으로 지연
        if (this.query && Object.values(this.summaryContainers).every(el => el)) {
            this.loadInitialSummary();
        }
    }

    setupEventListeners() {
        this.boundHandleChartDateClick = this.handleChartDateClick.bind(this);
        this.boundHandlePopState = this.handlePopState.bind(this);

        document.removeEventListener('chartDateClick', this.boundHandleChartDateClick);
        window.removeEventListener('popstate', this.boundHandlePopState);
        
        document.addEventListener('chartDateClick', this.boundHandleChartDateClick);
        window.addEventListener('popstate', this.boundHandlePopState);
    }

    async loadInitialSummary() {
        if (this.isLoading || this.initialLoadComplete) return;
        
        try {
            this.initialLoadComplete = true;
            await this.fetchAndUpdateSummary();
        } catch (error) {
            console.error('초기 요약 로드 오류:', error);
            this.showError('요약을 불러오는데 실패했습니다.');
        }
    }

    handleChartDateClick(e) {
        const { date, query, groupBy, startDate, endDate } = e.detail;
        this.initialLoadComplete = false; // 차트 클릭 시 초기화
        this.updateState(date, query, groupBy, startDate, endDate);
        this.fetchAndUpdateSummary();
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

    getCacheKey() {
        return `${this.query}-${this.date || 'overall'}-${this.startDate}-${this.endDate}-${this.groupBy}`;
    }

    async fetchAndUpdateSummary() {
        if (!this.query || this.isLoading) return;
        
        const requestKey = this.getCacheKey();
        if (requestKey === this.lastRequestKey) return;
        
        if (this.summaryCache.has(requestKey)) {
            this.displaySummary(this.summaryCache.get(requestKey));
            return;
        }

        this.isLoading = true;
        this.lastRequestKey = requestKey;
        
        try {
            this.showLoading();
            
            if (this.currentRequest) {
                this.currentRequest.abort();
            }

            this.currentRequest = new AbortController();
            
            const summary = await this.fetchSummaryWithRetry(
                this.buildSummaryUrl(),
                this.currentRequest.signal
            );
            
            if (summary) {
                this.summaryCache.set(requestKey, summary);
                this.displaySummary(summary);
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('이전 요청이 취소되었습니다.');
                return;
            }
            console.error('요약 업데이트 오류:', error);
            this.showError('요약을 불러오는데 실패했습니다.');
        } finally {
            this.isLoading = false;
            this.currentRequest = null;
        }
    }

    async fetchSummaryWithRetry(url, signal, maxRetries = 3) {
        let retryCount = 0;
        
        while (retryCount < maxRetries) {
            try {
                const response = await fetch(url, { signal });
                const data = await response.json();

                if (response.ok && !data.is_error) {
                    return data;
                }
            } catch (error) {
                if (error.name === 'AbortError') {
                    throw error;
                }
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

    buildSummaryUrl() {
        const url = new URL('/api/v2/news/summary/', window.location.origin);
        const params = new URLSearchParams({
            query: this.query,
            group_by: this.groupBy
        });

        if (this.date) params.append('date', this.date);
        if (this.startDate) params.append('start_date', this.startDate);
        if (this.endDate) params.append('end_date', this.endDate);

        url.search = params.toString();
        return url;
    }

    displaySummary(summaryData) {
        if (!summaryData) {
            console.error('요약 데이터가 없습니다.');
            return;
        }

        setTimeout(() => {
            this.summaryContainers.background.innerHTML = 
                this.formatSummaryText(summaryData.background);
        }, 0);
        
        setTimeout(() => {
            this.summaryContainers.mainContent.innerHTML = 
                this.formatSummaryText(summaryData.core_content);
        }, 100);
        
        setTimeout(() => {
            this.summaryContainers.currentStatus.innerHTML = 
                this.formatSummaryText(summaryData.conclusion);
        }, 200);

        this.updateURL();
    }

    formatSummaryText(text) {
        if (!text) return '';
        
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/_(.*?)_/g, '<em>$1</em>')
            .trim();
    }

    updateURL() {
        const searchParams = new URLSearchParams(window.location.search);
        
        if (this.date) searchParams.set('date', this.date);
        else searchParams.delete('date');
        
        if (this.startDate) searchParams.set('startDate', this.startDate);
        else searchParams.delete('startDate');
        
        if (this.endDate) searchParams.set('endDate', this.endDate);
        else searchParams.delete('endDate');
        
        searchParams.set('group_by', this.groupBy);
        searchParams.set('query', this.query);

        const newURL = `${window.location.pathname}?${searchParams.toString()}`;
        window.history.pushState({ path: newURL }, '', newURL);
    }

    showLoading(message = '요약을 생성하고 있습니다...') {
        const loadingHTML = `
            <div class="flex justify-center items-center py-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
                <span>${message}</span>
            </div>
        `;
        
        Object.values(this.summaryContainers).forEach(container => {
            if (container) container.innerHTML = loadingHTML;
        });
    }
    
    showError(message) {
        const errorHTML = `
            <div class="text-red-500 text-center py-4">
                ${message}
                <button 
                    class="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onclick="window.summaryHandler.retryLastUpdate()"
                >
                    다시 시도
                </button>
            </div>
        `;
        
        Object.values(this.summaryContainers).forEach(container => {
            if (container) container.innerHTML = errorHTML;
        });
    }

    retryLastUpdate() {
        this.fetchAndUpdateSummary();
    }
}

// Chart.js와의 통합
document.addEventListener('DOMContentLoaded', () => {
    const initializeHandlers = () => {
        if (!window.summaryHandler) {
            window.summaryHandler = new SummaryHandler();
        }
        if (!window.issuePulseChart) {
            window.issuePulseChart = new IssuePulseChart();
        }
    };

    // 지연 초기화
    setTimeout(initializeHandlers, 0);
});