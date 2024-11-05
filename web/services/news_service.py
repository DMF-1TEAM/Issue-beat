from django.db.models import Prefetch, Count, Q
from django.core.cache import cache
from .cache_service import CacheService, CacheKeys
import asyncio
import concurrent.futures

class NewsService:
    @staticmethod
    async def get_news_by_date(date, page=1, page_size=20):
        """날짜별 뉴스 조회 with 캐싱"""
        cache_key = CacheKeys.get_news_by_date_key(f"{date}:{page}")
        cached_data = CacheService.cache_get(cache_key)

        if cached_data:
            return cached_data

        try:
            # 비동기로 DB 쿼리 실행
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                news_data = await loop.run_in_executor(
                    pool,
                    NewsService._fetch_news_data,
                    date, page, page_size
                )

            CacheService.cache_set(cache_key, news_data, 1800)  # 30분 캐시
            return news_data
        except Exception as e:
            print(f"Error fetching news: {e}")
            return None

    @staticmethod
    def _fetch_news_data(date, page, page_size):
        """실제 DB 쿼리 실행"""
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        # 쿼리 최적화
        queryset = News.objects.filter(date=date).select_related(
            'press'
        ).only(
            'title', 'press', 'author', 'link', 'content'
        ).order_by('-press')

        return {
            'news': list(queryset[start_idx:end_idx].values(
                'title', 'press', 'author', 'link'
            )),
            'total_count': queryset.count()
        }

    @staticmethod
    async def get_daily_stats(days=30):
        """일별 통계 조회 with 캐싱"""
        cache_key = CacheKeys.get_daily_stats_key(days)
        cached_data = CacheService.cache_get(cache_key)

        if cached_data:
            return cached_data

        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                stats_data = await loop.run_in_executor(
                    pool,
                    NewsService._fetch_daily_stats,
                    days
                )

            CacheService.cache_set(cache_key, stats_data, 3600)  # 1시간 캐시
            return stats_data
        except Exception as e:
            print(f"Error fetching daily stats: {e}")
            return None

    @staticmethod
    def _fetch_daily_stats(days):
        """실제 일별 통계 쿼리 실행"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        return list(News.objects.filter(
            date__range=(start_date, end_date)
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date'))