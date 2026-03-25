from django.db.models import Max, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SensorData, AeracaoSilo, Silo, Sensor
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@receiver(post_save, sender=SensorData)
def check_temperature(sender, instance, **kwargs):
    try:
        sensor = Sensor.objects.select_related('silo').get(id_sensor=instance.sensor.id_sensor)

    except Sensor.DoesNotExist:
        print(f"Sensor com id {instance.sensor.id_sensor} não encontrado.")
        return

    try:
        silo = Silo.objects.get(id_silo=sensor.silo.id_silo)
    except Silo.DoesNotExist:
        print(f"Silo com id {sensor.silo.id_silo} não encontrado.")
        return
    try:
        sensor_estacao = Sensor.objects.get(nome="Estação externa", silo_id=sensor.silo.id_silo)
    except Sensor.DoesNotExist:
        silo.save()
        print("Sensor 'Estação externa' não encontrado.")
        return  # Para a execução se o sensor 'Estação externa' não for encontrado

    # Se o sensor 'Estação externa' for encontrado, continue com o restante da lógica
    ultimo_dado_estacao = SensorData.objects.filter(sensor_id=sensor_estacao.id_sensor).order_by('-time').first()

    sensores_temperatura = Sensor.objects.filter(
        silo_id=silo.id_silo,
        tipo='Temperatura'
    ).exclude(
        Q(nome='Estação externa') | Q(nome__icontains='estação externa')
    )

    ultimos_dados_sensores = []
    maiores_valores_sensores = []

    sensor_maior_valor = None
    maior_valor_global = float('-inf')

    for sensor in sensores_temperatura:
        try:
            ultimo_dado_sensor = SensorData.objects.filter(sensor=sensor).latest('time')
            maior_valor_sensor = float(ultimo_dado_sensor.valor)
            ultimos_dados_sensores.append(ultimo_dado_sensor)
            maiores_valores_sensores.append(maior_valor_sensor)

            if maior_valor_sensor > maior_valor_global:
                maior_valor_global = maior_valor_sensor
                sensor_maior_valor = sensor
        except SensorData.DoesNotExist:
            print(f"Dados do sensor {sensor.nome} não encontrados.")

    try:
        print(f"Maior valor global entre todos os sensores de temperatura: {maior_valor_global}")
        if sensor_maior_valor is not None:
            AeracaoSilo.calcular_aeracao_manutencao(maior_valor_global, ultimo_dado_estacao.valor, sensor.silo,
                                                    sensor_maior_valor)
            print(f"Sensor com maior valor: {sensor_maior_valor.nome}")
        else:
            print("Nenhum sensor com maior valor encontrado.")
    except AeracaoSilo.DoesNotExist:
        print("Objeto AeracaoSilo não encontrado no banco de dados.")

    silo.save()


@receiver(post_save, sender=Silo)
def silo_updated(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    silo_data = {
        'id_silo': instance.id_silo,
        'identificacao': instance.identificacao,
        'observacao': instance.observacao,
        'status': instance.status,
        'user_id': instance.user.id,
    }
    async_to_sync(channel_layer.group_send)(
        f"silo_{instance.id_silo}",
        {
            "type": "silo_update",
            "message": silo_data  # Enviar o dicionário diretamente
        }
    )
