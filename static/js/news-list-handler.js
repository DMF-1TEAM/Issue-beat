class NewsListHandler {
    constructor() {
        this.newsListContainer = document.getElementById('news-list');
        this.newsCountElement = document.getElementById('news-count');
        this.searchQuery = '';
        this.currentPage = 1;  // 초기 페이지 번호
        this.pageSize = 10;
        this.loading = false;
        this.hasNextPage = true;

        // 초기 데이터 로드
        this.fetchNews();

        // 스크롤 이벤트 등록
        window.addEventListener('scroll', () => this.handleScroll());
    }

    async handleSearch(query) {
        this.searchQuery = query;
        this.currentDate = null;
        this.resetList();

        try {
            const response = await fetch(`/api/news/search/?query=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '검색 중 오류가 발생했습니다.');
            }

            await this.updateNewsList(data);

        } catch (error) {
            console.error('Error searching news:', error);
            this.showError('검색 결과를 불러오는데 실패했습니다.');
        }
    }

    resetList() {
        this.currentPage = 1;
        this.hasMore = false;
        this.newsListContainer.innerHTML = '';
    }

    // API에서 뉴스 목록을 가져오는 메서드
    async fetchNews() {
        if (this.loading || !this.hasNextPage) return;
        this.loading = true;

        try {
            const response = await fetch(`/api/v2/news/?query=${encodeURIComponent(this.searchQuery)}&page=${this.currentPage}&page_size=${this.pageSize}`);
            const data = await response.json();

            if (data.news_list && data.news_list.length > 0) {
                this.renderNewsList(data.news_list);
                this.newsCountElement.innerText = `총 ${data.total_count}개 뉴스`; // 뉴스 개수 업데이트
                this.currentPage++;
                this.hasNextPage = data.has_next;
            }
        } catch (error) {
            console.error('뉴스 데이터를 가져오는 중 오류 발생:', error);
        } finally {
            this.loading = false;
        }
    }

    // 뉴스 목록을 화면에 추가하는 메서드
    renderNewsList(newsList) {
        newsList.forEach(news => {
            const newsItem = document.createElement('div');
            newsItem.classList.add('bg-white', 'rounded-lg', 'shadow-sm', 'hover:shadow-md', 'transition-shadow', 'duration-200', 'p-4', 'mb-4');

            newsItem.innerHTML = `
                <div class="flex justify-between items-start">
                    <h3 class="text-lg font-medium text-gray-900 mb-2 flex-grow">${news.title}</h3>
                    <span class="text-sm text-gray-500 ml-4 whitespace-nowrap">
                        ${news.date} 
                    </span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center space-x-4">
                        <span class="text-gray-600">${news.press}</span>
                    </div>
                    <a href="${news.link}" target="_blank" 
                       class="text-blue-600 hover:text-blue-800 flex items-center">
                        원문 보기
                        <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                    </a>
                </div>
            `;

            this.newsListContainer.appendChild(newsItem);
        });
    }

    // 스크롤 이벤트 핸들러
    handleScroll() {
        const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
        // 스크롤이 끝에 가까워졌을 때만 데이터 로드
        if (scrollTop + clientHeight >= scrollHeight - 100 && this.hasNextPage && !this.loading) {
            this.fetchNews();
        }
    }
}