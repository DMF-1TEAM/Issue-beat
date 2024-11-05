from django.db import transaction
from django.core.cache import cache
from .query_optimizer import QueryOptimizer
import asyncio

class DatabaseService:
    @staticmethod
    async def bulk_update_news(news_items):
        """대량 뉴스 업데이트 최적화"""
        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool,
                    DatabaseService._execute_bulk_update,
                    news_items
                )
            
            # 관련 캐시 삭제
            affected_dates = set(item['date'] for item in news_items)
            for date in affected_dates:
                cache_key = CacheKeys.get_news_by_date_key(date)
                cache.delete(cache_key)
                
            return True
        except Exception as e:
            logger.error(f"Bulk update error: {e}")
            return False

    @staticmethod
    @transaction.atomic
    def _execute_bulk_update(news_items):
        """실제 벌크 업데이트 실행"""
        batch_size = 1000
        for i in range(0, len(news_items), batch_size):
            batch = news_items[i:i + batch_size]
            News.objects.bulk_create(
                [News(**item) for item in batch],
                update_conflicts=True,
                update_fields=['title', 'content', 'keyword'],
                unique_fields=['date', 'press', 'link']
            )

    @staticmethod
    def optimize_database():
        """데이터베이스 최적화 작업"""
        with connection.cursor() as cursor:
            # 테이블 분석
            cursor.execute("ANALYZE news_news;")
            # 불필요한 인덱스 정리
            cursor.execute("REINDEX TABLE news_news;")
            # 테이블 최적화
            cursor.execute("VACUUM ANALYZE news_news;")