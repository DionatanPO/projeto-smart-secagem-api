from urllib import request

from django.db.models import Max, Prefetch
from rest_framework import viewsets, status
from rest_framework.response import Response

from plataforma.api import serializers
from plataforma import models
from plataforma.api.serializers import AlertaSerializer
from plataforma.models import SensorData, Alerta, AeracaoSilo, Sensor


class SilosViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SiloSerializer

    def get_queryset(self):
        # Obtém o usuário atualmente autenticado
        user = self.request.user
        # Filtra os silos com base no usuário
        queryset = models.Silo.objects.filter(user=user)

        return queryset

    def perform_create(self, serializer):
        # Obtém o usuário atualmente autenticado
        user = self.request.user

        # Adiciona o user_id ao criar o novo silo
        serializer.save(user=user)

        # Retorna a resposta de sucesso
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        # Obtém o usuário atualmente autenticado
        user = request.user

        # Obtém o objeto silo a ser atualizado
        instance = self.get_object()

        # Verifica se o usuário tem permissão para atualizar este objeto
        if instance.user != user:
            return Response({"error": "Você não tem permissão para atualizar este silo."},
                            status=status.HTTP_403_FORBIDDEN)

        # Atualiza o objeto silo
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def perform_update(self, serializer):
        # Atualiza o objeto silo
        serializer.save()

        # Retorna a resposta de sucesso
        return Response(serializer.data, status=status.HTTP_200_OK)


class SensoresViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SensorSerializer

    def get_queryset(self):
        # Obtém o ID do silo da solicitação
        silo_id = self.request.query_params.get('silo_id')
        # Query para obter os sensores e o último SensorData de cada sensor
        queryset = models.Sensor.objects.filter(silo_id=silo_id).prefetch_related(
            Prefetch('sensordata_set', queryset=models.SensorData.objects.order_by('-time')[:1],
                     to_attr='ultimo_dado_sensor')
        )

        return queryset

    def update(self, request, *args, **kwargs):
        sensor_id = kwargs.get('pk')  # ID do sensor a ser atualizado
        try:
            sensor = models.Sensor.objects.get(pk=sensor_id)
        except models.Sensor.DoesNotExist:
            return Response({'error': 'Sensor não encontrado'}, status=404)

        serializer = self.get_serializer(sensor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class ControladoresViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ControladorSerializer

    def get_queryset(self):
        queryset = models.Controlador.objects.all()
        silo_id = self.request.query_params.get('silo_id')  # Obtém o silo_id da query string da URL

        if silo_id:
            queryset = queryset.filter(silo_id=silo_id)

        return queryset


class SensorDataViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SensorDataSerializer

    def get_queryset(self):
        queryset = SensorData.objects.all()
        sensor_id = self.request.query_params.get('sensor_id')
        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)

        # Ordenar os dados pela coluna 'time' do mais recente para o mais antigo
        queryset = queryset.order_by('-time')

        return queryset


class AlertaViewSet(viewsets.ModelViewSet):
    serializer_class = AlertaSerializer

    def get_queryset(self):
        # Obtém o usuário da solicitação atual
        user = self.request.user

        # Filtra os silos do usuário
        silos = models.Silo.objects.filter(user=user)

        # Obtém os IDs dos silos filtrados
        silo_ids = silos.values_list('id_silo', flat=True)

        # Filtra os alertas com base nos IDs dos silos e trazendo informações do silo e do sensor
        queryset = Alerta.objects.filter(silo_id__in=silo_ids).select_related('silo', 'sensor').order_by('-time')

        return queryset

