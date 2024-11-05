from django.urls import path
from .views import home, result, newslist

urlpatterns = [
    path('', home, name='home'),
    path('result/', result, name='result'),
    path('newslist/', newslist, name='newslist'),  # 기본 뉴스 리스트
    path('newslist/<str:date>/', newslist, name='news_list_by_date'),  # 날짜만 필터링
    path('newslist/<str:date>/<str:keyword>/', newslist, name='news_list_by_date_and_keyword'),  # 날짜와 키워드 필터링
]