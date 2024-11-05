# services/daily_issue_analyzer.py
from typing import List, Dict, Any
from openai import OpenAI
from datetime import datetime
from ..models import News

class DailyIssueService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-4o-mini"

    def generate_keyword_summary(self, keywords: str) -> Dict[str, str]:
        """간단한 제목과 본문 요약 생성"""
        try:
            # 키워드 전처리
            keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
            
            prompt = f"""
다음 키워드들을 보고 두 줄로 요약해주세요:
{', '.join(keyword_list)}

첫 줄: 핵심 주제 (10자 이내)
둘째 줄: 현재 상황 (30자 이내)
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 뉴스 키워드를 간단히 요약하는 전문가입니다."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )

            # 응답 처리
            lines = response.choices[0].message.content.strip().split('\n')
            title_summary = lines[0].strip() if len(lines) > 0 else "요약 없음"
            content_summary = lines[1].strip() if len(lines) > 1 else "내용 없음"

            return {
                'title_summary': title_summary,
                'content_summary': content_summary
            }

        except Exception as e:
            print(f"Keyword summary generation error: {e}")
            return {
                'title_summary': "요약 실패",
                'content_summary': "요약 실패"
            }

    def get_daily_summary_data(self, date: datetime.date) -> Dict[str, Any]:
        """특정 날짜의 뉴스 데이터 간단 요약"""
        try:
            news_list = News.objects.filter(date=date)
            news_with_image = news_list.exclude(image='').order_by('?').first()
            
            # 키워드 수집
            keywords = set()
            for news in news_list:
                if news.keyword:
                    keywords.update(k.strip() for k in news.keyword.split(',') if k.strip())
            
            # 요약 생성
            if keywords:
                summaries = self.generate_keyword_summary(','.join(keywords))
            else:
                summaries = {
                    'title_summary': "키워드 없음",
                    'content_summary': "내용 없음"
                }
            
            return {
                'date': date,
                'image_url': news_with_image.image if news_with_image else None,
                'title_summary': summaries['title_summary'],
                'content_summary': summaries['content_summary'],
                'news_count': news_list.count()
            }

        except Exception as e:
            print(f"Error in get_daily_summary_data: {e}")
            return {
                'date': date,
                'image_url': None,
                'title_summary': "데이터 처리 실패",
                'content_summary': "데이터 처리 실패",
                'news_count': 0
            }