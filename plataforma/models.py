from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Silo(models.Model):
    id_silo = models.AutoField(primary_key=True, editable=False, auto_created=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    identificacao = models.CharField(max_length=255)
    observacao = models.CharField(max_length=255)
    status = models.CharField(max_length=255)


class Sensor(models.Model):
    id_sensor = models.AutoField(primary_key=True, editable=False, auto_created=True)
    silo = models.ForeignKey(Silo, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    unidade = models.CharField(max_length=25)
    tipo = models.CharField(max_length=45)
    status = models.CharField(max_length=255)
    observacao = models.CharField(max_length=255)
    time = models.DateTimeField(default=timezone.now)


class SensorData(models.Model):
    id_sensor_data = models.AutoField(primary_key=True, editable=False, auto_created=True)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    valor = models.CharField(max_length=25)
    time = models.DateTimeField(default=timezone.now)


class Controlador(models.Model):
    id_controlador = models.AutoField(primary_key=True, editable=False, auto_created=True)
    silo = models.ForeignKey(Silo, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=45)
    status = models.CharField(max_length=255)
    observacao = models.CharField(max_length=255)
    time = models.DateTimeField(default=timezone.now)


class AeracaoSilo(models.Model):
    silo = models.ForeignKey(Silo, on_delete=models.CASCADE)
    volume = models.FloatField(help_text='Volume do silo em m³', null=True)
    temperatura_inicial = models.FloatField(help_text='Temperatura inicial em °C', null=True)
    umidade_inicial = models.FloatField(help_text='Umidade relativa inicial em %', null=True)
    temperatura_desejada = models.FloatField(help_text='Temperatura desejada em °C', null=True)
    umidade_desejada = models.FloatField(help_text='Umidade relativa desejada em %', null=True)
    taxa_fluxo_ar = models.FloatField(help_text='Taxa de fluxo de ar em m³/s', null=True)
    time = models.DateTimeField(default=timezone.now)

    @staticmethod
    def calcular_aeracao_manutencao(valor, valor2, silo, sensor):
        global alerta
        if sensor.tipo != "Temperatura":
            return False

        temp_maior = float(valor)
        tempe_externa = float(valor2)
        diferenca = temp_maior - tempe_externa

        controlador_status = "Desligado" if diferenca < 3 else "Ligado"

        try:
            controlador = Controlador.objects.get(tipo="Aeração", silo_id=silo.id_silo)

            if diferenca >= 3:
                if controlador.status == "Ligado":
                    return False
                else:
                    titulo = "Alerta de Temperatura"
                    alert_descricao = 'Temperatura interna está acima da temperatura externa. Sistema de aeração foi acionado.'
                    alerta = Alerta.objects.create(
                        silo=silo,
                        sensor=sensor,
                        titulo=titulo,
                        user_id=silo.user_id,
                        descricao=alert_descricao
                    )

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'temperatura_notifications',
                        {
                            'type': 'temperatura_notification',
                            'titulo': 'Alerta de Temperatura sensor: ' + sensor.nome,
                            'descricao':'Temperatura interna do ' + sensor.silo.identificacao + ' acima da temperatura externa. Sistema de aeração foi acionado.',
                            'time': alerta.time.isoformat(),
                        }
                    )
                    controlador.status = controlador_status
                    controlador.save()

                    return True
                
            else:
                if controlador.status == "Ligado" and diferenca < 3:

                    titulo = "Alerta de Temperatura"
                    alert_descricao = 'Temperatura interna está abaixo da temperatura externa. Sistema de aeração foi desligado.'
                    alerta = Alerta.objects.create(
                        silo=silo,
                        sensor=sensor,
                        titulo=titulo,
                        user_id=silo.user_id,
                        descricao=alert_descricao
                    )

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        'temperatura_notifications',
                        {
                            'type': 'temperatura_notification',
                            'titulo': 'Alerta de Temperatura sensor: ' + sensor.nome,
                            'descricao':'Temperatura interna do ' + sensor.silo.identificacao + ' abaixo da temperatura externa. Sistema de aeração foi desligado.',
                            'time': alerta.time.isoformat(),
                        }
                    )
                    controlador.status = controlador_status
                    controlador.save()

                    return True


        except Controlador.DoesNotExist:
            return True

        return False



class Alerta(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    silo = models.ForeignKey(Silo, on_delete=models.CASCADE)
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField()
    time = models.DateTimeField(default=timezone.now)
