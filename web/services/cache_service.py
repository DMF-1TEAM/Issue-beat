from django.core.cache import cache
from datetime import datetime, timedelta
import pickle
import zlib

class CacheService:
    @staticmethod
    def compress_data(data):
        """데이터 압축"""
        pickled = pickle.dumps(data)
        compressed = zlib.compress(pickled)
        return compressed

    @staticmethod
    def decompress_data(compressed_data):
        """데이터 압축 해제"""
        if not compressed_data:
            return None
        pickled = zlib.decompress(compressed_data)
        return pickle.loads(pickled)

    @staticmethod
    def cache_set(key, data, timeout=3600):
        """압축된 데이터 캐시 저장"""
        compressed = CacheService.compress_data(data)
        cache.set(key, compressed, timeout)

    @staticmethod
    def cache_get(key):
        """압축된 데이터 캐시 조회"""
        compressed = cache.get(key)
        if compressed is None:
            return None
        return CacheService.decompress_data(compressed)

    @staticmethod
    def cache_delete_pattern(pattern):
        """패턴에 매칭되는 캐시 삭제"""
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)
