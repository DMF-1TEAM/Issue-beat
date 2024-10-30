from django.urls import path
from .views import home, resultsam, news, news_chart

urlpatterns = [
    path('', home, name='home'),
    path('result/', resultsam, name='resultsam'),
    path('news/', news, name='news'),
    path('chart/', news_chart, name='chart'),
]