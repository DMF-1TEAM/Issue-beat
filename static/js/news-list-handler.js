class NewsListHandler {
    constructor() {
        this.newsListContainer = document.getElementById('news-list');
        this.newsCountElement = document.getElementById('news-count');
        this.searchQuery = '';
        this.currentDate = this.getDateFromURL(); // Extract date from URL
        this.currentPage = 1;
        this.pageSize = 10;
        this.loading = false;
        this.hasNextPage = true;
        this.cache = {};  // 캐시 객체 추가

        // 초기 데이터 로드
        this.fetchNews();

        // Intersection Observer 설정
        this.observer = new IntersectionObserver((entries) => {
            const entry = entries[0];
            if (entry.isIntersecting && this.hasNextPage && !this.loading) {
                this.fetchNews();
            }
        }, { rootMargin: '100px' });

        // chartDateClick 이벤트 리스너
        document.addEventListener('chartDateClick', (e) => {
            const { date } = e.detail;
            if (date !== this.currentDate) {
                this.handleDateClick(date);
            }
        });
    }

    // URL에서 날짜 추출
    getDateFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('date') || null;  // URL에서 date 파라미터 추출
    }

    async handleDateClick(date) {
        if (this.currentDate === date) {
            return; // 같은 날짜 중복 클릭 방지
        }
        
        this.currentDate = date;
        this.resetList();
        await this.fetchNews();
    }

    async handleSearch(query) {
        this.searchQuery = query; // 검색어 업데이트
        this.resetList();

        try {
            const response = await fetch(`/api/v2/news/?query=${encodeURIComponent(query)}&date=${this.currentDate}`);
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
        this.hasNextPage = true;
        this.loading = false;
        this.cache = {};  // 캐시 초기화
        this.newsListContainer.innerHTML = '';
    }

    async fetchNews() {
        if (this.loading || !this.hasNextPage) return;
        this.loading = true;

        // 캐시에 페이지 데이터가 있는지 확인
        const cacheKey = `${this.searchQuery}_${this.currentDate}_${this.currentPage}`;
        if (this.cache[cacheKey]) {
            this.renderNewsList(this.cache[cacheKey].news_list);
            this.newsCountElement.innerText = `총 ${this.cache[cacheKey].total_count}개 뉴스`;
            this.currentPage++;
            this.hasNextPage = this.cache[cacheKey].has_next;
            this.loading = false;
            return;
        }

        try {
            // `currentDate`가 있으면 해당 날짜로 필터링
            const url = this.currentDate
                ? `/api/v2/news/?query=${encodeURIComponent(this.searchQuery)}&date=${this.currentDate}&page=${this.currentPage}&page_size=${this.pageSize}`
                : `/api/v2/news/?query=${encodeURIComponent(this.searchQuery)}&page=${this.currentPage}&page_size=${this.pageSize}`;
            
            const response = await fetch(url);
            const data = await response.json();
    
            if (data.news_list && data.news_list.length > 0) {
                this.cache[cacheKey] = data;
                this.renderNewsList(data.news_list);
                this.newsCountElement.innerText = `총 ${data.total_count}개 뉴스`;
                this.currentPage++;
                this.hasNextPage = data.has_next;
            } else {
                this.hasNextPage = false;
            }
        } catch (error) {
            console.error('뉴스 데이터를 가져오는 중 오류 발생:', error);
        } finally {
            this.loading = false;
        }
    }

    renderNewsList(newsList) {
        newsList.forEach((news, index) => {
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
    
            // 뉴스 항목 클릭 시 API 요청
            newsItem.addEventListener('click', async () => {
                try {
                    const response = await fetch(`/api/news/${news.id}`);
                    const data = await response.json();
    
                    if (!response.ok) {
                        throw new Error(data.error || '뉴스 데이터를 불러오는 데 실패했습니다.');
                    }
    
                    // 팝업 창을 생성하여 뉴스 데이터를 표시
                    this.showPopup(data);
                } catch (error) {
                    console.error('뉴스 데이터를 불러오는 중 오류 발생:', error);
                }
            });
    
            this.newsListContainer.appendChild(newsItem);
    
            // 무한 스크롤을 위해 마지막 뉴스 항목 관찰
            if (index === newsList.length - 1) {
                this.observer.observe(newsItem);
            }
        });
    }
    
    // 팝업 창 생성 함수
    showPopup(data) {
        const popup = document.createElement('div');
        popup.classList.add('popup', 'fixed', 'inset-0', 'bg-gray-800', 'bg-opacity-75', 'flex', 'justify-center', 'items-center', 'z-50');
        
        popup.innerHTML = `
            <div class="popup-content">
                <h2 class="text-2xl font-bold mb-2">${data.title}</h2>
                <div class="text-sm text-gray-500 mb-4">
                    <span>${data.press}</span> | <span>${data.author}</span>
                </div>
                ${data.image ? `<img src="${data.image}" alt="뉴스 이미지" class="mb-4 rounded">` : ''}
                <p class="text-gray-700 mb-4">${data.content}</p>
                <a href="${data.link}" target="_blank" class="text-blue-600 hover:text-blue-800">
                    원문 보기
                </a>
                <button class="mt-4 bg-red-500 text-white py-2 px-4 rounded close-popup">
                    닫기
                </button>
            </div>
        `;
        
        popup.querySelector('.close-popup').addEventListener('click', () => {
            popup.remove();
        });
        
        document.body.appendChild(popup);
    }  
}