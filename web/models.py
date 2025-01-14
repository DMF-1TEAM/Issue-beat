from django.db import models
from datetime import datetime

class News(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=100)
    press = models.CharField(max_length=20)
    author = models.CharField(max_length=20)
    content = models.TextField()
    keyword = models.CharField(max_length=1000000)
    image = models.TextField()
    link = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['date']),
        ]
        
    @classmethod
    def get_search_index(cls):
        """검색을 위한 인덱스 생성"""
        return {
            'mappings': {
                'properties': {
                    'title': {'type': 'text', 'analyzer': 'korean'},
                    'content': {'type': 'text', 'analyzer': 'korean'},
                    'keyword': {'type': 'keyword'},
                    'date': {'type': 'date'},
                    'press': {'type': 'keyword'}
                }
            }
        }

    def __str__(self):
        return f"[{self.press}] {self.title}"
    
class Keyword(models.Model):
    name = models.CharField(max_length=100)
    news = models.ManyToManyField(News, related_name='keywords')
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.keyword} ({self.count})"

class SearchHistory(models.Model):
    keyword = models.CharField(max_length=100)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-count']

    def __str__(self):
        return f"{self.keyword} ({self.count})"
    
class NewsSummary(models.Model):
    """3단 요약을 위한 모델"""
    keyword = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    group_by = models.CharField(
        max_length=10, 
        default='1day',
        choices=[
            ('1day', '일간'),
            ('1week', '주간'),
            ('1month', '월간')
        ]
    )
    background = models.TextField()
    core_content = models.TextField()
    conclusion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['keyword', 'date', 'group_by']
        # indexes = [
        #     models.Index(fields=['keyword', 'date', 'group_by']),
        # ]
    
    def __str__(self):
        period = self.date or 'overall'
        return f"{self.keyword} - {period} ({self.group_by})"
    
class DailySummary(models.Model):
    """차트 호버 요약을 위한 모델"""
    date = models.DateField()
    query = models.CharField(max_length=200, null=True, blank=True)
    group_by = models.CharField(
        max_length=10, 
        default='1day',
        choices=[
            ('1day', '일간'),
            ('1week', '주간'),
            ('1month', '월간')
        ]
    )
    title_summary = models.CharField(max_length=100)
    content_summary = models.TextField()
    news_count = models.IntegerField()
    representative_image = models.ImageField(upload_to='daily_summaries/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['date', 'query', 'group_by']),
        ]

    def __str__(self):
        query_str = self.query if self.query else 'All'
        return f"{self.date} - {query_str} ({self.group_by})"
    
class QuickSummary(models.Model):
    """검색 키워드에 대한 간단 요약 모델"""
    keyword = models.CharField(max_length=200, unique=True)
    summary = models.CharField(max_length=100)
    news_count = models.IntegerField(default=0)  # 요약 생성에 사용된 뉴스 수
    date_range = models.CharField(max_length=50)  # 뉴스 기간 (예: "2022-01-01~2024-03-01")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.keyword}: {self.summary}"
    
