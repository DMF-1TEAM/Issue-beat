class QuickSummaryHandler {
    constructor() {
        this.keywordElement = document.getElementById('quick-summary-keyword');
        this.contentElement = document.getElementById('quick-summary-content');
        
        // URL에서 검색어 가져오기
        this.searchQuery = new URLSearchParams(window.location.search).get('query');
        
        if (this.searchQuery) {
            this.fetchSummary();
        }
    }

    async fetchSummary() {
        try {
            this.showLoading();

            const response = await fetch(`/api/v2/news/quick-summary/?query=${encodeURIComponent(this.searchQuery)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '요약을 불러오는데 실패했습니다.');
            }

            this.updateUI(data);
        } catch (error) {
            console.error('Error fetching summary:', error);
            this.showError(error.message);
        }
    }

    updateUI(data) {
        // 키워드와 요약 내용 업데이트
        this.keywordElement.textContent = this.searchQuery;
        this.contentElement.textContent = data.summary;
    }

    showLoading() {
        this.keywordElement.textContent = this.searchQuery;
        this.contentElement.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span>요약을 생성하고 있습니다...</span>
            </div>
        `;
    }

    showError(message) {
        this.keywordElement.textContent = this.searchQuery;
        this.contentElement.innerHTML = `<span class="text-red-500">${message}</span>`;
    }
}

// DOM이 로드된 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.quickSummaryHandler = new QuickSummaryHandler();
});