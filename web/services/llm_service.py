from typing import List, Dict
from openai import OpenAI
import json

class LLMService:
    def __init__(self):
        self.client = OpenAI()
        
    def generate_structured_summary(self, news_list: List[Dict], search_keyword: str, is_overall: bool = True) -> Dict:
        try:
            # 뉴스 텍스트 준비
            news_text = "\n\n".join([
                f"제목: {news['title']}\n내용: {news['content']}"
                for news in news_list
            ])

            system_prompt = f"""
당신은 뉴스 분석 전문가입니다.
현재 '{search_keyword}'와 관련된 뉴스들을 분석하게 됩니다.
이 키워드를 중심으로 관련 뉴스들의 맥락을 파악하고 구조화된 요약을 제공해주세요.
반드시 JSON 형식으로 응답해주세요.
"""

            user_prompt = f"""
'{search_keyword}' 키워드로 검색된 다음 뉴스들을 분석하여 JSON 형식으로 3단계 요약을 생성해주세요.
<<<<<<< HEAD
다음 형식으로 응답해주세요:
=======
요약은 전체 흐름을 간결히 전달할 수 있도록 해주시고 아래 형식으로 응답해주세요.
각 형식에는 50~80자 내외로 작성해주세요.
>>>>>>> master

{{
    "background": "배경 설명",
    "core_content": "핵심 내용",
    "conclusion": "결론"
}}

각 섹션에서 다뤄야 할 내용:

1. 배경 (background):
<<<<<<< HEAD
- '{search_keyword}' 관련 이슈가 발생하게 된 배경과 원인
- 관련된 사회적/정책적 맥락
- 이 문제가 중요하게 다뤄지는 이유

2. 핵심내용 (core_content):
- 현재 진행 중인 핵심 사건과 상황
- 주요 이해관계자들의 입장과 행동
- '{search_keyword}' 관련 주요 쟁점들

3. 결론 (conclusion):
- 현재까지의 구체적인 진행 상황
- 이 이슈가 미치는 영향
- 향후 예상되는 전개 방향
=======
- '{search_keyword}' 이슈 발생 배경, 원인, 관련된 사회적/정책적 맥락을 간결히 설명해 주세요.

2. 핵심내용 (core_content):
- '{search_keyword}' 관련 주요 쟁점들과 현재 진행중인 상황, 주요 이해관계자 입장 등을 설명해 주세요.

3. 결론 (conclusion):
- 현재까지의 진행 상황과 향후 예상되는 전개 방향 이나 마무리된 상황이면 사건의 결론을 요약해 주세요.
- 
>>>>>>> master

분석할 뉴스:
{news_text}

{{"type": "참고", "keyword": "{search_keyword}", "is_overall": {str(is_overall).lower()}}}
- is_overall이 true인 경우: 이슈의 전체적인 흐름과 맥락을 중심으로 요약
- is_overall이 false인 경우: 최근 상황과 변화를 중심으로 요약

반드시 JSON 형식으로 응답해주세요.
"""

            # API 요청
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )

            # JSON 파싱
            result = json.loads(response.choices[0].message.content)
            
            return result

        except Exception as e:
            print(f"Error in generate_structured_summary: {e}")
            return {
                "background": "요약 생성 중 오류가 발생했습니다.",
                "core_content": "요약 생성 중 오류가 발생했습니다.",
                "conclusion": "요약 생성 중 오류가 발생했습니다."
            }