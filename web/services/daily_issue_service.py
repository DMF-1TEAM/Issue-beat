from django.db.models import Count
from datetime import datetime, timedelta
from openai import OpenAI
from ..models import News, DailySummary
from typing import List, Dict
import time

class DailyIssueService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4o-mini"
        self.min_news_count = 20
        self.batch_size = 5

    def get_period_range(self, date: datetime.date, group_by: str) -> tuple:
        """주어진 날짜와 그룹 기준에 따라 시작일과 종료일을 반환"""
        if group_by == '1week':
            start_date = date - timedelta(days=date.weekday())
            end_date = start_date + timedelta(days=6)
        elif group_by == '1month':
            start_date = date.replace(day=1)
            if date.month == 12:
                end_date = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
        else:  # 1day
            start_date = date
            end_date = date

        return start_date, end_date

    def prepare_daily_summaries(self, query: str, news_list, group_by: str = '1day') -> None:
        """차트 데이터 준비 시 호출되는 메서드 - 상위 10일 정도만 미리 처리"""
        news_by_period = {}
        for news in news_list:
            period_start, _ = self.get_period_range(news.date, group_by)
            period_key = period_start.strftime('%Y-%m-%d')
            
            if period_key not in news_by_period:
                news_by_period[period_key] = []
            news_by_period[period_key].append(news)
        
        # 뉴스가 많은 상위 10일만 선택
        important_periods = sorted(
            [
                (period, news_group) 
                for period, news_group in news_by_period.items() 
                if len(news_group) >= self.min_news_count
            ],
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]

        # 배치 처리
        for period_str, period_news_list in important_periods:
            # 이미 요약이 있는지 확인
            period_start = datetime.strptime(period_str, '%Y-%m-%d').date()
            if DailySummary.objects.filter(
                date=period_start,
                query=query,
                group_by=group_by
            ).exists():
                continue

            self._create_summary(period_start, query, period_news_list, group_by)
            time.sleep(0.5)  # API 요청 간 간격 조절

    def _create_summary(self, date: datetime.date, query: str, news_list: List[News], group_by: str) -> DailySummary:
        """요약을 생성하고 저장"""
        # 대표 이미지 선택
        representative_image = next(
            (news.image for news in news_list if news.image),
            None
        )

        # 요약 생성
        summary = self._generate_summary(
            [news.title for news in news_list[:10]],
            [news.content for news in news_list[:10]],
            group_by
        )

        # DB에 저장
        return DailySummary.objects.create(
            date=date,
            query=query,
            group_by=group_by,
            title_summary=summary['title'],
            content_summary=summary['content'],
            news_count=len(news_list),
            representative_image=representative_image
        )

    def get_cached_summary(self, date: datetime.date, query: str, group_by: str, news_list) -> Dict:
        """캐시된 요약 정보 반환 또는 새로운 요약 생성"""
        # 1. 기간 계산
        period_start, period_end = self.get_period_range(date, group_by)

        # 2. 해당 기간의 뉴스 필터링
        period_news = [
            news for news in news_list 
            if period_start <= news.date <= period_end
        ]

        # 3. DailySummary 캐시 확인 - group_by 기준으로 검색
        cached_summary = DailySummary.objects.filter(
            query=query,
            group_by=group_by,
        ).filter(
            date__range=[period_start, period_end]
        ).first()

        if cached_summary and period_news:  # 캐시가 있고 뉴스도 있는 경우
            return {
                'title_summary': cached_summary.title_summary,
                'content_summary': cached_summary.content_summary,
                'news_count': len(period_news)  # 항상 현재 필터링된 뉴스 수 사용
            }

        # 4. 뉴스가 없거나 적은 경우
        if not period_news:
            return {
                'title_summary': '요약 없음',
                'content_summary': '해당 기간의 뉴스가 없습니다.',
                'news_count': 0
            }

        # 5. 새로운 요약 생성 - 전체 기간의 뉴스 사용
        try:
            # 시간순으로 정렬하여 최신 뉴스 우선 사용
            sorted_news = sorted(period_news, key=lambda x: x.date, reverse=True)
            titles = [news.title for news in sorted_news[:10]]  # 상위 10개만 사용
            contents = [news.content for news in sorted_news[:10]]

            summary = self._generate_summary(titles, contents, group_by)

            # 6. 요약 저장 - 기간의 시작일로 저장
            DailySummary.objects.create(
                date=period_start,
                query=query,
                group_by=group_by,
                title_summary=summary['title'],
                content_summary=summary['content'],
                news_count=len(period_news)
            )

            return {
                'title_summary': summary['title'],
                'content_summary': summary['content'],
                'news_count': len(period_news)
            }
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {
                'title_summary': '요약 실패',
                'content_summary': '요약을 생성할 수 없습니다.',
                'news_count': len(period_news)
            }

    def _generate_summary(self, titles: List[str], contents: List[str], group_by: str) -> Dict[str, str]:
        """LLM을 사용해 뉴스 요약 생성"""
        period_type = {
            '1day': '하루',
            '1week': '한 주',
            '1month': '한 달'
        }.get(group_by, '기간')

        try:
            prompt = f"""다음 {period_type} 동안의 뉴스들을 분석해주세요:

제목들:
{' / '.join(titles)}

내용들:
{' / '.join(contents[:3])}  # 내용은 처음 3개만 사용하여 토큰 수 제한

아래 형식으로 요약해주세요:
- 제목 요약 (20자 이내)
- 내용 요약 (50자 이내)"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 뉴스를 간단명료하게 요약하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            summary = response.choices[0].message.content.strip().split('\n')
            return {
                'title': summary[0].replace('- 제목 요약: ', ''),
                'content': summary[1].replace('- 내용 요약: ', '')
            }
        except Exception as e:
            print(f"Error in generate_summary: {e}")
            return {
                'title': '요약 실패',
                'content': '요약을 생성할 수 없습니다.'
            }