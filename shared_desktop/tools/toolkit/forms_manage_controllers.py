from django import forms

from .models import ControllerManagement


class ControllerManagementData(forms.Form):
    configuration_from_db = forms.ModelChoiceField(queryset=ControllerManagement.objects.all(), label='Выбор конфигурации')