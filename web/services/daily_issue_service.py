from django.db.models import Count
from datetime import datetime
from openai import OpenAI
from ..models import News, DailySummary
from typing import List, Dict
import time

class DailyIssueService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4o-mini"
        self.min_news_count = 20
        self.batch_size = 5  # 한 번에 처리할 날짜 수
       
    def prepare_daily_summaries(self, query: str, news_list) -> None:
        """
        차트 데이터 준비 시 호출되는 메서드
        뉴스가 min_news_count개 이상인 날짜들에 대해 요약과 대표 이미지를 생성하고 캐시
        """
        # 뉴스 리스트를 날짜별로 그룹화
        news_by_date = {}
        for news in news_list:
            date_str = news.date.strftime('%Y-%m-%d')
            if date_str not in news_by_date:
                news_by_date[date_str] = []
            news_by_date[date_str].append(news)
        
        # min_news_count개 이상인 날짜만 필터링
        dates_to_summarize = {
            date: news_group 
            for date, news_group in news_by_date.items() 
            if len(news_group) >= self.min_news_count
        }

        # 이미 요약이 있는 날짜 제외
        dates_to_summarize = {
            date: news_group
            for date, news_group in dates_to_summarize.items()
            if not DailySummary.objects.filter(
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                query=query
            ).exists()
        }

        # 배치 처리
        dates = list(dates_to_summarize.items())
        for i in range(0, len(dates), self.batch_size):
            batch = dates[i:i + self.batch_size]
            
            for date_str, date_news_list in batch:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()

                # 대표 이미지 선택
                representative_image = next(
                    (news.image for news in date_news_list if news.image),
                    None
                )

                # 요약 생성
                summary = self._generate_summary(
                    [news.title for news in date_news_list[:10]],
                    [news.content for news in date_news_list[:10]]
                )

                # DB에 저장
                DailySummary.objects.create(
                    date=date,
                    query=query,
                    title_summary=summary['title'],
                    content_summary=summary['content'],
                    news_count=len(date_news_list),
                    representative_image=representative_image
                )

            # 배치 사이에 잠시 대기
            if i + self.batch_size < len(dates):
                time.sleep(1)

    def _generate_summary(self, titles: List[str], contents: List[str]) -> Dict[str, str]:
        """LLM을 사용해 뉴스 요약 생성"""
        prompt = f"""다음 뉴스들을 분석해주세요:

제목들:
{' / '.join(titles)}

내용들:
{' / '.join(contents)}

아래 형식으로 요약해주세요:
- 제목 요약 (20자 이내)
- 내용 요약 (50자 이내)"""

        try:
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

    def get_cached_summary(self, date: datetime.date, query: str = None) -> Dict:
        """캐시된 요약 정보 반환"""
        summary = DailySummary.objects.filter(
            date=date,
            query=query
        ).first()
        
        if summary:
            return {
                'date': date.strftime('%Y-%m-%d'),
                'title_summary': summary.title_summary,
                'content_summary': summary.content_summary,
                'news_count': summary.news_count,
                'image_url': summary.representative_image.url if summary.representative_image else None
            }
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'title_summary': '요약 없음',
            'content_summary': '해당 날짜의 요약 정보가 없습니다.',
            'news_count': 0,
            'image_url': None
        }