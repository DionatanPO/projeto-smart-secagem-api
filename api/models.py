from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ACCOUNT_TYPES = (
        ('super_admin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('visualizador', 'Visualizador'),
    )

    HIERARCHY = {
        'super_admin': 0,
        'admin': 1,
        'operador': 2,
        'visualizador': 3,
    }

    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='visualizador', verbose_name="Tipo de Conta")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    unidade_armazenadora = models.ForeignKey('UnidadeArmazenadora', on_delete=models.SET_NULL, null=True, blank=True, related_name='operadores', verbose_name="Unidade Armazenadora Vinculada")

    def __str__(self):
        return f"{self.username} ({self.get_account_type_display()})"

    def get_accessible_unidades(self):
        if self.account_type == 'super_admin':
            return UnidadeArmazenadora.objects.all()
        if self.account_type == 'operador' and self.unidade_armazenadora:
            return UnidadeArmazenadora.objects.filter(id=self.unidade_armazenadora.id)
        if self.account_type == 'admin':
            return self.unidades_armazenadoras.all()
        return UnidadeArmazenadora.objects.none()

    def can_manage_type(self, target_type):
        my_level = self.HIERARCHY.get(self.account_type, 99)
        target_level = self.HIERARCHY.get(target_type, 99)
        return my_level < target_level

    def can_manage_user(self, target_user):
        return self.can_manage_type(target_user.account_type)

    def save(self, *args, **kwargs):
        if self.account_type == 'super_admin':
            self.is_staff = True
            self.is_superuser = True
        elif self.account_type == 'admin':
            self.is_staff = True
            self.is_superuser = False
        elif self.account_type == 'operador':
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)

class SensorData(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('falha', 'Falha de Leitura'),
        ('desativado', 'Desativado'),
    )
    sensor_id = models.CharField(max_length=50, unique=True, verbose_name="ID do Sensor (Físico)")
    tipo = models.CharField(max_length=100, default='sensor_temperatura', verbose_name="Tipo de Dispositivo")
    
    silo = models.ForeignKey('Silo', on_delete=models.CASCADE, related_name='sensors', null=True, blank=True)
    secador = models.ForeignKey('Secador', on_delete=models.CASCADE, related_name='sensors', null=True, blank=True)
    unidade_armazenadora = models.ForeignKey('UnidadeArmazenadora', on_delete=models.CASCADE, related_name='sensors', null=True, blank=True)
    
    description = models.CharField(max_length=100, blank=True, verbose_name="Descrição/Localização")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status de Operação")

    class Meta:
        verbose_name = 'Configuração de Sensor'
        verbose_name_plural = 'Configurações de Sensores'

    def __str__(self):
        return f"Sensor {self.sensor_id} - {self.silo.name if self.silo else 'Sem Silo'}"

class Telemetry(models.Model):
    sensor = models.ForeignKey(SensorData, on_delete=models.CASCADE, related_name='telemetries')
    temperatura = models.FloatField(null=True, blank=True, verbose_name="Temperatura (°C)")
    umidade = models.FloatField(null=True, blank=True, verbose_name="Umidade (%)")
    dados_extras = models.JSONField(default=dict, blank=True, null=True, verbose_name="Dados Extras (JSON)")
    timestamp = models.DateTimeField(verbose_name="Data/Hora da Coleta (ISO)")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora de Recebimento")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Telemetria'
        verbose_name_plural = 'Telemetrias'

    def __str__(self):
        return f"{self.sensor.sensor_id} | {self.temperatura}°C | {self.timestamp}"

