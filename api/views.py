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
from decimal import Decimal
from .services.foundation_ai_service import send_chat_request
from .services.context_service import get_ai_context


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



def _calcular_custos_processo(processo):
    """Calcula custos de um processo de secagem."""
    if not processo.data_fim or not processo.data_inicio:
        return None

    duracao = processo.data_fim - processo.data_inicio
    duracao_horas = duracao.total_seconds() / 3600
    duracao_dias = duracao_horas / 24
    secador = processo.secador

    custo_combustivel = 0.0
    custo_energia = 0.0
    custo_mao_obra = 0.0
    custo_manutencao = 0.0
    custo_depreciacao = 0.0

    if secador:
        if secador.consumo_combustivel_hora and secador.preco_combustivel:
            custo_combustivel = float(secador.consumo_combustivel_hora * float(secador.preco_combustivel) * duracao_horas)
        if secador.consumo_energia_kwh and secador.preco_kwh:
            custo_energia = float(secador.consumo_energia_kwh * float(secador.preco_kwh) * duracao_horas)
        if secador.custo_mao_obra_hora:
            custo_mao_obra = float(secador.custo_mao_obra_hora) * duracao_horas
        if secador.custo_manutencao_anual:
            custo_manutencao = float(secador.custo_manutencao_anual) / 365 * duracao_dias
        if secador.custo_aquisicao and secador.valor_residual and secador.vida_util_anos:
            custo_depreciacao = (float(secador.custo_aquisicao) - float(secador.valor_residual)) / secador.vida_util_anos / 365 * duracao_dias

    custo_total = custo_combustivel + custo_energia + custo_mao_obra + custo_manutencao + custo_depreciacao

    lote = processo.lote
    agua_removida_kg = None
    if lote and lote.peso_final and lote.peso_inicial:
        agua_removida_kg = lote.peso_inicial - lote.peso_final

    custo_por_ton_agua = None
    if agua_removida_kg and agua_removida_kg > 0 and custo_total > 0:
        custo_por_ton_agua = custo_total / (agua_removida_kg / 1000)

    return {
        'processo_id': processo.id,
        'tipo_processo': processo.tipo_processo,
        'status': processo.status,
        'data_inicio': processo.data_inicio,
        'data_fim': processo.data_fim,
        'duracao_horas': round(duracao_horas, 2),
        'lote_id': lote.id if lote else None,
        'lote_numero': lote.numero_lote if lote else None,
        'lote_cultura': lote.cultura if lote else None,
        'lote_peso_inicial': lote.peso_inicial if lote else None,
        'lote_peso_final': lote.peso_final if lote else None,
        'secador_id': secador.id if secador else None,
        'secador_nome': secador.nome if secador else None,
        'secador_fonte_calor': secador.fonte_calor if secador else None,
        'custo_combustivel': round(custo_combustivel, 2),
        'custo_energia': round(custo_energia, 2),
        'custo_mao_obra': round(custo_mao_obra, 2),
        'custo_manutencao': round(custo_manutencao, 2),
        'custo_depreciacao': round(custo_depreciacao, 2),
        'custo_total': round(custo_total, 2),
        'custo_por_hora': round(custo_total / duracao_horas, 2) if duracao_horas > 0 else 0,
        'custo_por_ton_agua': round(custo_por_ton_agua, 2) if custo_por_ton_agua else None,
        'agua_removida_kg': round(agua_removida_kg, 2) if agua_removida_kg else None,
    }


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
        cost_data = _calcular_custos_processo(p)
        if cost_data:
            results.append(cost_data)

    return Response(results)


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
