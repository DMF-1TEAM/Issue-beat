from typing import List, Dict
from openai import OpenAI
import json

class LLMService:
    def __init__(self):
        self.client = OpenAI()
        
    def generate_structured_summary(self, news_list: List[Dict], search_keyword: str, is_overall: bool = True) -> Dict:
        try:
            # 뉴스 데이터 제한
            news_data = []
            total_length = 0
            max_content_length = 500  # 각 뉴스 내용 최대 길이
            max_total_length = 60000  # 전체 텍스트 최대 길이

            for news in news_list:
                content = news['content'][:max_content_length]
                news_text = f"제목: {news['title']}\n내용: {content}"
                if total_length + len(news_text) > max_total_length:
                    break
                news_data.append(news_text)
                total_length += len(news_text)

            # 뉴스 텍스트 준비
            news_text = "\n\n".join(news_data)

            system_prompt = f"""
    당신은 뉴스 분석 전문가입니다.
    현재 '{search_keyword}'와 관련된 뉴스들을 분석하게 됩니다.
    이 키워드를 중심으로 관련 뉴스들의 맥락을 파악하고 구조화된 요약을 제공해주세요.
    반드시 JSON 형식으로 응답해주세요.
    """

            user_prompt = f"""
    '{search_keyword}' 키워드로 검색된 다음 뉴스들을 분석하여 JSON 형식으로 3단계 요약을 생성해주세요.
    요약은 전체 흐름을 간결히 전달할 수 있도록 해주시고 아래 형식으로 응답해주세요.
    각 형식에는 50~80자 내외로 작성해주세요.

    {{
        "background": "배경 설명",
        "core_content": "핵심 내용",
        "conclusion": "결론"
    }}

    분석할 뉴스:
    {news_text}
    """
            # API 호출
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"Error in generate_structured_summary: {e}")
            return {
                "background": "요약 생성 중 오류가 발생했습니다.",
                "core_content": "요약 생성 중 오류가 발생했습니다.",
                "conclusion": "요약 생성 중 오류가 발생했습니다."
            }

    def generate_quick_summary(self, news_list: List[Dict], search_keyword: str) -> Dict:
        """뉴스 데이터를 받아 한 문장으로 된 요약을 생성합니다."""
        try:
            news_text = "\n\n".join([
                f"날짜: {news['date']}\n"
                f"제목: {news['title']}\n"
                f"내용: {news['content']}"
                for news in news_list
            ])

            system_prompt = f"""
당신은 뉴스 분석 전문가입니다.
'{search_keyword}' 관련 뉴스들을 분석하여 이 이슈의 본질을 한 문장으로 설명해주세요.

다음 사항을 고려해주세요:
1. 시간의 흐름에 따른 이슈의 전개와 맥락을 파악해주세요
2. 일시적인 현상이 아닌, 이슈의 근본적인 배경과 의미를 담아주세요
3. 설명은 30자 내외로 간단명료하게 작성해주세요
"""

            user_prompt = f"""
다음은 '{search_keyword}' 관련 주요 시점의 뉴스들입니다:

{news_text}

요구사항:
1. 30자 내외로 작성
2. 이슈의 본질과 맥락을 포함
3. JSON 형식으로 응답: {{"summary": "요약문"}}
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"Error in generate_quick_summary: {e}")
            return {
                "summary": "요약 생성 중 오류가 발생했습니다."
            }