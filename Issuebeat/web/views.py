from django.shortcuts import render
from .models import News
from django.db.models import Count
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
import json
from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from .pagination import PaginationHandlerMixin
from datetime import timedelta
from django.utils.dateparse import parse_date
from django.http import JsonResponse


def home(request):
    return render(request, 'home.html')

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
    # 뉴스 데이터 및 페이지네이션
    selected_date = request.GET.get('date', '')
    news = News.objects.all().order_by('-date')
    if selected_date:
        news = news.filter(date=selected_date)
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    keyword = request.GET.get('q', '')

    # 차트 데이터 생성
    group_by = request.GET.get('group', '1day')  # 기본값은 1일
    date_labels = []
    data_counts = []
    images = []

    # 데이터가 존재하는 시작일과 종료일 가져오기
    min_date = News.objects.earliest('date').date
    max_date = News.objects.latest('date').date

    # 그룹화 방식에 따른 날짜 범위 생성
    if group_by == '1day':
        date_range = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]
        news_data = (News.objects
                      .values('date')
                      .annotate(count=Count('id'))
                      .order_by('date'))
        news_data_dict = {entry['date']: entry['count'] for entry in news_data}
        
        for single_date in date_range:
            date_labels.append(single_date.strftime('%Y-%m-%d'))
            data_counts.append(news_data_dict.get(single_date, 0))
            try:
                image_url = News.objects.filter(date=single_date).first().image
                images.append(image_url)
            except AttributeError:
                images.append('')

    elif group_by == '1week':
        date_range = []
        current_date = min_date
        while current_date <= max_date:
            date_range.append(current_date)
            current_date += timedelta(weeks=1)

        news_data = (News.objects
                      .annotate(week=TruncWeek('date')) 
                      .values('week')
                      .annotate(count=Count('id'))
                      .order_by('week'))
        news_data_dict = {entry['week']: entry['count'] for entry in news_data}

        for single_week in date_range:
            week_str = single_week.strftime('%Y-%m-%d')
            date_labels.append(week_str)
            data_counts.append(news_data_dict.get(single_week, 0))
            try:
                image_url = News.objects.filter(date__range=[single_week, single_week + timedelta(days=6)]).first().image
                images.append(image_url)
            except AttributeError:
                images.append('')

    elif group_by == '1month':
        date_range = []
        current_date = min_date.replace(day=1)
        while current_date <= max_date:
            date_range.append(current_date)
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        news_data = (News.objects
                      .annotate(month=TruncMonth('date'))
                      .values('month')
                      .annotate(count=Count('id'))
                      .order_by('month'))
        news_data_dict = {entry['month']: entry['count'] for entry in news_data}

        for single_month in date_range:
            month_str = single_month.strftime('%Y-%m')
            date_labels.append(month_str)
            data_counts.append(news_data_dict.get(month_str, 0))
            try:
                image_url = News.objects.filter(date__month=single_month.month, date__year=single_month.year).first().image
                images.append(image_url)
            except AttributeError:
                images.append('')

    elif group_by == '1year':
        date_range = []
        current_date = min_date.replace(month=1, day=1)
        while current_date <= max_date:
            date_range.append(current_date)
            current_date = current_date.replace(year=current_date.year + 1)

        news_data = (News.objects
                      .annotate(year=TruncYear('date'))
                      .values('year')
                      .annotate(count=Count('id'))
                      .order_by('year'))
        news_data_dict = {entry['year']: entry['count'] for entry in news_data}

        for single_year in date_range:
            year_str = single_year.strftime('%Y')
            date_labels.append(year_str)
            data_counts.append(news_data_dict.get(year_str, 0))
            try:
                image_url = News.objects.filter(date__year=single_year.year).first().image
                images.append(image_url)
            except AttributeError:
                images.append('')

    # Context에 차트 데이터 추가
    context = {
        'keyword': keyword,
        'page_obj': page_obj,
        'date_labels': json.dumps(date_labels),
        'data_counts': json.dumps(data_counts),
        'images': json.dumps(images),  # 이미지 리스트 추가
        'news': news,
    }

    # AJAX 요청일 때 부분 템플릿 반환
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        return render(request, 'partials/newslist.html', context)

    return render(request, 'resultsam.html', context)

def result(request):
    keyword = request.GET.get('keyword', '')  # URL 쿼리 파라미터로 키워드 가져오기
    news_query = News.objects.filter(keyword__icontains=keyword).order_by('-date') if keyword else News.objects.all().order_by('-date')
    initial_news = news_query[:10]  # 초기 데이터로 10개의 뉴스만 전달s
    
    context = {
        "initial_news": initial_news,
        "keyword": keyword,
    }
    return render(request, "result.html", context)


def newslist(request, date=None, keyword=None):
    news_query = News.objects.all()
    
    # 키워드 필터링
    if keyword:
        news_query = news_query.filter(title__icontains=keyword)
    
    # 날짜 필터링
    if date:
        date_obj = parse_date(date)
        if date_obj:
            news_query = news_query.filter(date=date_obj)

    # 뉴스 정렬 및 제한
    news = news_query.order_by('-date')[:10]
    newslist = [
        {
            "date": n.date.strftime("%Y-%m-%d"),
            "title": n.title,
            "link": n.link,
            "press": n.press
        }
        for n in news
    ]
    return JsonResponse({"newslist": newslist})