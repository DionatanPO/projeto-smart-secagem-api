from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ACCOUNT_TYPES = (
        ('admin', 'Administrador'),
        ('operador', 'Operador'),
        ('visualizador', 'Visualizador'),
    )
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='visualizador', verbose_name="Tipo de Conta")

    def __str__(self):
        return f"{self.username} ({self.get_account_type_display()})"

class SensorData(models.Model):
    STATUS_CHOICES = (
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('falha', 'Falha de Leitura'),
        ('desativado', 'Desativado'),
    )
    sensor_id = models.CharField(max_length=50, unique=True, verbose_name="ID do Sensor (Físico)")
    silo = models.ForeignKey('Silo', on_delete=models.CASCADE, related_name='sensors', null=True, blank=True)
    description = models.CharField(max_length=100, blank=True, verbose_name="Descrição/Localização")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status de Operação")

    class Meta:
        verbose_name = 'Configuração de Sensor'
        verbose_name_plural = 'Configurações de Sensores'

    def __str__(self):
        return f"Sensor {self.sensor_id} - {self.silo.name if self.silo else 'Sem Silo'}"

class Telemetry(models.Model):
    sensor = models.ForeignKey(SensorData, on_delete=models.CASCADE, related_name='telemetries')
    temperatura = models.FloatField(verbose_name="Temperatura (°C)")
    umidade = models.FloatField(verbose_name="Umidade (%)")
    timestamp = models.DateTimeField(verbose_name="Data/Hora da Coleta (ISO)")
    received_at = models.DateTimeField(auto_now_add=True, verbose_name="Data/Hora de Recebimento")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Telemetria'
        verbose_name_plural = 'Telemetrias'

    def __str__(self):
        return f"{self.sensor.sensor_id} | {self.temperatura}°C | {self.timestamp}"

class Farm(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms', verbose_name="Dono/Usuário")
    name = models.CharField(max_length=100, verbose_name="Nome da Fazenda/Armazém")
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name="Localização/Cidade")
    description = models.TextField(blank=True, null=True, verbose_name="Observações da Unidade")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        ordering = ['name']
        verbose_name = 'Fazenda/Armazém'
        verbose_name_plural = 'Fazendas/Armazéns'

    def __str__(self):
        return self.name

class Silo(models.Model):
    STATUS_CHOICES = (
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('manutencao', 'Manutenção'),
        ('desativado', 'Desativado'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nome do Silo")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='silos', null=True, blank=True, verbose_name="Fazenda/Armazém")
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
        return f"{self.name} ({self.product_type if self.product_type else 'Vazio'})"

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

    numero_lote = models.CharField(max_length=50, unique=True, verbose_name="Número do Lote")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='lotes', verbose_name="Fazenda/Unidade")
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

    class Meta:
        ordering = ['-data_entrada']
        verbose_name = 'Lote'
        verbose_name_plural = 'Lotes'

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.cultura}"

    def save(self, *args, **kwargs):
        # Primeiro salvamos o lote
        super().save(*args, **kwargs)
        
        # Lógica de Automação de Status do Silo
        if self.silo:
            # Se o status contiver o nome de uma atividade (indicado pelo parênteses),
            # ou se estiver explicitamente 'aguardando' ou 'finalizado', o silo está em uso.
            # O silo só fica disponível se o lote for 'despachado'.
            
            if 'despachado' in self.status.lower():
                self.silo.status = 'disponivel'
            else:
                # Qualquer outro status (aguardando, atividades, finalizados) mantém o silo ocupado
                self.silo.status = 'em_uso'
            
            self.silo.save()

class Secador(models.Model):
    STATUS_CHOICES = (
        ('Ativo', 'Ativo'),
        ('Manutenção', 'Manutenção'),
        ('Inativo', 'Inativo'),
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
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='secadores', verbose_name="Fazenda/Unidade")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='Coluna', verbose_name="Tipo")
    capacidade = models.FloatField(verbose_name="Capacidade (t/h)")
    fonte_calor = models.CharField(max_length=20, choices=FONTE_CALOR_CHOICES, default='Lenha', verbose_name="Fonte de Calor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ativo', verbose_name="Status")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Secador'
        verbose_name_plural = 'Secadores'

    def __str__(self):
        return f"{self.nome} - {self.farm.name}"

class Processo(models.Model):
    TIPO_PROCESSO_CHOICES = (
        ('Secagem', 'Secagem'),
        ('Aeração', 'Aeração'),
    )
    
    STATUS_CHOICES = (
        ('Iniciada', 'Iniciada'),
        ('Pausada', 'Pausada'),
        ('Finalizada', 'Finalizada'),
        ('Cancelada', 'Cancelada'),
    )

    tipo_processo = models.CharField(max_length=20, choices=TIPO_PROCESSO_CHOICES, default='Secagem', verbose_name="Tipo de Atividade")
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='processos', verbose_name="Lote", null=True, blank=True)
    
    data_inicio = models.DateTimeField(default=timezone.now, verbose_name="Data de Início")
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name="Data de Fim")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Iniciada', verbose_name="Status")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Operador Responsável")
    
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
