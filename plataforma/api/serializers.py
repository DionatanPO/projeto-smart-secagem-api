from django.contrib.auth.models import User
from rest_framework import serializers
from plataforma import models
from plataforma.models import SensorData, Alerta, Controlador


class SiloSerializer(serializers.ModelSerializer):
    # Defina o campo user_id como não obrigatório (required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    observacao = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = models.Silo
        fields = '__all__'


class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = '__all__'


class SensorSerializer(serializers.ModelSerializer):
    ultimo_dado_sensor = SensorDataSerializer(many=True, read_only=True)

    class Meta:
        model = models.Sensor
        fields = '__all__'


class ControladorSerializer(serializers.ModelSerializer):
    observacao = serializers.CharField(max_length=255, required=False)

    class Meta:
        model = Controlador
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    silo = SiloSerializer()
    sensor = SensorSerializer()

    class Meta:
        model = Alerta
        fields = '__all__'
