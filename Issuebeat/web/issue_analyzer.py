import os
import numpy as np
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from itertools import groupby
import logging

logger = logging.getLogger(__name__)

class NewsStoryAnalyzer:
    def __init__(self, api_key: str = None):
        """Initialize NewsStoryAnalyzer"""
        self.client = OpenAI(api_key=api_key)
        self.vectorizer = TfidfVectorizer(
            max_features=200,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        
    def preprocess_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """키워드 중심의 전처리 로직"""
        if not articles:
            return []
            
        try:
            # 1. 시간순 정렬
            sorted_articles = sorted(articles, key=lambda x: x.get('date', ''))
            
            # 2. 날짜별 그룹화 및 키워드 기반 중복 제거
            grouped_articles = []
            for date, group in groupby(sorted_articles, key=lambda x: x.get('date', '')[:10]):
                group_list = list(group)
                
                if len(group_list) > 3:
                    # 키워드 유사도 기반으로 대표 기사 선택
                    keyword_texts = [' '.join(article.get('keyword', [])) for article in group_list]
                    if any(keyword_texts):
                        embeddings = self.get_embeddings(keyword_texts)
                        if embeddings.size > 0:
                            centrality_scores = np.mean(cosine_similarity(embeddings), axis=1)
                            top_indices = np.argsort(centrality_scores)[-3:]
                            group_list = [group_list[i] for i in top_indices]
                
                grouped_articles.extend(group_list)
            
            # 3. 전체 기사 수가 너무 많은 경우 처리
            if len(grouped_articles) > 300:
                keyword_texts = [' '.join(article.get('keyword', [])) for article in grouped_articles]
                embeddings = self.get_embeddings(keyword_texts)
                centrality_scores = np.mean(cosine_similarity(embeddings), axis=1)
                top_indices = np.argsort(centrality_scores)[-300:]
                grouped_articles = [grouped_articles[i] for i in sorted(top_indices)]
            
            return grouped_articles
            
        except Exception as e:
            logger.error(f"Error in preprocessing: {str(e)}")
            return articles[:100]

    def create_keyword_summary(self, articles: List[Dict[str, Any]]) -> str:
        """키워드 기반의 요약 텍스트 생성"""
        summary = []
        for article in articles:
            date = article.get('date', '')[:10]
            title = article.get('title', '')
            keywords = article.get('keyword', [])
            
            if keywords:
                summary.append(f"[{date}] {title}\n키워드: {', '.join(keywords)}")
        
        return '\n\n'.join(summary)

    def analyze_story(self, articles: List[Dict[str, Any]], keyword: str) -> Dict[str, Any]:
        """전체 분석 프로세스"""
        try:
            logger.info(f"Starting analysis for keyword '{keyword}' with {len(articles)} articles")
            
            # 날짜 범위 계산
            dates = [article.get('date', '') for article in articles if article.get('date')]
            if not dates:
                return None
                
            start_date = min(dates)
            end_date = max(dates)
            
            # 전처리
            processed_articles = self.preprocess_articles(articles)
            if not processed_articles:
                return None
                
            # 키워드 요약 생성
            summary = self.create_keyword_summary(processed_articles)
            
            # GPT 분석 수행
            prompt = f"""다음은 '{keyword}' 관련 뉴스 기사들의 제목과 핵심 키워드입니다. 
            전체 내용을 종합적으로 분석하여 각각 100자 내로 요약해주세요:

            1. 배경: 이슈의 발생 원인과 맥락
            2. 핵심: 주요 사건 전개와 쟁점
            3. 결론: 현재 상황과 전망

            기사 정보:
            {summary}

            형식:
            배경: (설명)
            핵심내용: (설명)
            결론: (설명)"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "뉴스 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # 응답 파싱
            result = self._parse_response(response.choices[0].message.content)
            
            # 분석 결과 저장
            analysis = {
                'keyword': keyword,
                'background': result['background'],
                'core_content': result['core_content'],
                'conclusion': result['conclusion'],
                'article_count': len(articles),
                'processed_article_count': len(processed_articles),
                'processed_at': datetime.now(),
                'date_range_start': datetime.strptime(start_date[:10], '%Y-%m-%d').date(),
                'date_range_end': datetime.strptime(end_date[:10], '%Y-%m-%d').date()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_story: {str(e)}")
            return None

    def _parse_response(self, content: str) -> Dict[str, str]:
        """Parse GPT response into structured format"""
        result = {
            'background': '',
            'core_content': '',
            'conclusion': ''
        }
        
        for line in content.split('\n'):
            if line.startswith('배경:'):
                result['background'] = line[3:].strip()
            elif line.startswith('핵심내용:'):
                result['core_content'] = line[5:].strip()
            elif line.startswith('결론:'):
                result['conclusion'] = line[3:].strip()
                
        return result

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """TF-IDF를 사용한 텍스트 임베딩 생성"""
        if not texts:
            return np.array([])
        
        try:
            if all(not text.strip() for text in texts):
                return np.zeros((len(texts), 1))
            if len(texts) == 1:
                return np.ones((1, 1))
            return self.vectorizer.fit_transform(texts).toarray()
        except Exception as e:
            logger.error(f"Error in get_embeddings: {str(e)}")
            return np.ones((len(texts), 1))