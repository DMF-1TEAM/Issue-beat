from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'web'

urlpatterns = [
    # 웹 페이지 URL
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'),
    path('api/news/search/', views.SearchNewsAPIView.as_view(), name='search_api'),
    path('api/news/hover-summary/<str:date>/', views.get_hover_summary, name='hover_summary'),  # 추가된 부분
    path('api/news/date/<str:date>/', views.get_news_by_date, name='news_by_date'),
    path('api/news/summary/<str:date>/', views.get_daily_summary, name='daily_summary'),
    path('api/trending/', views.get_trending_keywords_api, name='trending_keywords'),
    path('api/stats/daily/', views.get_daily_stats, name='daily_stats'),
    path('api/suggestions/', views.get_search_suggestions_api, name='suggestions'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 