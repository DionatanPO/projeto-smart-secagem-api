from rest_framework import serializers
from .models import SensorData, User, Silo, Telemetry

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = '__all__'

class TelemetrySerializer(serializers.ModelSerializer):
    # Permite enviar o sensor_id (String) em vez do ID numérico na criação
    sensor_physical_id = serializers.CharField(source='sensor.sensor_id', read_only=True)
    
    class Meta:
        model = Telemetry
        fields = ['id', 'sensor', 'sensor_physical_id', 'temperatura', 'umidade', 'timestamp', 'received_at']

class SiloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Silo
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'account_type', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)
