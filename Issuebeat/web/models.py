from django.db import models

class News(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=100)
    press = models.CharField(max_length=20)
    author = models.CharField(max_length=20)
    content = models.TextField()
    keyword = models.TextField()
    image = models.TextField()
    link = models.TextField()