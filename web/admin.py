from django.contrib import admin
from .models import News
from import_export.admin import ImportExportMixin


class NewsAdmin(ImportExportMixin, admin.ModelAdmin):
    pass

admin.site.register(News, NewsAdmin)