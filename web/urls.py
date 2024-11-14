from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'web'

urlpatterns = [
    # 웹 페이지 URL
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'),

    # v2 뉴스 검색 관련 API
    path('api/v2/news/chart/', views.news_count_chart_api, name='news_count_chart_api'),
    path('api/v2/news/summary/', views.get_summary_api, name='get_summary_api'),
    path('api/v2/news/', views.get_news_api, name='get_news_api'),

    # 추가 기능 API
    path('api/trending/', views.get_trending_keywords_api, name='trending_keywords'),
    path('api/suggestions/', views.get_search_suggestions_api, name='search_suggestions'),
    path('api/v2/news/hover-summary/<str:date>/', views.get_hover_summary, name='get_hover_summary'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
