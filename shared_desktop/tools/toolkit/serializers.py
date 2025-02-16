from rest_framework import serializers

from tools.toolkit.models import ControllerManagement, TrafficLightsObjects


class ControllerHostsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControllerManagement
        fields = '__all__'


class TrafficLightsSerializerAllFields(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightsObjects
        fields = '__all__'


class BaseTrafficLightsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficLightsObjects
        fields = ('number', 'description', 'type_controller', 'ip_adress', 'adress')
