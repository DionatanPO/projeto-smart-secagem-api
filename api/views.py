from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import SensorData, User, Silo, Telemetry, Farm, Lote, Secador, Processo, Cliente
from .serializers import SensorDataSerializer, UserSerializer, SiloSerializer, TelemetrySerializer, FarmSerializer, LoteSerializer, SecadorSerializer, ProcessoSerializer, ClienteSerializer
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
from .services.foundation_ai_service import send_chat_request


class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

    def get_queryset(self):
        queryset = SensorData.objects.all()
        silo = self.request.query_params.get('silo_id') or self.request.query_params.get('silo')
        if silo:
            queryset = queryset.filter(silo_id=silo)
        return queryset

class TelemetryViewSet(viewsets.ModelViewSet):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer

    def get_queryset(self):
        queryset = Telemetry.objects.all()

        # Filtrar pelo PK do sensor (id numérico do banco)
        sensor_pk = self.request.query_params.get('sensor')
        if sensor_pk:
            queryset = queryset.filter(sensor_id=sensor_pk)

        # Filtrar por Silo (todos os sensores de um silo)
        silo_id = self.request.query_params.get('silo') or self.request.query_params.get('silo_id')
        if silo_id:
            queryset = queryset.filter(sensor__silo_id=silo_id)

        # Filtrar pelo ID físico do sensor (ex: "sensor_01")
        sensor_physical_id = self.request.query_params.get('sensor_id')
        if sensor_physical_id:
            queryset = queryset.filter(sensor__sensor_id=sensor_physical_id)

        # Filtrar por data (YYYY-MM-DD)
        date_str = self.request.query_params.get('data')
        if date_str:
            queryset = queryset.filter(timestamp__date=date_str)

        return queryset

    def create(self, request, *args, **kwargs):
        # Lógica especial para aceitar o physical_id do sensor vindo do Gateway
        data = request.data
        physical_id = data.get('sensor_id')
        
        if physical_id:
            try:
                sensor = SensorData.objects.get(sensor_id=physical_id)
                data['sensor'] = sensor.id
            except SensorData.DoesNotExist:
                return Response(
                    {"error": f"Sensor com ID físico {physical_id} não encontrado na configuração."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SiloViewSet(viewsets.ModelViewSet):
    queryset = Silo.objects.all()
    serializer_class = SiloSerializer

class FarmViewSet(viewsets.ModelViewSet):
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Cada usuário só vê as suas próprias fazendas
        return Farm.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Atribui o usuário logado como dono da fazenda automaticamente
        serializer.save(owner=self.request.user)

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtra os lotes das fazendas que pertencem ao usuário logado
        return Lote.objects.filter(farm__owner=self.request.user)

class SecadorViewSet(viewsets.ModelViewSet):
    serializer_class = SecadorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtra os secadores das fazendas que pertencem ao usuário logado
        return Secador.objects.filter(farm__owner=self.request.user)

class ProcessoViewSet(viewsets.ModelViewSet):
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtra os processos vinculados às fazendas do usuário logado
        return Processo.objects.filter(lote__farm__owner=self.request.user)

    def perform_create(self, serializer):
        # Atribui o usuário logado como responsável pelo processo automaticamente
        serializer.save(responsavel=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Apenas administradores podem gerenciar usuários por padrão
    permission_classes = [IsAdminUser]
    
class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Deleta o token do usuário logado
    request.user.auth_token.delete()
    return Response({"message": "Logout realizado com sucesso"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_view(request):
    """
    Recebe uma mensagem do Flutter e encaminha para a Foundation AI local.

    Campos de entrada (JSON):
      - prompt (str, obrigatório)
      - image_base64 (str, opcional)
      - history (list, opcional)
      - use_rag (bool, opcional, padrão True)
      - temperature (float, opcional, padrão 0.2)
      - system_prompt (str, opcional)

    Retorno:
      - 200: { "response": "texto da IA" }
      - 400: { "error": "mensagem" }  (validação)
      - 503/504/500: { "error": "mensagem" }  (falha na IA)
    """
    prompt = request.data.get('prompt')

    # Validação do campo obrigatório
    if not prompt:
        return Response(
            {"error": "O campo 'prompt' é obrigatório."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Campos opcionais com valores padrão
    image_base64  = request.data.get('image_base64', None)
    history       = request.data.get('history', None)
    use_rag       = request.data.get('use_rag', True)
    temperature   = request.data.get('temperature', 0.2)
    system_prompt = request.data.get('system_prompt', None)

    # Validação de tipos simples
    if not isinstance(use_rag, bool):
        return Response(
            {"error": "O campo 'use_rag' deve ser um booleano (true/false)."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not isinstance(temperature, (int, float)) or not (0.0 <= temperature <= 1.0):
        return Response(
            {"error": "O campo 'temperature' deve ser um número entre 0.0 e 1.0."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if history is not None and not isinstance(history, list):
        return Response(
            {"error": "O campo 'history' deve ser uma lista de objetos."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Encaminha para o serviço da Foundation AI
    resultado = send_chat_request(
        prompt=prompt,
        image_base64=image_base64,
        history=history,
        use_rag=use_rag,
        temperature=temperature,
        system_prompt=system_prompt,
    )

    if resultado['success']:
        return Response({"response": resultado['response']}, status=status.HTTP_200_OK)

    # Repassa o erro com o status code original da IA
    error_status = resultado.get('status_code', 500)
    return Response({"error": resultado['error']}, status=error_status)
