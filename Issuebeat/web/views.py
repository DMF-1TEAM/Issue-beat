from django.shortcuts import render
import requests

def home(request):
    return render(request, 'home.html')

def result(request, query):
    articles = []
    
    if query:
        # 실제 뉴스 API 호출 로직을 여기에 추가합니다.
        url = f'https://newsapi.org/v2/everything?q={query}&apiKey=YOUR_API_KEY'
        response = requests.get(url)
        articles = response.json().get('articles', [])

    return render(request, 'web/result.html', {'articles': articles, 'query': query})