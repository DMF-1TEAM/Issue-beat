class IssueListHandler {
    constructor() {
        this.newsListContainer = document.getElementById('news-list');
        this.currentPage = 1;
        this.hasMore = true;
        this.isLoading = false;
        this.currentDate = null;
        this.searchQuery = null;
        
        this.initialize();
    }

    initialize() {
        this.setupInfiniteScroll();
    }

    setupInfiniteScroll() {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && this.hasMore && !this.isLoading) {
                    this.loadMoreNews();
                }
            },
            { threshold: 0.5 }
        );

        const sentinel = document.createElement('div');
        sentinel.id = 'scroll-sentinel';
        this.newsListContainer.appendChild(sentinel);
        observer.observe(sentinel);
    }

    async updateNewsList(newsData, isInitialLoad = true) {
        if (isInitialLoad) {
            this.currentPage = 1;
            this.newsListContainer.innerHTML = '';
        }

        const newsHTML = this.createNewsListHTML(newsData.news_list);
        
        if (isInitialLoad) {
            this.newsListContainer.innerHTML = newsHTML;
        } else {
            this.newsListContainer.insertAdjacentHTML('beforeend', newsHTML);
        }

        this.hasMore = newsData.has_next;
        this.updateNewsCount(newsData.total_count);
    }

    createNewsListHTML(newsList) {
        return newsList.map(news => `
            <div class="bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 p-4 mb-4">
                <div class="flex justify-between items-start">
                    <h3 class="text-lg font-medium text-gray-900 mb-2 flex-grow">${news.title}</h3>
                    <span class="text-sm text-gray-500 ml-4 whitespace-nowrap">
                        ${this.formatDate(news.date)}
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
            </div>
        `).join('');
    }

    async loadMoreNews() {
        if (this.isLoading || !this.hasMore) return; // isLoading 또는 hasMore가 false일 경우 호출 방지
    
        this.isLoading = true;
        this.showLoadingIndicator();
        
        try {
            const nextPage = this.currentPage + 1;
            let url;
    
            // currentDate 또는 searchQuery에 따라 URL 설정
            if (this.currentDate) {
                url = `/api/news/date/${this.currentDate}/?page=${nextPage}`;
            } else {
                url = `/api/news/search/?query=${encodeURIComponent(this.searchQuery)}&page=${nextPage}`;
            }
            
            console.log("Loading URL:", url);
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to fetch news data');
            }
    
            const data = await response.json();
            console.log("Response Data:", data); // 응답 데이터 확인
    
            await this.updateNewsList(data, false); // 리스트 추가로 업데이트
            this.currentPage = nextPage;
            this.hasMore = data.has_next; // 다음 페이지 유무 갱신
    
        } catch (error) {
            console.error('Error loading more news:', error);
            this.showError('추가 뉴스를 불러오는데 실패했습니다.');
        } finally {
            this.isLoading = false; // 로딩 완료 후 isLoading 상태 갱신
            this.hideLoadingIndicator();
        }
    }    

    async handleDateClick(date) {
        this.currentDate = date;
        this.searchQuery = null;
        this.resetList();

        try {
            const response = await fetch(`/api/news/date/${date}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '뉴스를 불러오는 중 오류가 발생했습니다.');
            }

            await this.updateNewsList(data);

        } catch (error) {
            console.error('Error loading date news:', error);
            this.showError('해당 날짜의 뉴스를 불러오는데 실패했습니다.');
        }
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

    updateNewsCount(total) {
        const countElement = document.getElementById('news-count');
        if (countElement) {
            countElement.textContent = `총 ${total}건의 뉴스`;
        }
    }

    formatDate(dateString) {
        return new Intl.DateTimeFormat('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(dateString));
    }

    showLoadingIndicator() {
        const loader = document.getElementById('scroll-sentinel');
        if (loader) {
            loader.innerHTML = `
                <div class="flex justify-center items-center py-4">
                    <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
            `;
        }
    }

    hideLoadingIndicator() {
        const loader = document.getElementById('scroll-sentinel');
        if (loader) {
            loader.innerHTML = '';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border-l-4 border-red-500 p-4 my-4';
        errorDiv.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-red-700">${message}</p>
                </div>
            </div>
        `;
        
        this.newsListContainer.insertAdjacentElement('afterbegin', errorDiv);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }
}