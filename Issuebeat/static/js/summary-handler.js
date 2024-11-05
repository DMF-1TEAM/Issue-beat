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
    }

    async updateSummary(date) {
        try {
            this.showLoading();
            const response = await fetch(`/api/summary/${date}/`);
            const data = await response.json();

            if (data.success) {
                this.displaySummary(data.data);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            this.showError('요약을 불러오는 중 오류가 발생했습니다.');
            console.error('Summary error:', error);
        } finally {
            this.hideLoading();
        }
    }

    displaySummary(summaryData) {
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

        // 주요 내용 표시
        this.summaryContainers.mainContent.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    ${this.summaryIcons.mainContent}
                    <h3 class="text-lg font-medium text-gray-900">주요내용</h3>
                </div>
                <div class="text-gray-600 leading-relaxed">
                    ${this.formatSummaryText(summaryData.main_content)}
                </div>
            </div>
        `;

        // 현재 상황 표시
        this.summaryContainers.currentStatus.innerHTML = `
            <div class="space-y-4">
                <div class="flex items-center space-x-2">
                    ${this.summaryIcons.currentStatus}
                    <h3 class="text-lg font-medium text-gray-900">현황</h3>
                </div>
                <div class="text-gray-600 leading-relaxed">
                    ${this.formatSummaryText(summaryData.current_status)}
                </div>
            </div>
        `;
    }

    formatSummaryText(text) {
        // 줄바꿈을 HTML로 변환
        return text.replace(/\n/g, '<br>');
    }

    showLoading() {
        Object.values(this.summaryContainers).forEach(container => {
            container.innerHTML = `
                <div class="flex items-center justify-center py-8">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                </div>
            `;
        });
    }

    hideLoading() {
        // 로딩 인디케이터는 displaySummary에서 자동으로 제거됨
    }

    showError(message) {
        Object.values(this.summaryContainers).forEach(container => {
            container.innerHTML = `
                <div class="text-red-500 text-center py-4">
                    ${message}
                </div>
            `;
        });
    }
}

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.summaryHandler = new SummaryHandler();
});