class UnidadeArmazenadora(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unidades_armazenadoras', verbose_name="Dono/Usuário")
    name = models.CharField(max_length=100, verbose_name="Nome da Unidade Armazenadora")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Localização/Cidade")
    description = models.TextField(blank=True, null=True, verbose_name="Observações da Unidade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        ordering = ['name']
        verbose_name = 'Unidade Armazenadora'
        verbose_name_plural = 'Unidades Armazenadoras'

    def __str__(self):
        return self.name

class Silo(models.Model):
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Manutenção'),
        ('desativado', 'Desativado'),
    )
    TIPO_CHOICES = (
        ('pulmao', 'Silo Pulmão'),
        ('armazenamento', 'Silo de Armazenamento'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nome do Silo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='pulmao', verbose_name="Tipo do Silo")
    unidade_armazenadora = models.ForeignKey(UnidadeArmazenadora, on_delete=models.CASCADE, related_name='silos', null=True, blank=True, verbose_name="Unidade Armazenadora")
    capacity = models.FloatField(verbose_name="Capacidade Máxima (Toneladas)")
    current_quantity = models.FloatField(default=0, verbose_name="Quantidade Atual (Toneladas)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disponivel', verbose_name="Status")
    observations = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['name']
        verbose_name = 'Silo'
        verbose_name_plural = 'Silos'

    def __str__(self):
        return self.name

class Lote(models.Model):
    STATUS_CHOICES = (
        ('aguardando', 'Aguardando'),
        ('finalizado', 'Finalizado'),
        ('despachado', 'Despachado'),
        ('Secagem (Iniciada)', 'Secagem (Iniciada)'),
        ('Secagem (Pausada)', 'Secagem (Pausada)'),
        ('Secagem (Finalizada)', 'Secagem (Finalizada)'),
        ('Secagem (Cancelada)', 'Secagem (Cancelada)'),
        ('Aeração (Iniciada)', 'Aeração (Iniciada)'),
        ('Aeração (Pausada)', 'Aeração (Pausada)'),
        ('Aeração (Finalizada)', 'Aeração (Finalizada)'),
        ('Aeração (Cancelada)', 'Aeração (Cancelada)'),
    )

    numero_lote = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Número do Lote")
    unidade_armazenadora = models.ForeignKey(UnidadeArmazenadora, on_delete=models.CASCADE, related_name='lotes', verbose_name="Unidade Armazenadora")
    cliente = models.ForeignKey('Cliente', on_delete=models.PROTECT, related_name='lotes', verbose_name="Cliente/Produtor", null=True)
    cultura = models.CharField(max_length=100, verbose_name="Cultura (ex: Milho, Soja)")
    variedade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Variedade")
    safra = models.CharField(max_length=20, verbose_name="Safra")
    
    # Dados de Entrada
    peso_inicial = models.FloatField(verbose_name="Peso Inicial (kg)")
    umidade_inicial = models.FloatField(verbose_name="Umidade Inicial (%)")
    data_entrada = models.DateTimeField(auto_now_add=True, verbose_name="Data de Entrada")
    
    # Dados de Saída (preenchidos depois)
    peso_final = models.FloatField(null=True, blank=True, verbose_name="Peso Final (kg)")
    umidade_final = models.FloatField(null=True, blank=True, verbose_name="Umidade Final (%)")
    data_saida = models.DateTimeField(null=True, blank=True, verbose_name="Data de Saída")
    
    # Vínculos e Status
    silo = models.ForeignKey(Silo, on_delete=models.SET_NULL, null=True, blank=True, related_name='lotes', verbose_name="Silo de Destino")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='aguardando', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    placa_caminhao = models.CharField(max_length=20, blank=True, null=True, verbose_name="Placa do Caminhão")
    motorista_nome = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nome do Motorista")
    peso_caminhao = models.FloatField(null=True, blank=True, verbose_name="Peso do Caminhão (kg)")

    class Meta:
        ordering = ['-data_entrada']
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.cultura}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Salvamos primeiro para garantir o ID se for novo
        super().save(*args, **kwargs)
        
        # Se for novo e não tiver número, gera baseado no ID
        if is_new and not self.numero_lote:
            self.numero_lote = f"LOTE-{self.id:04d}"
            # Atualiza no banco sem disparar o save novamente
            Lote.objects.filter(pk=self.pk).update(numero_lote=self.numero_lote)
            
        # Lógica de Automação de Status do Silo
        if self.silo:
            if 'despachado' in self.status.lower():
                self.silo.status = 'disponivel'
            else:
                self.silo.status = 'em_uso'
            self.silo.save()

class Secador(models.Model):
    STATUS_CHOICES = (
        ('Disponível', 'Disponível'),
        ('Em Uso', 'Em Uso'),
        ('Em Manutenção', 'Em Manutenção'),
        ('Desativado', 'Desativado'),
    )
    TIPO_CHOICES = (
        ('Coluna', 'Coluna'),
        ('Cascata', 'Cascata'),
        ('Fluxo Contínuo', 'Fluxo Contínuo'),
        ('Batelada', 'Batelada'),
    )
    FONTE_CALOR_CHOICES = (
        ('Lenha', 'Lenha'),
        ('Gás GLP', 'Gás GLP'),
        ('Biomassa', 'Biomassa'),
        ('Elétrico', 'Elétrico'),
    )

    nome = models.CharField(max_length=100, verbose_name="Nome do Secador")
    unidade_armazenadora = models.ForeignKey(UnidadeArmazenadora, on_delete=models.CASCADE, related_name='secadores', verbose_name="Unidade Armazenadora")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='Coluna', verbose_name="Tipo")
    capacidade = models.FloatField(verbose_name="Capacidade (t/h)")
    fonte_calor = models.CharField(max_length=20, choices=FONTE_CALOR_CHOICES, default='Lenha', verbose_name="Fonte de Calor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Disponível', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")

    # Custos de Capital
    custo_aquisicao = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Custo de Aquisição (R$)")
    valor_residual = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Valor Residual (R$)")
    vida_util_anos = models.IntegerField(blank=True, null=True, verbose_name="Vida Útil (anos)")

    # Custos Operacionais
    custo_instalacao = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Custo de Instalação (R$)")
    custo_manutencao_anual = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, verbose_name="Custo de Manutenção Anual (R$)")
    consumo_combustivel_hora = models.FloatField(blank=True, null=True, verbose_name="Consumo de Combustível (L/h ou kg/h)")
    preco_combustivel = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Preço do Combustível (R$/un)")
    consumo_energia_kwh = models.FloatField(blank=True, null=True, verbose_name="Consumo de Energia (kWh)")
    preco_kwh = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True, verbose_name="Preço da Energia (R$/kWh)")
    custo_mao_obra_hora = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Custo de Mão de Obra (R$/h)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Secador'
        verbose_name_plural = 'Secadores'

    def __str__(self):
        return f"{self.nome} - {self.unidade_armazenadora.name}"

