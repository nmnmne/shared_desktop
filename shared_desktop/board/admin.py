from django.contrib import admin

from .models import Rule


class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "pub_date", "author")
    search_fields = ("name",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


admin.site.register(Rule, RuleAdmin)
