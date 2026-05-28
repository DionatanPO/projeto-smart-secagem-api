import json
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import SensorData, User, Silo, Telemetry, Farm, Lote, Secador, Processo, Cliente
from .serializers import SensorDataSerializer, UserSerializer, MeSerializer, SiloSerializer, TelemetrySerializer, FarmSerializer, LoteSerializer, SecadorSerializer, ProcessoSerializer, ClienteSerializer
from .permissions import IsAdminOrReadOnly, IsAdminOrDeleteOnly, CanManageUsers
from django.db.models import Avg, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from .services.foundation_ai_service import send_chat_request
from .services.context_service import get_ai_context


class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        queryset = SensorData.objects.filter(
            Q(farm__in=farms) | Q(silo__farm__in=farms) | Q(secador__farm__in=farms)
        ).distinct()
        silo = self.request.query_params.get('silo_id') or self.request.query_params.get('silo')
        if silo:
            queryset = queryset.filter(silo_id=silo)
        return queryset

class TelemetryViewSet(viewsets.ModelViewSet):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        queryset = Telemetry.objects.filter(
            Q(sensor__farm__in=farms) |
            Q(sensor__silo__farm__in=farms) |
            Q(sensor__secador__farm__in=farms)
        ).distinct()

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
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        return Silo.objects.filter(farm__in=farms)

class FarmViewSet(viewsets.ModelViewSet):
    serializer_class = FarmSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        return self.request.user.get_accessible_farms()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        return Lote.objects.filter(farm__in=farms)

class SecadorViewSet(viewsets.ModelViewSet):
    serializer_class = SecadorSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        return Secador.objects.filter(farm__in=farms)

class ProcessoViewSet(viewsets.ModelViewSet):
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        return Processo.objects.filter(lote__farm__in=farms)

    def perform_create(self, serializer):
        # Atribui o usuário logado como responsável pelo processo automaticamente
        serializer.save(responsavel=self.request.user)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, CanManageUsers]

    def get_queryset(self):
        user = self.request.user
        if user.account_type == 'super_admin':
            return User.objects.all()
        if user.account_type == 'admin':
            my_farms = user.farms.all()
            return User.objects.filter(
                farm__in=my_farms, account_type__in=['operador', 'visualizador']
            ) | User.objects.filter(id=user.id)
        return User.objects.none()

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        farms = self.request.user.get_accessible_farms()
        return Cliente.objects.filter(farm__in=farms)

    def perform_create(self, serializer):
        farms = self.request.user.get_accessible_farms()
        farm_id = self.request.data.get('farm')
        if not farm_id:
            # Se não enviou, pega a primeira fazenda disponível do usuário
            farm = farms.first()
        else:
            farm = farms.filter(id=farm_id).first()
        if not farm:
            raise PermissionError("Você não tem permissão para vincular clientes a esta fazenda.")
        serializer.save(farm=farm)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me_view(request):
    if request.method == 'GET':
        serializer = MeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = MeSerializer(request.user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


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
    """
    prompt = request.data.get('prompt')
    if not prompt:
        return Response({"error": "O campo 'prompt' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

    # Campos opcionais
    image_base64  = request.data.get('image_base64', None)
    history       = request.data.get('history', None)
    use_rag       = request.data.get('use_rag', False)
    temperature   = request.data.get('temperature', 0.1)
    system_prompt = request.data.get('system_prompt', None)

    # Coleta de contexto otimizada
    context_json = get_ai_context(request.user)

    enhanced_prompt = (
        f"{prompt}\n\n"
        f"--- CONTEXTO DO SISTEMA (Dados em tempo real) ---\n"
        f"Use estas informações para fundamentar sua resposta:\n\n"
        f"{context_json}"
    )

    # Se o cliente não enviar um system_prompt, enviamos None para a IA
    final_system_prompt = system_prompt

    resultado = send_chat_request(
        prompt=enhanced_prompt,
        image_base64=image_base64,
        history=history,
        use_rag=use_rag,
        temperature=temperature,
        system_prompt=final_system_prompt,
    )

    if resultado['success']:
        return Response({"response": resultado['response']}, status=status.HTTP_200_OK)

    error_status = resultado.get('status_code', 500)
    return Response({"error": resultado['error']}, status=error_status)
