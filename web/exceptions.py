from rest_framework.exceptions import APIException
from http import HTTPStatus

class BaseCustomException(APIException):
    """기본 커스텀 예외 클래스"""
    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)
        self.detail = detail or self.default_detail
        self.status_code = self.status_code

class NewsNotFoundException(BaseCustomException):
    status_code = HTTPStatus.NOT_FOUND
    default_detail = '요청하신 뉴스를 찾을 수 없습니다.'

class SearchQueryException(BaseCustomException):
    status_code = HTTPStatus.BAD_REQUEST
    default_detail = '검색어를 확인해주세요.'

class DatabaseException(BaseCustomException):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_detail = '데이터베이스 오류가 발생했습니다.'

class CacheException(BaseCustomException):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    default_detail = '캐시 서버 오류가 발생했습니다.'