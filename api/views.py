import json
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import SensorData, User, Silo, Telemetry, UnidadeArmazenadora, Lote, Secador, Processo, Cliente
from .serializers import SensorDataSerializer, UserSerializer, MeSerializer, SiloSerializer, TelemetrySerializer, UnidadeArmazenadoraSerializer, LoteSerializer, SecadorSerializer, ProcessoSerializer, ClienteSerializer
from .permissions import IsAdminOrReadOnly, IsAdminOrDeleteOnly, CanManageUsers
from django.db.models import Avg, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from .services.context_service import get_ai_context
from .services.custos_service import calcular_custos_processo


class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        queryset = SensorData.objects.filter(
            Q(unidade_armazenadora__in=unidades) | Q(silo__unidade_armazenadora__in=unidades) | Q(secador__unidade_armazenadora__in=unidades)
        ).distinct()
        silo = self.request.query_params.get('silo_id') or self.request.query_params.get('silo')
        if silo:
            queryset = queryset.filter(silo_id=silo)
        secador = self.request.query_params.get('secador')
        if secador:
            queryset = queryset.filter(secador_id=secador)
        return queryset

class TelemetryViewSet(viewsets.ModelViewSet):
    queryset = Telemetry.objects.all()
    serializer_class = TelemetrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        queryset = Telemetry.objects.filter(
            Q(sensor__unidade_armazenadora__in=unidades) |
            Q(sensor__silo__unidade_armazenadora__in=unidades) |
            Q(sensor__secador__unidade_armazenadora__in=unidades)
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
        unidades = self.request.user.get_accessible_unidades()
        return Silo.objects.filter(unidade_armazenadora__in=unidades)

class UnidadeArmazenadoraViewSet(viewsets.ModelViewSet):
    serializer_class = UnidadeArmazenadoraSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        return self.request.user.get_accessible_unidades()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        return Lote.objects.filter(unidade_armazenadora__in=unidades)

class SecadorViewSet(viewsets.ModelViewSet):
    serializer_class = SecadorSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        return Secador.objects.filter(unidade_armazenadora__in=unidades)

class ProcessoViewSet(viewsets.ModelViewSet):
    serializer_class = ProcessoSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        return Processo.objects.filter(lote__unidade_armazenadora__in=unidades)

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
            my_unidades = user.unidades_armazenadoras.all()
            return User.objects.filter(
                unidade_armazenadora__in=my_unidades, account_type__in=['operador', 'visualizador']
            ) | User.objects.filter(id=user.id)
        return User.objects.none()

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated, IsAdminOrDeleteOnly]

    def get_queryset(self):
        unidades = self.request.user.get_accessible_unidades()
        return Cliente.objects.filter(unidade_armazenadora__in=unidades)

    def perform_create(self, serializer):
        unidades = self.request.user.get_accessible_unidades()
        unidade_id = self.request.data.get('unidade_armazenadora')
        if not unidade_id:
            unidade = unidades.first()
        else:
            unidade = unidades.filter(id=unidade_id).first()
        if not unidade:
            raise PermissionError("Você não tem permissão para vincular clientes a esta unidade armazenadora.")
        serializer.save(unidade_armazenadora=unidade)


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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def custos_secagem_view(request):
    """Retorna custos calculados para todos os processos de secagem finalizados."""
    unidades = request.user.get_accessible_unidades()
    processos = Processo.objects.filter(
        tipo_processo='Secagem',
        lote__unidade_armazenadora__in=unidades,
        data_fim__isnull=False,
    ).select_related('lote', 'secador').order_by('-data_fim')

    secador_id = request.query_params.get('secador')
    if secador_id:
        processos = processos.filter(secador_id=secador_id)

    data_inicio = request.query_params.get('data_inicio')
    if data_inicio:
        processos = processos.filter(data_inicio__gte=data_inicio)

    data_fim = request.query_params.get('data_fim')
    if data_fim:
        processos = processos.filter(data_inicio__lte=data_fim)

    results = []
    for p in processos:
        cost_data = calcular_custos_processo(p)
        if cost_data:
            lote = p.lote
            secador = p.secador
            agua_removida_kg = None
            if lote and lote.peso_final and lote.peso_inicial:
                agua_removida_kg = lote.peso_inicial - lote.peso_final
            custo_por_ton_agua = None
            if agua_removida_kg and agua_removida_kg > 0 and cost_data.get('custo_total', 0) > 0:
                custo_por_ton_agua = cost_data['custo_total'] / (agua_removida_kg / 1000)

            results.append({
                'processo_id': p.id,
                'tipo_processo': p.tipo_processo,
                'status': p.status,
                'data_inicio': p.data_inicio,
                'data_fim': p.data_fim,
                'lote_id': lote.id if lote else None,
                'lote_numero': lote.numero_lote if lote else None,
                'lote_cultura': lote.cultura if lote else None,
                'lote_peso_inicial': lote.peso_inicial if lote else None,
                'lote_peso_final': lote.peso_final if lote else None,
                'secador_id': secador.id if secador else None,
                'secador_nome': secador.nome if secador else None,
                'secador_fonte_calor': secador.fonte_calor if secador else None,
                **cost_data,
                'agua_removida_kg': round(agua_removida_kg, 2) if agua_removida_kg else None,
                'custo_por_ton_agua': round(custo_por_ton_agua, 2) if custo_por_ton_agua else None,
            })

    return Response(results)


