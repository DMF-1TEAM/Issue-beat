from openai import OpenAI
import json
from typing import List, Dict

class LLMService:
    def __init__(self):
        self.client = OpenAI()

    def generate_structured_summary(self, news_list: List[Dict], is_overall: bool = True) -> Dict:
        """동기식 뉴스 분석 및 JSON 형태로 요약 반환"""
        
        system_prompt = """
당신은 뉴스 분석 전문가입니다. 주어진 뉴스들을 분석하여 JSON 형식으로 구조화된 요약을 제공해주세요.
반드시 다음 형식의 JSON으로 응답해주세요:
{
    "background": "이슈의 배경과 맥락",
    "core_content": "주요 사건과 핵심 내용",
    "conclusion": "현재 상황과 결과"
}
"""

        user_prompt = """
다음 뉴스들을 분석하여 3단계로 요약해주세요:

1. 배경 (background):
- 이 이슈가 발생하게 된 맥락과 배경
- 이전에 있었던 관련 사건이나 상황
- 이 이슈가 중요한 이유

2. 핵심내용 (core_content):
- 현재 일어나고 있는 핵심 사건이나 상황
- 관련된 주요 인물이나 기관의 행동
- 핵심 쟁점이나 갈등

3. 결론 (conclusion):
- 현재까지의 결과나 영향
- 현재 진행 상황
- 앞으로 예상되는 전개 방향

분석할 뉴스:
{news_text}

{"type": "참고", "is_overall": %(is_overall)s}
- is_overall이 true인 경우: 전체적인 이슈의 흐름을 중심으로 요약
- is_overall이 false인 경우: 해당 시점의 상황을 중심으로 요약
"""

        try:
            # 뉴스 텍스트 준비
            news_text = "\n\n".join([
                f"제목: {news['title']}\n내용: {news['content']}"
                for news in news_list
            ])

            # API 요청 (동기식)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt % {'is_overall': str(is_overall).lower()}}
                ],
                response_format={ "type": "json_object" }
            )

            # JSON 파싱
            result = json.loads(response.choices[0].message.content)
            
            # 결과 키 검증
            required_keys = {"background", "core_content", "conclusion"}
            if not all(key in result for key in required_keys):
                raise ValueError("Invalid response format from OpenAI API")

            return result

        except Exception as e:
            print(f"Error in generate_structured_summary: {e}")
            return {
                "background": "요약 생성 중 오류가 발생했습니다.",
                "core_content": "요약 생성 중 오류가 발생했습니다.",
                "conclusion": "요약 생성 중 오류가 발생했습니다."
            }