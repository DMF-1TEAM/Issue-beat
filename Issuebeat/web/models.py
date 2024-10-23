from django.db import models

class News(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=50)
    content = models.TextField()
    image = models.URLField()
    link = models.URLField()
    press = models.CharField(max_length=20)
    author = models.CharField(max_length=10)