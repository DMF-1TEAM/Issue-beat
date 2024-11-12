from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db.models import Min, Max
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.core.paginator import Paginator
from .models import News, SearchHistory, NewsSummary
from datetime import datetime, timedelta
from .services.llm_service import LLMService
from .services.daily_issue_service import DailyIssueService

def home(request):
    """홈 페이지"""
    try:
        trending_response = get_trending_keywords_api(request)
        trending_keywords = trending_response.data.get('keywords', [])
    except Exception:
        trending_keywords = []
    return render(request, 'web/home.html', {'trending_keywords': trending_keywords})

def search_view(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return render(request, 'web/search.html')  # 검색 페이지 템플릿 렌더링

    search_history, created = SearchHistory.objects.get_or_create(
        keyword=query,
        defaults={'count': 1}
    )
    if not created:
        search_history.count += 1
        search_history.save()

    return render(request, 'web/search.html', {'query': query})

@api_view(['GET'])
def news_count_chart_api(request):
    """
    - request
    /api/v2/news/?query=검색어
    - response
    [
        {
            "date": "2024-11-01",
            "count": 9
        },
        {
            "date": "2024-11-02",
            "count": 6
        },
        {
            "date": "2024-11-03",
            "count": 5
        },
        {
            "date": "2024-11-04",
            "count": 2
        }
    ]
    """
    query = request.GET.get('query', '').strip()
    group_by = request.GET.get('group_by', '1day').strip()

    # 뉴스 검색: query를 사용해 제목과 내용에서 검색어 포함된 뉴스만 필터링
    news_list = News.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-date')
    # print('news_list:\n',news_list[:10])

    # 뉴스가 없는 경우 빈 배열 반환
    if not news_list.exists():
        return Response([])

    # 차트 데이터 생성 전에 요약 캐시 준비
    summary_cache = DailyIssueService()
    summary_cache.prepare_daily_summaries(query, news_list)

    # 시작 끝 날짜 
    min_date = news_list.earliest('date').date
    max_date = news_list.latest('date').date

    # agg_by_date 함수로 날짜별 집계 결과를 받음
    date_labels, data_counts = agg_by_date(news_list, group_by, min_date, max_date)

    # 날짜별 카운트 결과 반환
    chart_data = [
        {"date": date, "count": count}
        for date, count in zip(date_labels, data_counts)
    ]

    return Response(chart_data)

def agg_by_date(news_list, group_by, min_date, max_date):
    date_labels = []
    data_counts = []

    # 기준에 따른 날짜 범위 생성
    # print(group_by)
    if group_by == '1day':

        date_range = [min_date + timedelta(days=i) for i in range((max_date - min_date).days + 1)]
        
        news_data = (news_list
                        .values('date')
                        .annotate(count=Count('id'))
                        .order_by('date'))
        
        news_data_dict = {entry['date']: entry['count'] for entry in news_data}

        for single_date in date_range:
            date_labels.append(single_date.strftime('%Y-%m-%d'))
            data_counts.append(news_data_dict.get(single_date, 0))

    elif group_by == '1week':

        date_range = []
        current_date = min_date

        while current_date <= max_date:
            date_range.append(current_date)
            current_date += timedelta(weeks=1)

        news_data = (news_list
                     .filter(date__range=[min_date, max_date])
                     .annotate(week=TruncWeek('date'))
                     .values('week')
                     .annotate(count=Count('id'))
                     .order_by('week'))

        news_data_dict = {entry['week'].strftime('%Y-%m-%d'): entry['count'] for entry in news_data}

        for single_week in date_range:
            week_str = single_week.strftime('%Y-%m-%d')
            date_labels.append(week_str)
            data_counts.append(news_data_dict.get(week_str, 0))

    elif group_by == '1month':

        date_range = []
        current_date = min_date.replace(day=1)

        while current_date <= max_date:
            date_range.append(current_date)
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        
        news_data = (news_list
                     .filter(date__range=[min_date, max_date])
                     .annotate(month=TruncMonth('date'))
                     .values('month')
                     .annotate(count=Count('id'))
                     .order_by('month'))
        
        news_data_dict = {entry['month'].strftime('%Y-%m'): entry['count'] for entry in news_data}

        for single_month in date_range:
            month_str = single_month.strftime('%Y-%m')
            date_labels.append(month_str)
            data_counts.append(news_data_dict.get(month_str, 0))

    return date_labels, data_counts

@api_view(['GET'])
def get_hover_summary(request, date):
    """특정 날짜의 요약 정보를 반환하는 API"""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        query = request.GET.get('query', '').strip()
        
        issue_service = DailyIssueService()
        summary_data = issue_service.get_cached_summary(date_obj, query)
        
        return Response(summary_data)

    except ValueError:
        return Response(
            {'error': '잘못된 날짜 형식입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
def get_summary_api(request):
    """전체 또는 특정 날짜의 뉴스 요약 API"""
    query = request.GET.get('query', '').strip()
    date = request.GET.get('date', '').strip()
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else None

        # 캐시된 요약 확인
        saved_summary = NewsSummary.objects.filter(
            keyword=query,
            date=date_obj
        ).first()

        if saved_summary:
            return Response({
                'background': saved_summary.background,
                'core_content': saved_summary.core_content,
                'conclusion': saved_summary.conclusion,
                'cached': True
            })

        # 뉴스 필터링
        news_filter = Q(title__icontains=query) | Q(content__icontains=query)
        if date:
            news_filter &= Q(date=date_obj)
        
        news_list = News.objects.filter(news_filter).order_by('-date')[:50]

        # 새로운 요약 생성
        llm_service = LLMService()
        summary = llm_service.generate_structured_summary(
            [{'title': news.title, 'content': news.content} for news in news_list],
            search_keyword=query,
            is_overall=not bool(date)
        )

        # 요약 저장
        NewsSummary.objects.create(
            keyword=query,
            date=date_obj,
            background=summary['background'],
            core_content=summary['core_content'],
            conclusion=summary['conclusion']
        )

        return Response(summary)

    except ValueError:
        return Response(
            {'error': '잘못된 날짜 형식입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        print(f"요약 API 오류: {e}")
        return Response({
            'background': '요약 생성 중 오류가 발생했습니다.',
            'core_content': '잠시 후 다시 시도해주세요.',
            'conclusion': '',
            'is_error': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 3. 뉴스 목록(페이지네이션) (/api/v2/news/?query=keyword&date=2024-11-01&page=1&page_size=10)
@api_view(['GET'])
def get_news_api(request):
    """
    - request
    /api/v2/news/?query=keyword&date=2024-11-01&page=1&page_size=10

    - response
    {
        "news_list": [
            {
                "id": 1,
                "title": "뉴스 제목",
                "content": "뉴스 내용",
                "press": "언론사",
                "date": "2024-11-01",
                "link": "뉴스 링크"
            },
            {
                "id": 2,
                "title": "뉴스 제목",
                "content": "뉴스 내용",
                "press": "언론사",
                "date": "2024-11-01",
                "link": "뉴스 링크"
            }
        ],
        "total_count": 10,
        "current_page": 1,
        "total_pages": 2,
        "has_next": true,
        "has_previous": false
    }
    """

    query = request.GET.get('query', '').strip()
    date = request.GET.get('date', '').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    # 뉴스 검색
    # 1. 날짜가 주어진 경우 해당 날짜의 키워드 뉴스를 가져옴
    if date:
        news_list = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            date=date
        ).order_by('-date')
    # 2. 날짜가 주어지지 않은 경우 모든 뉴스를 가져옴
    else:
        news_list = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).order_by('-date')

    # 페이지네이션
    paginator = Paginator(news_list, page_size)
    current_page = paginator.page(page)

    news_data = [{
        'id': news.id,
        'title': news.title,
        'content': news.content,
        'press': news.press,
        'date': news.date.strftime('%Y-%m-%d') if news.date else None,
        'link': news.link
    } for news in current_page.object_list]

    return Response({
        'news_list': news_data,
        'total_count': news_list.count(),
        'current_page': page,
        'total_pages': paginator.num_pages,
        'has_next': current_page.has_next(),
        'has_previous': current_page.has_previous()
    })



# 트렌딩 키워드 API
@api_view(['GET'])
def get_trending_keywords_api(request):
    """트렌딩 키워드 API"""
    try:
        trending = SearchHistory.objects.order_by('-count')[:5]
        return JsonResponse({
            'keywords': [
                {
                    'keyword': item.keyword, 
                    'count': item.count,
                    'last_searched': item.last_searched.strftime('%Y-%m-%d %H:%M:%S')
                } 
                for item in trending
            ]
        })
    except Exception as e:
        print(f"트렌딩 키워드 API 오류: {e}")
        return JsonResponse(
            {'error': '트렌딩 키워드를 불러오는 중 오류가 발생했습니다.'},
            status=500
        )

def update_search_history(keyword):
    """검색 기록을 업데이트하거나 생성하는 함수"""
    try:
        search_history, created = SearchHistory.objects.get_or_create(
            keyword=keyword,
            defaults={'count': 1}
        )
        
        if not created:
            search_history.count += 1
            search_history.save()
            
        return search_history
    except Exception as e:
        print(f"Error updating search history: {e}")
        return None

@api_view(['GET'])
def get_search_suggestions_api(request):
    """검색어 자동완성 API"""
    query = request.GET.get('query', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    try:
        suggestions = News.objects.filter(
            title__icontains=query
        ).values_list('title', flat=True).distinct()[:5]
        
        return JsonResponse({'suggestions': list(suggestions)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)