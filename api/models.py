from django.db import models
from django.contrib.auth.models import AbstractUser

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
        ('ativo', 'Ativo'),
        ('manutencao', 'Em Manutenção'),
        ('desativado', 'Desativado'),
    )
    
    name = models.CharField(max_length=100, verbose_name="Nome do Silo")
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='silos', null=True, blank=True, verbose_name="Fazenda/Armazém")
    capacity = models.FloatField(verbose_name="Capacidade Máxima (Toneladas)")
    current_quantity = models.FloatField(default=0, verbose_name="Quantidade Atual (Toneladas)")
    product_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Tipo de Produto")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status")
    observations = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ['name']
        verbose_name = 'Silo'
        verbose_name_plural = 'Silos'

    def __str__(self):
        return f"{self.name} ({self.product_type if self.product_type else 'Vazio'})"
