from django.shortcuts import render
import requests
from .models import News
from django.db.models import Count
import json
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from .pagination import PaginationHandlerMixin
from django.http import JsonResponse

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


class NewsPagination(PageNumberPagination):
    page_size = 10  # 페이지 당 10개의 항목
    page_size_query_param = 'page_size'
    max_page_size = 100  # 최대 100개로 설정 (필요에 따라 변경 가능)

class NewsListView(PaginationHandlerMixin):
    pagination_class = NewsPagination

class NewsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

def resultsam(request):
    if request.is_ajax() and 'url' in request.GET:
        # AJAX 요청 시 뉴스 내용 가져오기 로직
        url = request.GET.get('url')
        if not url:
            return JsonResponse({'error': 'URL is required'}, status=400)

        try:
            response = requests.get(url)
            response.raise_for_status()
            return JsonResponse({'content': response.text})
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)

    # 일반 요청: 뉴스 리스트와 페이지네이션 처리
    news = News.objects.all().order_by('-date')
    paginator = NewsPagination()
    page = paginator.paginate_queryset(news, request)

    if request.is_ajax():
        # AJAX 요청일 때 부분 템플릿을 반환
        return render(request, 'partials/newslist.html', {'page_obj': page})

    context = {
        'page_obj': page,
    }
    return render(request, 'resultsam.html', context)

def resultsam(request):
    news = News.objects.all().order_by('-date')
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        # AJAX 요청일 때 HTML을 반환
        return render(request, 'partials/newslist.html', {'page_obj': page_obj})

    context = {
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
