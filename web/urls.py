from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'web'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'),
<<<<<<< HEAD
    # path('api/news/search/', views.SearchNewsAPIView.as_view(), name='search_api'),
    # path('api/news/hover-summary/<str:date>/', views.get_hover_summary, name='hover_summary'),  # 추가된 부분
    # path('api/news/date/<str:date>/', views.get_news_by_date, name='news_by_date'),
    # path('api/news/summary/<str:date>/', views.get_daily_summary, name='daily_summary'),
    # path('api/trending/', views.get_trending_keywords_api, name='trending_keywords'),
    # path('api/stats/daily/', views.get_daily_stats, name='daily_stats'),
    # path('api/suggestions/', views.get_search_suggestions_api, name='suggestions'),

    path('api/v2/news/chart/', views.news_count_chart_api, name='news_count_chart_api'),
    path('api/v2/news/summary/', views.get_summary_api, name='get_summary_api'),
    path('api/v2/news/', views.get_news_api, name='get_news_api'),
=======
    path('api/news/search/', views.SearchNewsAPIView.as_view(), name='search_api'),
    path('api/news/hover-summary/<str:date>/', views.get_hover_summary, name='hover_summary'),  # 추가된 부분
    path('api/news/date/<str:date>/', views.get_news_by_date, name='news_by_date'),
    path('api/news/summary/<str:date>/', views.get_daily_summary, name='daily_summary'),
    path('api/trending/', views.get_trending_keywords_api, name='trending_keywords'),
    path('api/stats/daily/', views.get_daily_stats, name='daily_stats'),
    path('api/suggestions/', views.get_search_suggestions_api, name='suggestions'),
>>>>>>> master
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 