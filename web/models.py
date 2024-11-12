from django.db import models
from datetime import datetime

class News(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=100)
    press = models.CharField(max_length=20)
    author = models.CharField(max_length=20)
    content = models.TextField()
    keyword = models.TextField()
    image = models.TextField()
    link = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['date', 'press']),
            models.Index(fields=['date', '-press']),
            models.Index(fields=['keyword']),
            models.Index(fields=['date', 'keyword']),
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

class SearchHistory(models.Model):
    keyword = models.CharField(max_length=100)
    count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-count']

    def __str__(self):
        return f"{self.keyword} ({self.count})"
    
class NewsSummary(models.Model):
    keyword = models.CharField(max_length=200)
    date = models.DateField(null=True, blank=True)
    background = models.TextField()
    core_content = models.TextField()
    conclusion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['keyword', 'date']
        indexes = [
            models.Index(fields=['keyword', 'date']),
        ]
    
    def __str__(self):
        return f"{self.keyword} - {self.date or 'overall'}"
    
class DailySummary(models.Model):
    date = models.DateField()
    query = models.CharField(max_length=200, null=True, blank=True)
    title_summary = models.CharField(max_length=100)
    content_summary = models.TextField()
    news_count = models.IntegerField()
    representative_image = models.ImageField(upload_to='daily_summaries/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['query']),
        ]

    def __str__(self):
        return f"{self.date} - {self.query if self.query else 'All'}"
