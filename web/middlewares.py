from django.http import JsonResponse
from django.db import DatabaseError
from redis.exceptions import RedisError
import logging
import traceback

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.handle_exception(e)

    def handle_exception(self, exc):
        if isinstance(exc, BaseCustomException):
            return JsonResponse({
                'error': {
                    'message': exc.detail,
                    'code': exc.status_code
                }
            }, status=exc.status_code)
        elif isinstance(exc, DatabaseError):
            logger.error(f"Database error: {traceback.format_exc()}")
            return JsonResponse({
                'error': {
                    'message': '데이터베이스 오류가 발생했습니다.',
                    'code': 500
                }
            }, status=500)
        elif isinstance(exc, RedisError):
            logger.error(f"Redis error: {traceback.format_exc()}")
            return JsonResponse({
                'error': {
                    'message': '캐시 서버 오류가 발생했습니다.',
                    'code': 500
                }
            }, status=500)
        else:
            logger.error(f"Unexpected error: {traceback.format_exc()}")
            return JsonResponse({
                'error': {
                    'message': '알 수 없는 오류가 발생했습니다.',
                    'code': 500
                }
            }, status=500)