class Processo(models.Model):
    TIPO_PROCESSO_CHOICES = (
        ('Triagem', 'Triagem'),
        ('Secagem', 'Secagem'),
        ('Resfriamento', 'Resfriamento'),
        ('Armazenamento', 'Armazenamento'),
    )
    
    STATUS_CHOICES = (
        ('Iniciada', 'Iniciada'),
        ('Pausada', 'Pausada'),
        ('Finalizada', 'Finalizada'),
        ('Cancelada', 'Cancelada'),
    )

    tipo_processo = models.CharField(max_length=20, choices=TIPO_PROCESSO_CHOICES, default='Secagem', verbose_name="Tipo de Atividade")
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='processos', verbose_name="Lote", null=True, blank=True)
    secador = models.ForeignKey(Secador, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos', verbose_name="Secador")
    silo = models.ForeignKey(Silo, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos', verbose_name="Silo")
    
    data_inicio = models.DateTimeField(default=timezone.now, verbose_name="Data de Início")
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name="Data de Fim")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Iniciada', verbose_name="Status")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Operador Responsável")
    dados_extras = models.JSONField(default=dict, blank=True, verbose_name="Dados Extras")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_inicio']
        verbose_name = 'Processo Operacional'
        verbose_name_plural = 'Processos Operacionais'

    def __str__(self):
        lote_str = self.lote.numero_lote if self.lote else "S/ Lote"
        return f"{self.tipo_processo} | {lote_str} | {self.status}"

    def save(self, *args, **kwargs):
        # Validação de Segurança: Um lote não pode ter duas atividades ativas ao mesmo tempo
        if self.lote and self.status in ['Iniciada', 'Pausada']:
            # Procuramos outros processos ativos para este mesmo lote (excluindo o atual)
            conflito = Processo.objects.filter(
                lote=self.lote, 
                status__in=['Iniciada', 'Pausada']
            ).exclude(pk=self.pk).exists()
            
            if conflito:
                raise ValueError(f"O lote {self.lote.numero_lote} já possui uma atividade em andamento ou pausada.")

        # Primeiro salvamos o processo
        super().save(*args, **kwargs)
        
        # Sincronização automática com o status do Lote
        if self.lote:
            # Ex: Secagem (Iniciada), Aeração (Finalizada)
            new_status = f"{self.tipo_processo} ({self.status})"
            
            Lote.objects.filter(id=self.lote.id).update(status=new_status)
            self.lote.refresh_from_db()
            self.lote.save()

class MotorAeracao(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('falha', 'Falha'),
        ('desativado', 'Desativado'),
    )
    ESTADO_CHOICES = (
        ('ligado', 'Ligado'),
        ('desligado', 'Desligado'),
    )

    motor_id = models.CharField(max_length=50, unique=True, verbose_name="ID do Motor")
    description = models.CharField(max_length=200, verbose_name="Descrição/Localização")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status Operacional")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='desligado', verbose_name="Estado")

    potencia_kw = models.FloatField(null=True, blank=True, verbose_name="Potência (kW)")
    rpm = models.FloatField(null=True, blank=True, verbose_name="RPM")
    vazao_ar = models.FloatField(null=True, blank=True, verbose_name="Vazão de Ar (m³/h)")
    horimetro = models.FloatField(null=True, blank=True, verbose_name="Horímetro (horas)")
    consumo_atual_kw = models.FloatField(null=True, blank=True, verbose_name="Consumo Atual (kW)")

    silo = models.ForeignKey('Silo', on_delete=models.SET_NULL, null=True, blank=True, related_name='motores_aeracao', verbose_name="Silo Vinculado")
    secador = models.ForeignKey('Secador', on_delete=models.SET_NULL, null=True, blank=True, related_name='motores_aeracao', verbose_name="Secador Vinculado")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['motor_id']
        verbose_name = 'Motor de Aeração'
        verbose_name_plural = 'Motores de Aeração'

    def __str__(self):
        return f"{self.motor_id} - {self.description}"


class Cliente(models.Model):
    unidade_armazenadora = models.ForeignKey(UnidadeArmazenadora, on_delete=models.CASCADE, related_name='clientes', verbose_name="Unidade Armazenadora", null=True, blank=True)
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    email = models.EmailField(max_length=200, blank=True, null=True, verbose_name="E-mail")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    cpf_cnpj = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="CPF/CNPJ")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['nome']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome
