from django.shortcuts import render
import requests
from .models import News
from django.db.models import Count
import json
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from .pagination import PaginationHandlerMixin
from django.http import JsonResponse
from datetime import timedelta, datetime

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
    group_by = request.GET.get('group', '1day')  # 기본값은 1일
    news_data = []
    date_labels = []
    data_counts = []

    # 데이터가 존재하는 시작일과 종료일 가져오기
    min_date = News.objects.earliest('date').date
    max_date = News.objects.latest('date').date

    # 그룹화 방식에 따른 날짜 범위 생성
    if group_by == '1day':
        # 일 단위 그룹화
        date_range = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]
        news_data = (News.objects
                      .values('date')
                      .annotate(count=Count('id'))
                      .order_by('date'))
        news_data_dict = {entry['date']: entry['count'] for entry in news_data}
        
        for single_date in date_range:
            date_labels.append(single_date.strftime('%Y-%m-%d'))
            data_counts.append(news_data_dict.get(single_date, 0))
    
    elif group_by == '1week':
        # 주 단위 그룹화
        date_range = []
        current_date = min_date
        while current_date <= max_date:
            date_range.append(current_date)
            current_date += timedelta(weeks=1)

        news_data = (News.objects
                      .extra(select={'week': "strftime('%Y-%m-%d', date, 'weekday 0', '-6 days')"})
                      .values('week')
                      .annotate(count=Count('id'))
                      .order_by('week'))
        news_data_dict = {entry['week']: entry['count'] for entry in news_data}

        for single_week in date_range:
            week_str = single_week.strftime('%Y-%m-%d')
            date_labels.append(week_str)
            data_counts.append(news_data_dict.get(week_str, 0))

    elif group_by == '1month':
        # 월 단위 그룹화
        date_range = []
        current_date = min_date.replace(day=1)
        while current_date <= max_date:
            date_range.append(current_date)
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        news_data = (News.objects
                      .extra(select={'month': "strftime('%Y-%m', date)"})
                      .values('month')
                      .annotate(count=Count('id'))
                      .order_by('month'))
        news_data_dict = {entry['month']: entry['count'] for entry in news_data}

        for single_month in date_range:
            month_str = single_month.strftime('%Y-%m')
            date_labels.append(month_str)
            data_counts.append(news_data_dict.get(month_str, 0))

    elif group_by == '1year':
        # 연 단위 그룹화
        date_range = []
        current_date = min_date.replace(month=1, day=1)
        while current_date <= max_date:
            date_range.append(current_date)
            current_date = current_date.replace(year=current_date.year + 1)

        news_data = (News.objects
                      .extra(select={'year': "strftime('%Y', date)"})
                      .values('year')
                      .annotate(count=Count('id'))
                      .order_by('year'))
        news_data_dict = {entry['year']: entry['count'] for entry in news_data}

        for single_year in date_range:
            year_str = single_year.strftime('%Y')
            date_labels.append(year_str)
            data_counts.append(news_data_dict.get(year_str, 0))

    context = {
        'date_labels': json.dumps(date_labels),
        'data_counts': json.dumps(data_counts),
    }
    return render(request, 'chart.html', context)