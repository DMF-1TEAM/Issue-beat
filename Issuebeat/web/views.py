from django.shortcuts import render
import requests
from .models import News

def home(request):
    return render(request, 'home.html')

def result(request, query):
    articles = []
    
    if query:
        # 실제 뉴스 API 호출 로직을 여기에 추가
        url = f'https://newsapi.org/v2/everything?q={query}&apiKey=YOUR_API_KEY'
        response = requests.get(url)
        articles = response.json().get('articles', [])

    return render(request, 'web/result.html', {'articles': articles, 'query': query})

def resultsam(request):
    news= News.objects.all()

    context={
        'news': news,
    }
    return render(request, 'resultsam.html')

def news(request):
    news= News.objects.all()

    context={
        'news': news,
    }
    return render(request, 'news.html', context)