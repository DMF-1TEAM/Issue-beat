from django.contrib import admin
from .models import News
from import_export.admin import ImportExportMixin
from .models import SearchHistory


class NewsAdmin(ImportExportMixin, admin.ModelAdmin):
    pass

admin.site.register(News, NewsAdmin)

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'count', 'last_searched']
    list_filter = ['last_searched']
    search_fields = ['keyword']
    ordering = ['-count', '-last_searched']