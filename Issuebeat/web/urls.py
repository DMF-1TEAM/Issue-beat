from django.urls import path
from .views import home, result, resultsam, news

urlpatterns = [
    path('', home, name='home'),
    path('<str:query>/result/', result, name='result'),
    path('result/', resultsam, name='resultsam'),
    path('news/', news, name='news')
]