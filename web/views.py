from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from .models import News, SearchHistory, NewsSummary, DailySummary
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
    """검색 페이지"""
    query = request.GET.get('query', '').strip()
    if not query:
        return render(request, 'web/search.html')

    search_history, created = SearchHistory.objects.get_or_create(
        keyword=query,
        defaults={'count': 1}
    )
    if not created:
        search_history.count += 1
        search_history.save()

    return render(request, 'web/search.html', {'query': query})

def get_news_filter(query, group_by='1day', start_date=None, end_date=None, selected_date=None, for_chart=False):
    """뉴스 데이터를 필터링하고 집계하는 공통 함수"""

    print("Start Date:", start_date)
    print("End Date:", end_date)

    # 기본 날짜 범위 설정 (1년)
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    # 기본 쿼리셋
    queryset = News.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-date')

    # 날짜 필터링
    if selected_date:
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date() if isinstance(selected_date, str) else selected_date
        
        if group_by == '1week':
            # 해당 주의 월요일과 일요일 찾기
            start_date = date_obj - timedelta(days=date_obj.weekday())
            end_date = start_date + timedelta(days=6)
        elif group_by == '1month':
            # 해당 월의 첫날과 마지막 날 찾기
            start_date = date_obj.replace(day=1)
            if date_obj.month == 12:
                end_date = date_obj.replace(year=date_obj.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = date_obj.replace(month=date_obj.month + 1, day=1) - timedelta(days=1)
        else:  # 1day
            start_date = end_date = date_obj

    queryset = queryset.filter(date__range=[start_date, end_date])

    # 차트를 위한 데이터 집계
    if for_chart:
        trunc_map = {
            '1day': TruncDay,
            '1week': TruncWeek,
            '1month': TruncMonth
        }
        trunc_func = trunc_map.get(group_by, TruncDay)
        return (queryset
                .annotate(period=trunc_func('date'))
                .values('period')
                .annotate(count=Count('id'))
                .order_by('period'))

    return queryset

@api_view(['GET'])
def get_trending_keywords_api(request):
    """트렌딩 키워드 API"""
    try:
        trending = SearchHistory.objects.order_by('-count')[:5]
        return Response({
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
        return Response(
            {'error': '트렌딩 키워드를 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

@api_view(['GET'])
def news_count_chart_api(request):
    """뉴스 집계 차트 API"""
    query = request.GET.get('query', '').strip()
    group_by = request.GET.get('group_by', '1day').strip()
    start_date = request.GET.get('start_date','')
    end_date = request.GET.get('end_date', '')

    try:
        chart_data = get_news_filter(
            query=query,
            group_by=group_by,
            start_date=start_date,
            end_date=end_date,
            for_chart=True  # 차트용 데이터 요청
        )

        response_data = [
            {
                "date": item['period'].strftime('%Y-%m-%d'),
                "count": item['count']
            }
            for item in chart_data
        ]

        print(response_data)
        
        return Response(response_data)

    except Exception as e:
        print(f"차트 데이터 전송 오류: {e}")
        return Response(
            {'error': '차트 데이터를 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_news_api(request):
    """뉴스 목록 API"""
    query = request.GET.get('query', '').strip()
    date = request.GET.get('date', '').strip()
    group_by = request.GET.get('group_by', '1day').strip()
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    try:
        news_list = get_news_filter(
            query=query,
            selected_date=date,
            group_by=group_by,
            for_chart=False  # 뉴스 목록 요청
        )

        paginator = Paginator(news_list, page_size)
        current_page = paginator.page(page)

        return Response({
            'news_list': [
                {
                    'id': news.id,
                    'title': news.title,
                    'content': news.content,
                    'press': news.press,
                    'date': news.date.strftime('%Y-%m-%d'),
                    'link': news.link
                }
                for news in current_page.object_list
            ],
            'total_count': news_list.count(),
            'current_page': page,
            'total_pages': paginator.num_pages,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous()
        })

    except Exception as e:
        print(f"뉴스 목록 조회 오류: {e}")
        return Response(
            {'error': '뉴스 목록을 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_summary_api(request):
    """뉴스 요약 API"""
    query = request.GET.get('query', '').strip()
    date = request.GET.get('date', '').strip()
    group_by = request.GET.get('group_by', '1day').strip()
    
    try:
        news_list = get_news_filter(
            query=query,
            selected_date=date,
            group_by=group_by
        )

        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            if group_by == '1week':
                period_start = date_obj - timedelta(days=date_obj.weekday())
            elif group_by == '1month':
                period_start = date_obj.replace(day=1)
            else:
                period_start = date_obj
        else:
            period_start = None

        # 캐시된 요약 확인
        saved_summary = NewsSummary.objects.filter(
            keyword=query,
            date=period_start,
            group_by=group_by
        ).first()

        if saved_summary:
            return Response({
                'background': saved_summary.background,
                'core_content': saved_summary.core_content,
                'conclusion': saved_summary.conclusion,
                'cached': True
            })

        # 새로운 요약 생성
        news_data = [
            {
                'title': news.title,
                'content': news.content
            }
            for news in news_list[:50]
        ]

        llm_service = LLMService()
        summary = llm_service.generate_structured_summary(
            news_data,
            search_keyword=query,
            is_overall=not bool(date)
        )

        # 요약 저장
        NewsSummary.objects.create(
            keyword=query,
            date=period_start,
            group_by=group_by,
            background=summary['background'],
            core_content=summary['core_content'],
            conclusion=summary['conclusion']
        )

        return Response(summary)

    except Exception as e:
        print(f"요약 생성 오류: {e}")
        return Response({
            'background': '요약 생성 중 오류가 발생했습니다.',
            'core_content': '잠시 후 다시 시도해주세요.',
            'conclusion': '',
            'is_error': True
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_hover_summary(request, date):
    """차트 호버 요약 API"""
    try:
        query = request.GET.get('query', '').strip()
        group_by = request.GET.get('group_by', '1day').strip()
        
        news_list = get_news_filter(
            query=query,
            selected_date=date,
            group_by=group_by
        )
        
        issue_service = DailyIssueService()
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        if group_by == '1week':
            period_start = date_obj - timedelta(days=date_obj.weekday())
        elif group_by == '1month':
            period_start = date_obj.replace(day=1)
        else:
            period_start = date_obj
            
        summary_data = issue_service.get_cached_summary(period_start, query, group_by)
        
        if not summary_data:
            issue_service.prepare_daily_summaries(query, news_list, group_by)
            summary_data = issue_service.get_cached_summary(period_start, query, group_by)
        
        return Response(summary_data)

    except Exception as e:
        print(f"호버 요약 조회 오류: {e}")
        return Response(
            {'error': '요약을 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )