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
    """
    뉴스 데이터를 필터링하고 집계하는 공통 함수
    """
    # 1. 날짜 파라미터 처리
    if isinstance(start_date, str) and start_date:  # 빈 문자열 체크 추가
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
            
    if isinstance(end_date, str) and end_date:  # 빈 문자열 체크 추가
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
            
    if isinstance(selected_date, str) and selected_date:  # 빈 문자열 체크 추가
        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            selected_date = None

    # 2. 기본 날짜 범위 설정
    if not end_date:
        end_date = datetime.now().date()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    # 3. 기본 쿼리셋 생성 (검색어 필터링)
    queryset = News.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-date')
    # print('news_list:\n',news_list[:10])

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

# 2. 뉴스 요약 생성 (/api/v2/news/summary/?query=keyword&date=2024-11-01)
@api_view(['GET'])
def get_summary_api(request):
    """
    - request
    /api/v2/news/summary/?query=keyword&date=2024-11-01

    - response
    {
        "background": "요약 정보",
        "core_content": "요약 정보",
        "conclusion": "요약 정보"
    }
    """
    query = request.GET.get('query', '').strip()
    date = request.GET.get('date', '').strip()

    try:
        # 저장된 요약이 있는지 확인
        date_obj = datetime.strptime(date, '%Y-%m-%d').date() if date else None
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
        
        # 뉴스 검색
        news_filter = Q(title__icontains=query) | Q(content__icontains=query)
        if date:
            news_filter &= Q(date=date_obj)
        
        news_list = News.objects.filter(news_filter)
        
        summary_data = [{
            'title': news.title,
            'content': news.content
        } for news in news_list]

        # LLM 요약 생성
        llm_service = LLMService()

        summary = llm_service.generate_structured_summary(
            summary_data,
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
    
    except Exception as e:
        return Response(
            {'error': '요약을 생성하는 중 오류가 발생했습니다.', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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

def home(request):
    """홈 페이지"""
    try:
        trending_response = get_trending_keywords_api(request)
        trending_keywords = trending_response.data.get('keywords', [])
    except Exception:
        trending_keywords = []
    return render(request, 'web/home.html', {'trending_keywords': trending_keywords})

# 트렌딩 키워드 API
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
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    try:
        chart_data = get_news_filter(
            query=query,
            group_by=group_by,
            start_date=start_date,
            end_date=end_date,
            for_chart=True
        )

        response_data = [
            {
                "date": item['period'].strftime('%Y-%m-%d'),
                "count": item['count']
            }
            for item in chart_data
        ]

        return Response(response_data)

    except Exception as e:
        print(f"차트 데이터 조회 오류: {e}")
        return Response(
            {'error': '차트 데이터를 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_news_api(request):
    """뉴스 목록 API"""
    try:
        query = request.GET.get('query', '').strip()
        date = request.GET.get('date', '').strip() or None
        group_by = request.GET.get('group_by', '1day').strip()
        start_date = request.GET.get('start_date', '').strip() or None
        end_date = request.GET.get('end_date', '').strip() or None
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        news_list = get_news_filter(
            query=query,
            selected_date=date if not (start_date and end_date) else None,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        paginator = Paginator(news_list, page_size)
        try:
            current_page = paginator.page(page)
        except:
            return Response({
                'news_list': [],
                'total_count': 0,
                'current_page': page,
                'total_pages': 0,
                'has_next': False,
                'has_previous': False
            })

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
    try:
        query = request.GET.get('query', '').strip()
        date = request.GET.get('date', '').strip()
        group_by = request.GET.get('group_by', '1day').strip()
        start_date = request.GET.get('start_date', '').strip() or None
        end_date = request.GET.get('end_date', '').strip() or None

        # date가 빈 문자열이면 None으로 설정
        date = date or None
        
        news_list = get_news_filter(
            query=query,
            selected_date=date if not (start_date and end_date) else None,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )

        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                if group_by == '1week':
                    period_start = date_obj - timedelta(days=date_obj.weekday())
                elif group_by == '1month':
                    period_start = date_obj.replace(day=1)
                else:
                    period_start = date_obj
            except ValueError:
                period_start = None
        else:
            period_start = None
            if start_date:
                try:
                    period_start = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    period_start = None

        # 캐시된 요약 확인
        saved_summary = None
        if period_start:
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

        # 최대 50개의 뉴스로 제한하여 요약 생성
        news_data = [{'title': news.title, 'content': news.content} for news in news_list[:50]]

        if not news_data:
            return Response({
                'background': '검색된 뉴스가 없습니다.',
                'core_content': '검색 조건을 변경해보세요.',
                'conclusion': '',
                'is_empty': True
            })

        llm_service = LLMService()
        summary = llm_service.generate_structured_summary(
            news_data,
            search_keyword=query,
            is_overall=not bool(date)
        )

        # 요약 결과 캐시 저장
        if period_start:
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
        
        # 1. 날짜 객체로 변환
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # 2. 날짜 범위 계산
        issue_service = DailyIssueService()
        start_date, end_date = issue_service.get_period_range(date_obj, group_by)

        # 3. 뉴스 데이터 조회 (전체 기간)
        news_list = get_news_filter(
            query=query,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        # 4. 요약 생성
        summary_data = issue_service.get_cached_summary(
            date=date_obj,
            query=query,
            group_by=group_by,
            news_list=news_list
        )
        
        # 5. 응답 데이터 구성
        response_data = {
            'date': f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            **summary_data
        }
        
        return Response(response_data)

    except Exception as e:
        print(f"호버 요약 조회 오류: {e}")
        return Response(
            {'error': '요약을 불러오는데 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )