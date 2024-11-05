class NewsList {
    constructor() {
        this.newsListContainer = document.querySelector('#news-list tbody'); // tbody 선택
        this.isLoading = false;

        this.setupInfiniteScroll();
    }

    setupInfiniteScroll() {
        const sentinel = document.getElementById('scroll-sentinel');
        const observer = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && !this.isLoading) {
                this.loadMoreNews(); // 더 많은 뉴스 로드
            }
        });

        observer.observe(sentinel); // 감지할 요소 설정
    }

    async loadMoreNews(date) {
        if (this.isLoading) return;
    
        this.isLoading = true;
        const url = date ? `newslist/${date}?keyword=${encodeURIComponent(keyword)}` : `newslist?keyword=${encodeURIComponent(keyword)}`;
    
        try {
            const response = await fetch(url);
            const data = await response.json();
    
            if (!response.ok) {
                throw new Error('뉴스를 불러오는 중 오류가 발생했습니다.');
            }
    
            this.renderNews(data.news_list);
    
        } catch (error) {
            console.error('Error loading news:', error);
        } finally {
            this.isLoading = false;
        }
    }    

    renderNews(newsList) {
        const newsHTML = newsList.map(news => `
            <tr>
                <td>${news.date}</td>
                <td><a href="${news.link}" target="_blank">${news.title}</a></td>
                <td>${news.press}</td>
            </tr>
        `).join('');
        
        this.newsListContainer.insertAdjacentHTML('beforeend', newsHTML); // tbody에 추가
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const newsList = new NewsList();
    newsList.loadMoreNews(); // 페이지 로드 시 뉴스 불러오기
});
