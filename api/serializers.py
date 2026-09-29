from rest_framework import serializers
from .models import SensorData, User, Silo, Telemetry, UnidadeArmazenadora, Lote, Secador, Processo, Cliente, MotorAeracao, Notificacao, ReceitaSecagem, ParametroAutomacaoSecador

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = '__all__'

    def validate(self, data):
        silo = data.get('silo', self.instance.silo if self.instance else None)
        secador = data.get('secador', self.instance.secador if self.instance else None)
        unidade = data.get('unidade_armazenadora', self.instance.unidade_armazenadora if self.instance else None)
        if not silo and not secador and not unidade:
            raise serializers.ValidationError("Sensor precisa estar vinculado a um silo, secador ou unidade armazenadora.")
        return data

class TelemetrySerializer(serializers.ModelSerializer):
    sensor_physical_id = serializers.CharField(source='sensor.sensor_id', read_only=True)
    
    class Meta:
        model = Telemetry
        fields = ['id', 'sensor', 'sensor_physical_id', 'temperatura', 'umidade', 'co2_ppm', 'dados_extras', 'timestamp', 'received_at']

class UnidadeArmazenadoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnidadeArmazenadora
        fields = '__all__'
        read_only_fields = ['owner']

class SiloSerializer(serializers.ModelSerializer):
    unidade_armazenadora_nome = serializers.CharField(source='unidade_armazenadora.name', read_only=True)
    
    class Meta:
        model = Silo
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'account_type', 'is_staff', 'first_name', 'last_name', 'telefone', 'unidade_armazenadora']
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ['is_staff']

    def validate_account_type(self, value):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return value
        creator = request.user
        target_type = value
        # Na edição, permite manter o próprio tipo sem checar hierarquia
        if self.instance and self.instance.account_type == target_type:
            return value
        if not creator.can_manage_type(target_type):
            raise serializers.ValidationError(
                f"Você ({creator.account_type}) não tem permissão para criar/gerenciar usuários do tipo '{target_type}'."
            )
        return value

    def validate_unidade_armazenadora(self, value):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return value
        creator = request.user
        target_type = self.initial_data.get('account_type', getattr(self.instance, 'account_type', None))
        # operador/visualizador exigem unidade dentro do escopo do criador
        if target_type in ('operador', 'visualizador'):
            if not value:
                raise serializers.ValidationError("Operador/visualizador precisa estar vinculado a uma unidade armazenadora.")
            acessiveis = creator.get_accessible_unidades()
            # super_admin vê todas, então qualquer unidade válida passa; admin só as suas
            if not acessiveis.filter(id=value.id).exists():
                raise serializers.ValidationError("Você não tem permissão para vincular usuários a esta unidade armazenadora.")
        return value

    def validate(self, data):
        # Impede auto-promoção: ninguém troca o próprio tipo por esse endpoint (usar admin/super_admin em outro usuário)
        request = self.context.get('request')
        if request and self.instance and request.user.id == self.instance.id:
            novo_tipo = data.get('account_type', self.instance.account_type)
            if novo_tipo != self.instance.account_type:
                raise serializers.ValidationError({"account_type": "Você não pode alterar seu próprio tipo de conta."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'telefone', 'account_type']
        read_only_fields = ['id', 'username', 'account_type']

class LoteSerializer(serializers.ModelSerializer):
    unidade_armazenadora_nome = serializers.CharField(source='unidade_armazenadora.name', read_only=True)
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
    unidade_armazenadora_nome = serializers.CharField(source='unidade_armazenadora.name', read_only=True)

    class Meta:
        model = Secador
        fields = '__all__'

class ProcessoSerializer(serializers.ModelSerializer):
    lote_numero = serializers.CharField(source='lote.numero_lote', read_only=True)
    lote_cultura = serializers.CharField(source='lote.cultura', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.username', read_only=True, default=None, allow_null=True)
    secador_nome = serializers.CharField(source='secador.nome', read_only=True, default=None, allow_null=True)
    silo_nome = serializers.CharField(source='silo.name', read_only=True, default=None, allow_null=True)

    class Meta:
        model = Processo
        fields = '__all__'

    def validate(self, data):
        from .models import Processo as ProcessoModel
        lote = data.get('lote', self.instance.lote if self.instance else None)
        if not lote:
            raise serializers.ValidationError({"lote": "Processo precisa estar vinculado a um lote."})
        tipo = data.get('tipo_processo', self.instance.tipo_processo if self.instance else 'Secagem')
        secador = data.get('secador', self.instance.secador if self.instance else None)
        if tipo == 'Secagem' and not secador:
            raise serializers.ValidationError({"secador": "Processo de Secagem exige um secador."})
        status_val = data.get('status', self.instance.status if self.instance else 'Iniciada')
        if status_val in ['Iniciada', 'Pausada']:
            conflito = ProcessoModel.objects.filter(lote=lote, status__in=['Iniciada', 'Pausada'])
            if self.instance:
                conflito = conflito.exclude(pk=self.instance.pk)
            if conflito.exists():
                raise serializers.ValidationError("Este lote já possui uma atividade em andamento ou pausada.")
        return data


class MotorAeracaoSerializer(serializers.ModelSerializer):
    silo_name = serializers.CharField(source='silo.name', read_only=True, default=None, allow_null=True)
    secador_name = serializers.CharField(source='secador.nome', read_only=True, default=None, allow_null=True)

    class Meta:
        model = MotorAeracao
        fields = '__all__'

    def validate(self, data):
        silo = data.get('silo', self.instance.silo if self.instance else None)
        secador = data.get('secador', self.instance.secador if self.instance else None)
        if not silo and not secador:
            raise serializers.ValidationError("Motor precisa estar vinculado a um silo ou secador.")
        return data


class ClienteSerializer(serializers.ModelSerializer):
    unidade_armazenadora_nome = serializers.CharField(source='unidade_armazenadora.name', read_only=True)

    class Meta:
        model = Cliente
        fields = '__all__'

    def validate_unidade_armazenadora(self, value):
        if not value:
            raise serializers.ValidationError("Cliente deve estar vinculado a uma unidade armazenadora.")
        return value


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id', 'titulo', 'descricao', 'tipo', 'icone', 'cor', 'target', 'is_read', 'created_at']


class ReceitaSecagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceitaSecagem
        fields = '__all__'

    def validate(self, data):
        alvo = data.get('temp_ar_alvo', getattr(self.instance, 'temp_ar_alvo', None))
        corte = data.get('temp_ar_max', getattr(self.instance, 'temp_ar_max', None))
        if alvo is not None and corte is not None and alvo > corte:
            raise serializers.ValidationError({"temp_ar_alvo": "Temp. alvo não pode exceder o corte máximo."})
        return data


class ParametroAutomacaoSecadorSerializer(serializers.ModelSerializer):
    secador_nome = serializers.CharField(source='secador.nome', read_only=True)
    sensor_ambiente_physical_id = serializers.CharField(source='sensor_ambiente.sensor_id', read_only=True, default=None, allow_null=True)
    receita_nome = serializers.CharField(source='receita.nome', read_only=True, default=None, allow_null=True)

    class Meta:
        model = ParametroAutomacaoSecador
        fields = '__all__'
        read_only_fields = ['atualizado_por']

    def validate(self, data):
        alvo = data.get('temp_ar_alvo', getattr(self.instance, 'temp_ar_alvo', None))
        corte = data.get('temp_ar_max', getattr(self.instance, 'temp_ar_max', None))
        if alvo is not None and corte is not None and alvo > corte:
            raise serializers.ValidationError({"temp_ar_alvo": "Temp. alvo não pode exceder o corte máximo."})
        umid_in = data.get('umidade_entrada', getattr(self.instance, 'umidade_entrada', None))
        modo = data.get('modo_descarga', getattr(self.instance, 'modo_descarga', None))
        if umid_in is not None and umid_in > 18 and modo == 'continuo':
            raise serializers.ValidationError({"modo_descarga": "Umidade de entrada acima de 18% exige descarga intermitente (contínua só até 18%)."})
        sensor = data.get('sensor_ambiente', getattr(self.instance, 'sensor_ambiente', None))
        secador = data.get('secador', getattr(self.instance, 'secador', None))
        if sensor and secador:
            if sensor.silo_id or sensor.secador_id:
                raise serializers.ValidationError({"sensor_ambiente": "Sensor ambiente deve estar vinculado só à unidade (estação meteorológica)."})
            sec_unidade = getattr(secador, 'unidade_armazenadora_id', None)
            if sec_unidade and sensor.unidade_armazenadora_id and sensor.unidade_armazenadora_id != sec_unidade:
                raise serializers.ValidationError({"sensor_ambiente": "Sensor ambiente deve ser da mesma unidade do secador."})
        return data
