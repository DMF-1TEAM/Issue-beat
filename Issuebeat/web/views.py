from django.shortcuts import render
import requests
from .models import News
from django.db.models import Count
from datetime import date, timedelta
import json

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
    news = News.objects.all().order_by('-date')

    context={
        'news': news,
    }
    return render(request, 'resultsam.html', context)

def news(request):
    news = News.objects.all().order_by('-date')  # 최신 뉴스 먼저 보기
    return render(request, 'news.html', {'news': news})


def news_chart(request):
    group_by = request.GET.get('group', '1day')  # 기본값은 1일로?

    if group_by == '1day':
        news_data = (News.objects
                      .values('date')
                      .annotate(count=Count('id'))
                      .order_by('date'))
        print(news_data)
    elif group_by == '1week':
        news_data = (News.objects
                      .extra(select={'week': "strftime('%Y-%m-%d', date, 'weekday 0', '-6 days')"})
                      .values('week')
                      .annotate(count=Count('id'))
                      .order_by('week'))
    elif group_by == '1month':
        news_data = (News.objects
                      .extra(select={'month': "strftime('%Y-%m', date)"})
                      .values('month')
                      .annotate(count=Count('id'))
                      .order_by('month'))
    elif group_by == '1year':
        news_data = (News.objects
                      .extra(select={'year': "strftime('%Y', date)"})
                      .values('year')
                      .annotate(count=Count('id'))
                      .order_by('year'))

    date_labels = []
    data_counts = []

    for entry in news_data:
        if group_by == '1day':
            date_labels.append(entry['date'].strftime('%Y-%m-%d'))
        elif group_by == '1week':
            date_labels.append(entry['week'])
        elif group_by == '1month':
            date_labels.append(entry['month'])
        elif group_by == '1year':
            date_labels.append(entry['year'])
        data_counts.append(entry['count'])

    context = {
        'date_labels': json.dumps(date_labels),
        'data_counts': json.dumps(data_counts),
    }
    return render(request, 'chart.html', context)

