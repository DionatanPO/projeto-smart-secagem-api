from rest_framework import serializers
from .models import SensorData, User, Silo, Telemetry, Farm, Lote, Secador, Processo, Cliente

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

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = '__all__'
        read_only_fields = ['owner']

class SiloSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    
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

class LoteSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)
    silo_name = serializers.CharField(source='silo.name', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)

    class Meta:
        model = Lote
        fields = '__all__'

    def validate(self, data):
        # Para casos de PATCH, precisamos pegar os valores atuais se não forem enviados
        silo = data.get('silo', self.instance.silo if self.instance else None)
        peso_inicial = data.get('peso_inicial', self.instance.peso_inicial if self.instance else 0)
        status = data.get('status', self.instance.status if self.instance else 'aguardando')

        if silo:
            # 1. Validação de Capacidade (1 Ton = 1000 kg)
            capacidade_kg = silo.capacity * 1000
            if peso_inicial > capacidade_kg:
                raise serializers.ValidationError({
                    "peso_inicial": f"O peso do lote ({peso_inicial}kg) excede a capacidade do silo ({capacidade_kg}kg)."
                })

            # 2. Validação de Ocupação
            # Verifica se já existe um lote ativo (aguardando ou secando) neste silo
            lote_ativo_query = Lote.objects.filter(
                silo=silo, 
                status__in=['aguardando', 'secando']
            )
            
            # Se estivermos editando, excluímos o próprio lote da busca
            if self.instance:
                lote_ativo_query = lote_ativo_query.exclude(id=self.instance.id)
            
            if lote_ativo_query.exists() and status in ['aguardando', 'secando']:
                raise serializers.ValidationError({
                    "silo": "Este silo já possui um lote em processamento ativo."
                })

        return data

class SecadorSerializer(serializers.ModelSerializer):
    farm_name = serializers.CharField(source='farm.name', read_only=True)

    class Meta:
        model = Secador
        fields = '__all__'

class ProcessoSerializer(serializers.ModelSerializer):
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    lote_cultura = serializers.CharField(source='lote.cultura', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.username', read_only=True)
    secador_nome = serializers.CharField(source='secador.nome', read_only=True, default=None)
    silo_nome = serializers.CharField(source='silo.name', read_only=True, default=None)

    class Meta:
        model = Processo
        fields = '__all__'


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
