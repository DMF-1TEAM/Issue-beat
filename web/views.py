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
#            )

# 차트 데이터 API
@api_view(['GET'])
def news_count_chart_api(request):
    query = request.GET.get('query', '').strip()

    news_list = News.objects.filter(
       Q(title__icontains=query) | Q(content__icontains=query)
    ).order_by('-date')

    daily_counts = news_list.values('date').annotate(
       count=Count('id')
    ).order_by('date')

    daily_counts_dict = {
       item['date'].strftime('%Y-%m-%d'): item['count'] 
       for item in daily_counts
    }

    return Response(daily_counts_dict)

# 요약 API
@api_view(['GET'])
def get_summary_api(request):
   query = request.GET.get('query', '').strip()
   date = request.GET.get('date', '').strip()

   if date:
       news_list = News.objects.filter(
           Q(title__icontains=query) | Q(content__icontains=query),
           date=date
       )
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

   llm_service = LLMService()
   summary = llm_service.generate_structured_summary(
       summary_data,
       search_keyword=query,
       is_overall=True
   )

   return Response(summary)

# 뉴스 목록 API
@api_view(['GET'])
def get_news_api(request):
   query = request.GET.get('query', '').strip()
   date = request.GET.get('date', '').strip()
   page = int(request.GET.get('page', 1))
   page_size = int(request.GET.get('page_size', 10))

   if date:
       news_list = News.objects.filter(
           Q(title__icontains=query) | Q(content__icontains=query),
           date=date
       )
   else:
       news_list = News.objects.filter(
           Q(title__icontains=query) | Q(content__icontains=query)
       )

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




