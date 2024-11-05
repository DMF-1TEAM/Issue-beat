from django.db import connection
from django.db.models import Q
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def query_debugger(func):
    """쿼리 성능 디버깅 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        reset_queries()
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        queries = connection.queries
        query_count = len(queries)
        query_time = sum(float(q['time']) for q in queries)
        
        logger.debug(f"""
            Function: {func.__name__}
            Query Count: {query_count}
            Total Query Time: {query_time}
            Total Time: {end - start}
        """)
        
        return result
    return wrapper

class QueryOptimizer:
    @staticmethod
    def optimize_news_query(queryset, filters=None, prefetch_fields=None):
        """뉴스 쿼리 최적화"""
        if filters:
            queryset = queryset.filter(**filters)
        
        # 필요한 필드만 선택
        queryset = queryset.defer(
            'content',  # 큰 텍스트 필드는 필요할 때만 로드
            'image'     # 이미지 URL도 필요할 때만 로드
        )
        
        # Prefetch 관련 필드
        if prefetch_fields:
            for field in prefetch_fields:
                queryset = queryset.prefetch_related(field)
        
        return queryset

    @staticmethod
    def build_search_query(search_terms):
        """검색 쿼리 최적화"""
        query = Q()
        
        for term in search_terms:
            term_query = Q()
            # 정확한 키워드 매칭 우선
            term_query |= Q(keyword__iexact=term)
            # 부분 매칭
            term_query |= Q(title__icontains=term)
            term_query |= Q(content__icontains=term)
            
            query &= term_query
        
        return query