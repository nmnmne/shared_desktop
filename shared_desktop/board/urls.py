"""board URL configuration."""
from django.urls import path

from . import views
from .views import RuleListAPIView


app_name = "rules"

urlpatterns = [
    path("", views.index, name="rules"),
    path("full/", views.full, name="full"),
    path("rules/", views.rules_list, name="rule"),
    path("rules/<pk>/", views.rules_detail),
    path('api/rules/', RuleListAPIView.as_view(), name='rule-list'),
]
