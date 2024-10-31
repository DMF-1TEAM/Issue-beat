from django.urls import path
from .views import home, resultsam

urlpatterns = [
    path('', home, name='home'),
    path('result/', resultsam, name='resultsam'),
]