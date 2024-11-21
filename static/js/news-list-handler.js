
class NewsListHandler {
    constructor() {
        this.newsListContainer = document.getElementById('news-list');
        this.newsCountElement = document.getElementById('count');
        this.searchQuery = '';
        this.currentDate = null;
        this.startDate = null;
        this.endDate = null;
        this.groupBy = '1day';
        this.currentPage = 1;
        this.pageSize = 10;
        this.loading = false;
        this.hasNextPage = true;
        this.cache = {};

        // URL에서 초기 값 가져오기
        const urlParams = new URLSearchParams(window.location.search);
        this.searchQuery = urlParams.get('query') || '';
        this.currentDate = urlParams.get('date') || null;
        this.startDate = urlParams.get('start_date') || null;
        this.endDate = urlParams.get('end_date') || null;
        this.groupBy = urlParams.get('group_by') || '1day';

        // Intersection Observer 설정
        this.observer = new IntersectionObserver((entries) => {
            const entry = entries[0];
            if (entry.isIntersecting && this.hasNextPage && !this.loading) {
                this.fetchNews();
            }
        }, { rootMargin: '100px' });

        // chartDateClick 이벤트 리스너
        document.addEventListener('chartDateClick', (e) => {
            const { date, query, startDate, endDate, groupBy } = e.detail;
            this.handleDateClick({
                detail: {
                    date,
                    query,
                    startDate,
                    endDate,
                    groupBy
                }
            });
        });

        // 초기 데이터 로드
        if (this.searchQuery) {
            this.fetchNews();
        }
    }

    // URL에서 날짜 추출
    getDateFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('date') || null;  // URL에서 date 파라미터 추출
    }

    async handleDateClick(event) {
        const { date, query, startDate, endDate, groupBy } = event.detail;
        
        // 같은 데이터 요청인지 확인
        if (this.currentDate === date && 
            this.startDate === startDate && 
            this.endDate === endDate && 
            this.groupBy === groupBy) {
            return;
        }
        
        // 상태 업데이트
        this.currentDate = date;
        this.searchQuery = query;  // 이 부분이 누락되어 있었음
        this.startDate = startDate;
        this.endDate = endDate;
        this.groupBy = groupBy;
        
        console.log('Handling date click:', {
            date: this.currentDate,
            query: this.searchQuery,
            startDate: this.startDate,
            endDate: this.endDate,
            groupBy: this.groupBy
        });
        
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
        this.cache = {};
        this.newsListContainer.innerHTML = '';
    }

    async fetchNews() {
        if (this.loading || !this.hasNextPage) return;
        this.loading = true;

        const cacheKey = this.getCacheKey();
        if (this.cache[cacheKey]) {
            this.renderNewsList(this.cache[cacheKey].news_list);
            this.updateNewsCount(this.cache[cacheKey].total_count);
            this.currentPage++;
            this.hasNextPage = this.cache[cacheKey].has_next;
            this.loading = false;
            return;
        }

        try {
            console.log('Fetching news with params:', {
                query: this.searchQuery,
                date: this.currentDate,
                startDate: this.startDate,
                endDate: this.endDate,
                groupBy: this.groupBy,
                page: this.currentPage
            });

            const url = new URL('/api/v2/news/', window.location.origin);
            const params = new URLSearchParams({
                query: this.searchQuery,
                page: this.currentPage.toString(),
                page_size: this.pageSize.toString(),
                group_by: this.groupBy
            });

            if (this.startDate && this.endDate) {
                params.append('start_date', this.startDate);
                params.append('end_date', this.endDate);
            } else if (this.currentDate) {
                params.append('date', this.currentDate);
            }

            url.search = params.toString();
            console.log('Fetching URL:', url.toString());  // URL 로깅 추가

            const response = await fetch(url);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '뉴스를 불러오는데 실패했습니다.');
            }
    
            if (data.news_list && data.news_list.length > 0) {
                this.cache[cacheKey] = data;
                this.renderNewsList(data.news_list);
                this.updateNewsCount(data.total_count);
                this.currentPage++;
                this.hasNextPage = data.has_next;
            } else {
                this.hasNextPage = false;
                if (this.currentPage === 1) {
                    this.showEmptyMessage();
                }
            }
        } catch (error) {
            console.error('뉴스 데이터를 가져오는 중 오류 발생:', error);
            this.showError(error.message);
        } finally {
            this.loading = false;
        }
    }

    getCacheKey() {
        return `${this.searchQuery}_${this.currentDate}_${this.startDate}_${this.endDate}_${this.groupBy}_${this.currentPage}`;
    }

    updateNewsCount(count) {
        if (this.newsCountElement) {
            // 총 건의 기사가 있습니다. 텍스트와 숫자 모두 업데이트
            this.newsCountElement.innerHTML = `<span id="news-date"></span> 총 <span class="bold">${count}</span>건의 기사가 있습니다.`;
        }
    }

    showEmptyMessage() {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'text-center py-8 text-gray-500';
        emptyMessage.innerHTML = '검색된 뉴스가 없습니다.';
        this.newsListContainer.appendChild(emptyMessage);
    }

    showError(message) {
        const errorMessage = document.createElement('div');
        errorMessage.className = 'text-center py-8 text-red-500';
        errorMessage.innerHTML = message;
        this.newsListContainer.appendChild(errorMessage);
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

    showPopup(data) {
        const popup = document.createElement('div');
        popup.className = 'popup';
    
        popup.innerHTML = `
            <div class="popup-content">
                <a href="${data.link}" target="_blank" class="original-link">원문 보기</a>
                <h1 class="article-title">${data.title}</h1>
                <div class="press-info">${data.press} ${data.author ? `| ${data.author}` : ''}</div>
                ${data.image ? `<img src="${data.image}" alt="Article Image" class="">` : ''}
                <div class="article-content">${data.content}</div>
                <button class="close-button">닫기</button>
            </div>
        `;
    
        // 팝업 닫기 함수
        function closePopup() {
            document.body.removeChild(popup);
            document.body.style.overflow = 'auto'; // 화면 스크롤 복원
        }
    
        // 배경 클릭 시 팝업 닫기
        popup.addEventListener('click', function (e) {
            if (e.target === popup) {
                closePopup();
            }
        });
    
        // 닫기 버튼 클릭 시 팝업 닫기
        popup.querySelector('.close-button').addEventListener('click', closePopup);
    
        // 팝업을 화면에 추가 및 스크롤 잠금
        document.body.appendChild(popup);
        document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
    }
}
