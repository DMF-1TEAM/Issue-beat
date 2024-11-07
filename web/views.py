from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import News, SearchHistory
from datetime import datetime, timedelta
from .services.llm_service import LLMService
from .services.daily_issue_service import DailyIssueService

# 데이터를 받아서 각 API로 전달하는 기본 뷰
# def get(self, request):
#     query = request.GET.get('query', '').strip()
#     page = int(request.GET.get('page', 1))
#     page_size = int(request.GET.get('page_size', 10))

#     if not query:
#         return Response({'error': '검색어를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

#     return Response({
#         'query': query,
#         'page': page,
#         'page_size': page_size
#     })

#        if not query:
#            return Response({'error': '검색어를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
           
#        return self._process_request(request, query, page, page_size)
   
#    def _process_request(self, request, query, page, page_size):
#        try:
#            return Response({
#                'success': True,
#                'query': query
#            })
#        except Exception as e:
#            return Response(
#                {'error': '검색 중 오류가 발생했습니다.', 'detail': str(e)}, 
#                status=status.HTTP_500_INTERNAL_SERVER_ERROR

# 세개의 영역에 보내줘야하는 데이터

# 1. 뉴스데이터 날짜별 개수 라인차트 보여주기위한 데이터
# 2. 뉴스 요약 생성
#     2-1. 전체 기간 요약
#     2-2. 차트 클릭시 해당 날짜 요약
# 3. 뉴스 목록(페이지네이션)
#     3-1. 전체 기간 뉴스 목록
#     3-2. 차트 클릭시 해당 날짜 뉴스 목록


# 1. 뉴스데이터 날짜별 개수 라인차트 보여주기위한 데이터 (/api/v2/news/chart/?query=)
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

    # 뉴스 검색
    news_list = News.objects.filter(
        Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-date')

    # 일별 통계 계산
    daily_counts = news_list.values('date').annotate(
        count=Count('id')
    ).order_by('date')

    daily_counts_dict = {
        item['date'].strftime('%Y-%m-%d'): item['count'] 
        for item in daily_counts
    }

    return Response(daily_counts_dict)


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

    # 뉴스 검색
    # 1. 날짜가 주어진 경우 해당 날짜의 키워드 뉴스를 가져옴
    if date:
        news_list = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query),
            date=date
        )
    # 2. 날짜가 주어지지 않은 경우 모든 뉴스를 가져옴
    else:
        news_list = News.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    summary_data = [
        {
            'title': news.title,
            'content': news.content
        }
        for news in news_list
    ]

    # LLM 요약 생성
    llm_service = LLMService()

    summary = llm_service.generate_structured_summary(
        summary_data,
        search_keyword=query,
        is_overall=True
    )

    return Response(summary)


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
    try:
        # 가장 많이 검색된 키워드 상위 5개
        trending = SearchHistory.objects.all()[:5]
        # last_searched 필드로 변경
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
        return JsonResponse({'error': str(e)}, status=500)

def search_view(request):
    query = request.GET.get('query', '').strip()
    if not query:
        return render(request, 'web/search.html')  

    # 검색 기록 업데이트 함수 호출
    update_search_history(query)
    
    return render(request, 'web/search.html', {'query': query})

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

# 마우스 오버시 요약 정보 API
@api_view(['GET'])
def get_hover_summary(request, date):
   try:
       print(f"Fetching hover summary for date: {date}")  
       
       date_obj = datetime.strptime(date, '%Y-%m-%d').date()
       
       analyzer = DailyIssueService()
       summary_data = analyzer.get_daily_summary_data(date_obj)
       
       print(f"Generated summary data: {summary_data}")
       
       return Response(summary_data)
       
   except ValueError as e:
       print(f"Date parsing error: {e}")
       return Response(
           {'error': '잘못된 날짜 형식입니다. (YYYY-MM-DD)'}, 
           status=status.HTTP_400_BAD_REQUEST
       )
   except Exception as e:
       print(f"Error in get_hover_summary: {e}")
       return Response(
           {
               'error': '데이터를 불러오는 중 오류가 발생했습니다.',
               'detail': str(e) if settings.DEBUG else None
           }, 
           status=status.HTTP_500_INTERNAL_SERVER_ERROR
       )