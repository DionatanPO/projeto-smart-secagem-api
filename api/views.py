from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .models import SensorData, User, Silo, Telemetry, Farm, Lote, Secador, Processo, Cliente
from .serializers import SensorDataSerializer, UserSerializer, SiloSerializer, TelemetrySerializer, FarmSerializer, LoteSerializer, SecadorSerializer, ProcessoSerializer, ClienteSerializer
from .services.local_ai_service import LocalAIService
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta


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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analisar_silo_view(request, silo_id):
    try:
        silo = Silo.objects.get(pk=silo_id)
        # Buscar as últimas 10 telemetrias dos sensores deste silo
        telemetrias = Telemetry.objects.filter(sensor__silo=silo).order_by('-timestamp')[:10]
        
        dados_lista = []
        for t in telemetrias:
            dados_lista.append({
                "temp": t.temperatura,
                "umid": t.umidade,
                "data": t.timestamp.strftime("%d/%m %H:%M")
            })
            
        # Buscar o produto a partir do lote ativo no silo
        lote_ativo = Lote.objects.filter(silo=silo, status__in=['aguardando', 'secando', 'finalizado']).first()
        produto = lote_ativo.cultura if lote_ativo else "Vazio/Não informado"

        service = LocalAIService()
        insight = service.analisar_telemetria(
            silo_name=silo.name,
            produto=produto,
            dados_telemetria=dados_lista
        )
        
        return Response({"insight": insight}, status=status.HTTP_200_OK)
    except Silo.DoesNotExist:
        return Response({"error": "Silo não encontrado"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_ia_view(request):
    """
    Recebe uma pergunta do usuário e responde com base em um snapshot completo do sistema.
    """
    mensagem = request.data.get('message')
    if not mensagem:
        return Response({"error": "Mensagem não fornecida"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Gerar Snapshot do Sistema
        contexto = get_sistema_context()
        
        # 2. Chamar o serviço de IA
        service = LocalAIService()
        resposta = service.responder_chat(mensagem, contexto)
        
        return Response({"response": resposta}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_sistema_context():
    """
    Gera uma string formatada com o estado atual de todo o sistema para a IA.
    """
    agora = timezone.now()
    inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    
    contexto = f"Data/Hora Atual: {agora.strftime('%d/%m/%Y %H:%M')}\n\n"
    
    # --- Silos e Sensores ---
    contexto += "--- ESTADO DOS SILOS ---\n"
    silos = Silo.objects.all()
    for s in silos:
        lote_ativo = Lote.objects.filter(silo=s, status__in=['aguardando', 'secando', 'finalizado']).first()
        produto = lote_ativo.cultura if lote_ativo else "Vazio"
        contexto += f"Silo: {s.name} | Status: {s.get_status_display()} | Produto: {produto} | Cap: {s.capacity}t\n"
        
        for sensor in s.sensors.all():
            # Estatísticas do dia (últimas 24h ou desde meia-noite)
            stats = Telemetry.objects.filter(sensor=sensor, timestamp__gte=inicio_dia).aggregate(
                avg_temp=Avg('temperatura'),
                max_temp=Max('temperatura'),
                min_temp=Min('temperatura'),
                avg_umid=Avg('umidade')
            )
            
            ultima = Telemetry.objects.filter(sensor=sensor).order_by('-timestamp').first()
            
            contexto += f"  - Sensor {sensor.sensor_id}: "
            if ultima:
                contexto += f"Atual: {ultima.temperatura}°C / {ultima.umidade}% | "
            if stats['avg_temp']:
                contexto += f"Hoje -> Média: {stats['avg_temp']:.1f}°C, Máx: {stats['max_temp']:.1f}°C, Mín: {stats['min_temp']:.1f}°C\n"
            else:
                contexto += "Sem dados hoje.\n"
    
    # --- Lotes ---
    contexto += "\n--- LOTES ATIVOS ---\n"
    lotes = Lote.objects.exclude(status='despachado')[:5]
    for l in lotes:
        contexto += f"Lote: {l.numero_lote} | Cultura: {l.cultura} | Status: {l.status} | Umidade Inicial: {l.umidade_inicial}%\n"
        
    # --- Processos ---
    contexto += "\n--- PROCESSOS RECENTES ---\n"
    try:
        processos = Processo.objects.all().order_by('-data_inicio')[:5]
        for p in processos:
            inicio_str = p.data_inicio.strftime('%d/%m %H:%M') if p.data_inicio else "N/A"
            duracao = ""
            if p.data_inicio and p.data_fim:
                duracao = f" | Duração: {p.data_fim - p.data_inicio}"
            elif p.data_inicio:
                duracao = " | Em andamento"
            
            silo_nome = p.lote.silo.name if (p.lote and p.lote.silo) else "Desconhecido"
            contexto += f"Processo: {p.tipo_processo} | Status: {p.status} | Silo: {silo_nome} | Início: {inicio_str}{duracao}\n"
    except Exception as e:
        contexto += f"Erro ao listar processos: {str(e)}\n"

    # --- Fazenda e Clientes ---
    contexto += "\n--- INFORMAÇÕES ESTRUTURAIS ---\n"
    try:
        fazenda = Farm.objects.first()
        if fazenda:
            contexto += f"Fazenda: {fazenda.name} | Local: {fazenda.location}\n"
        
        clientes_count = Cliente.objects.count()
        contexto += f"Total de Clientes Cadastrados: {clientes_count}\n"
    except:
        pass
    
    # --- Dispositivos e Infraestrutura ---
    contexto += "\n--- DISPOSITIVOS E INFRAESTRUTURA ---\n"
    try:
        secadores = Secador.objects.all()
        for sec in secadores:
            silo_vinculado = sec.lote.silo.name if (hasattr(sec, 'lote') and sec.lote and sec.lote.silo) else 'Nenhum'
            # Nota: O modelo Secador não tem lote direto no models.py, vou simplificar
            contexto += f"Secador: {sec.nome} | Modelo: {sec.tipo} | Fonte: {sec.fonte_calor}\n"
    except:
        pass

    return contexto
