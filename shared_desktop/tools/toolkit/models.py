from django.db import models
from django.utils import timezone


class ControllerManagement(models.Model):
    name = models.CharField(max_length=30, blank=False, null=False, unique=True)
    # num_visible_hosts = models.CharField(max_length=2, blank=False, null=False, default='1')
    num_visible_hosts = models.IntegerField(default=1, blank=True)
    data = models.TextField(unique=True)
    # data = models.JSONField(unique=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    category = models.IntegerField()
    user_name = models.CharField(max_length=20, default='0')

    def __str__(self):
        return self.name


class TrafficLightsObjects(models.Model):
    number = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True)
    type_controller = models.CharField(max_length=20)
    group = models.IntegerField(default=0)
    ip_adress = models.CharField(max_length=20, null=True)
    adress = models.TextField(blank=True, null=True)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.number} {self.adress} {self.type_controller}'


class TelegrammUsers(models.Model):
    chat_id = models.CharField(max_length=10, unique=True)
    username = models.CharField(max_length=40, null=True)
    first_name = models.CharField(max_length=40, null=True)
    last_name = models.CharField(max_length=40, null=True)
    access_level = models.IntegerField(default=0)
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.chat_id} {self.username} {self.first_name} {self.username} {self.access_level}'


class TrafficLightConfigurator(models.Model):
    function = models.CharField(max_length=255, verbose_name='Тип запроса')
    condition_string = models.TextField(verbose_name='Условие из tlc')
    function_values = models.TextField(max_length=255, verbose_name='Значения функций', default='')
    condition_string_for_parse = models.TextField(verbose_name='Условие с заданными значениями функций', default='')
    tokens = models.TextField(max_length=255, verbose_name='Функции(токены) из условия tlc', default='')
    result_condition_value = models.BooleanField(
        verbose_name='Результат выражения условия из tlc для заданных функций', default='', null=True
    )
    errors = models.CharField(max_length=255, verbose_name='Ошибки')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')


class SaveConfigFiles(models.Model):
    source = models.CharField(max_length=20)
    file = models.FileField(upload_to='conflicts/configs/', null=True, verbose_name='config_file')
    time_create = models.DateTimeField(default=timezone.now)
    controller_type = models.CharField(max_length=20, db_index=True, default='undefined')
    description = models.TextField(null=True)
    number = models.CharField(max_length=100, null=True)
    ip_adress = models.CharField(max_length=20, null=True)
    address = models.TextField(blank=True, null=True)

    def __repr__(self):
        return self.file.name