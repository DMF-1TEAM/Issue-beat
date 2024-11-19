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

def test(request):
    news = News.objects.all()
    print(news)

    return None

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
    )

    # 4. 선택된 날짜가 있는 경우 날짜 범위 계산
    if selected_date:
        if group_by == '1week':
            start_date = selected_date - timedelta(days=selected_date.weekday())
            end_date = start_date + timedelta(days=6)
        elif group_by == '1month':
            start_date = selected_date.replace(day=1)
            if selected_date.month == 12:
                end_date = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)
        else:
            start_date = end_date = selected_date

    # 5. 날짜 필터 적용
    queryset = queryset.filter(date__range=[start_date, end_date])

    # 6. 차트 데이터를 위한 집계가 필요한 경우
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

    # 7. 일반 쿼리셋 반환 (최신순 정렬)
    return queryset.order_by('-date')


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
        news_data = [{'title': news.title, 'content': news.content} for news in news_list[::5]]

        if not news_data:
            return Response({
                'background': '검색된 뉴스가 없습니다.',
                'core_content': '검색된 뉴스가 없습니다.',
                'conclusion': '검색된 뉴스가 없습니다.',
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
            'core_content': '요약 생성 중 오류가 발생했습니다.',
            'conclusion': '요약 생성 중 오류가 발생했습니다.',
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
    
# 뉴스 팝업 창 위한 목록 저장 api
def news_detail_api(request, news_id):
    try:
        # 제목으로 뉴스 항목을 조회
        news_item = News.objects.get(id=news_id)
        
        # JSON 형식으로 응답할 데이터 준비
        data = {
            'title': news_item.title,
            'content': news_item.content,
            'press': news_item.press,
            'author': news_item.author,
            'image': news_item.image if news_item.image else None,
            'link': news_item.link
        }
        
        # JSON 응답
        return JsonResponse(data)
    
    except News.DoesNotExist:
        return JsonResponse({'error': '뉴스를 찾을 수 없습니다.'}, status=404)