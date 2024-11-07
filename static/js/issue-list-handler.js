class IssueListHandler {
    constructor(initialQuery = null) {
        this.newsListContainer = document.getElementById('news-list');
        this.currentPage = 1;  // 시작 페이지는 1
        this.hasMore = true;
        this.isLoading = false;
        this.currentDate = null;
        this.searchQuery = initialQuery || window.searchQuery;
        this.initialize();
    }

    initialize() {
        console.log('Initializing infinite scroll'); // 디버깅용
        this.setupInfiniteScroll();
    }

    setupInfiniteScroll() {
        // 스크롤 감지를 위한 옵저버 설정
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting && this.hasMore && !this.isLoading) {
                        console.log('Loading more news...'); // 디버깅용
                        this.loadMoreNews();
                    }
                });
            },
            { 
                root: this.newsListContainer,  // 뉴스 컨테이너를 root로 설정
                threshold: 0.1,  // 10%만 보여도 로드 시작
                rootMargin: '20px'  // 하단에서 20px 전에 로드 시작
            }
        );

        // sentinel 요소 생성 및 관찰
        const sentinel = document.createElement('div');
        sentinel.id = 'scroll-sentinel';
        sentinel.style.height = '1px';  // 높이 설정
        this.newsListContainer.appendChild(sentinel);
        observer.observe(sentinel);
        
        console.log('Infinite scroll setup complete'); // 디버깅용
    }

    async updateNewsList(newsData, isInitialLoad = true) {
        console.log('Updating news list:', { isInitialLoad, newsData }); // 디버깅용
        
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
        
        // sentinel 재설정
        const sentinel = document.getElementById('scroll-sentinel');
        if (sentinel) {
            this.newsListContainer.appendChild(sentinel);
        }
        
        console.log('News list updated, hasMore:', this.hasMore); // 디버깅용
    }

    async loadMoreNews() {
        if (this.isLoading || !this.hasMore) {
            console.log('Skip loading: ', { isLoading: this.isLoading, hasMore: this.hasMore }); // 디버깅용
            return;
        }

        console.log('Loading more news, page:', this.currentPage + 1); // 디버깅용
        this.isLoading = true;
        this.showLoadingIndicator();

        try {
            const nextPage = this.currentPage + 1;
            const url = `/api/v2/news/?query=${encodeURIComponent(this.searchQuery)}&page=${nextPage}`;
            
            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '뉴스를 불러오는 중 오류가 발생했습니다.');
            }

            await this.updateNewsList(data, false);
            this.currentPage = nextPage;

        } catch (error) {
            console.error('Error loading more news:', error);
            this.showError('추가 뉴스를 불러오는데 실패했습니다.');
        } finally {
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }


    async handleDateClick(date) {
        this.currentDate = date;
        // this.searchQuery = null; 제거 (검색어는 유지되어야 함)
        this.resetList();
    
        try {
            const response = await fetch(`/api/v2/news/?query=${encodeURIComponent(window.searchQuery)}&date=${date}`);
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
        if (!query) {
            console.error('No search query provided');
            this.showError('검색어를 입력해주세요.');
            return;
        }
    
        console.log('Searching with query:', query);  // 디버깅용 로그
        this.searchQuery = query;
        this.currentDate = null;
        this.resetList();
    
        try {
            const response = await fetch(`/api/v2/news/?query=${encodeURIComponent(query)}`);
            const data = await response.json();
    
            console.log('Search response:', data);  // 디버깅용 로그
    
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