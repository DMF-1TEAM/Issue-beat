class SummaryHandler {
    constructor() {
        this.summaryContainers = {
            background: document.getElementById('summary-level-1'),
            mainContent: document.getElementById('summary-level-2'),
            currentStatus: document.getElementById('summary-level-3')
        };
        
        this.summaryIcons = {
            background: `
                <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
            `,
            mainContent: `
                <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                </svg>
            `,
            currentStatus: `
                <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
            `
        };

        // DOM 요소 확인
        Object.entries(this.summaryContainers).forEach(([key, element]) => {
            if (!element) {
                console.error(`${key} 컨테이너를 찾을 수 없습니다.`);
            }
        });

        // 캐시 초기화
        this.summaryCache = new Map();

        // 현재 상태 관리
        this.currentState = {
            query: new URLSearchParams(window.location.search).get('query') || '',
            date: new URLSearchParams(window.location.search).get('date') || null
        };

        // 이벤트 리스너 등록 (바인딩된 메소드 사용)
        document.addEventListener('chartDateClick', this.handleChartDateClick.bind(this));
        window.addEventListener('popstate', this.handlePopState.bind(this));

        // 초기 데이터가 있으면 로드
        if (this.currentState.query) {
            this.loadInitialSummary();
        }
    }

    async loadInitialSummary() {
        try {
            await this.updateSummary(this.currentState.query, this.currentState.date);
        } catch (error) {
            console.error('초기 요약 로드 오류:', error);
        }
    }

    async handleChartDateClick(e) {
        const { date, query } = e.detail;
        
        // 같은 날짜 중복 클릭 방지
        if (date === this.currentState.date) return;
        
        this.currentState.date = date;
        this.currentState.query = query;
        
        const cacheKey = this.getCacheKey(query, date);
        if (this.summaryCache.has(cacheKey)) {
            this.displaySummary(this.summaryCache.get(cacheKey));
        } else {
            await this.updateSummary(query, date);
        }
    }

    handlePopState(e) {
        const searchParams = new URLSearchParams(window.location.search);
        const newDate = searchParams.get('date');
        const query = searchParams.get('query');

        // 상태가 변경되었을 때만 요약 업데이트
        if (this.currentState.date !== newDate || this.currentState.query !== query) {
            this.currentState.date = newDate;
            this.currentState.query = query;
            
            const cacheKey = this.getCacheKey(query, newDate);
            if (this.summaryCache.has(cacheKey)) {
                this.displaySummary(this.summaryCache.get(cacheKey));
            } else {
                this.updateSummary(query, newDate);
            }
        }
    }

    getCacheKey(query, date) {
        return `${query}-${date || 'overall'}`;
    }

    async updateSummary(query, date) {
        if (!query) return;
        
        try {
            this.showLoading('요약을 생성하고 있습니다...');
            
            let retryCount = 0;
            const maxRetries = 3;
            let summary = null;

            while (retryCount < maxRetries) {
                const url = new URL('/api/v2/news/summary/', window.location.origin);
                url.searchParams.set('query', query);
                if (date) url.searchParams.set('date', date);

                const response = await fetch(url);
                const data = await response.json();

                if (response.ok && !data.is_error) {
                    summary = data;
                    break;  // 성공적으로 요약을 받았으면 반복 중단
                } else {
                    // 에러 응답이나 요약 생성 중인 경우 잠시 대기 후 재시도
                    retryCount++;
                    if (retryCount < maxRetries) {
                        this.showLoading(`요약 생성 중입니다... (${retryCount}/${maxRetries})`);
                        await new Promise(resolve => setTimeout(resolve, 2000));  // 2초 대기
                    }
                }
            }

            if (summary) {
                this.displaySummary(summary);
            } else {
                this.showError('요약 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
            
        } catch (error) {
            console.error('요약 업데이트 오류:', error);
            this.showError('요약을 불러오는데 실패했습니다.');
        }
    }

    displaySummary(summaryData) {
        if (!summaryData) {
            console.error('요약 데이터가 없습니다.');
            return;
        }

        // 배경 정보 표시
        this.summaryContainers.background.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    ${this.summaryIcons.background}
                    <h3 class="text-lg font-medium text-gray-900">배경</h3>
                </div>
                <div class="text-gray-600 leading-relaxed">
                    ${this.formatSummaryText(summaryData.background)}
                </div>
            </div>
        `;

        // 핵심 내용 표시
        this.summaryContainers.mainContent.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    ${this.summaryIcons.mainContent}
                    <h3 class="text-lg font-medium text-gray-900">핵심 내용</h3>
                </div>
                <div class="text-gray-600 leading-relaxed">
                    ${this.formatSummaryText(summaryData.core_content)}
                </div>
            </div>
        `;

        // 결론 표시
        this.summaryContainers.currentStatus.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    ${this.summaryIcons.currentStatus}
                    <h3 class="text-lg font-medium text-gray-900">결론</h3>
                </div>
                <div class="text-gray-600 leading-relaxed">
                    ${this.formatSummaryText(summaryData.conclusion)}
                </div>
            </div>
        `;
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