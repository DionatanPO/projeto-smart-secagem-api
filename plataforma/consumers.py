import json
import datetime

import pytz
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.authtoken.models import Token
from django.forms.models import model_to_dict
from django.db.models import Max

from plataforma.models import Silo, Sensor, SensorData  # Ajuste os imports conforme necessário


# Custom JSON encoder that handles datetime objects
class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)

class SiloConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        token_key = text_data_json.get('token')
        id_silo = text_data_json.get('id_silo')

        if token_key:
            user = await self.get_user_from_token(token_key)
            if user and user.is_authenticated:
                self.scope['user'] = user

                # Adicionar o usuário a um grupo específico do silo
                self.group_name = f"silo_{id_silo}"
                await self.channel_layer.group_add(
                    self.group_name,
                    self.channel_name
                )

                silo_data = await self.get_silo_data(id_silo)
                if silo_data:
                    await self.send(text_data=json.dumps({
                        'message': silo_data
                    }, cls=CustomJSONEncoder))  # Use the custom encoder
                else:
                    await self.close(code=4002)  # Silo não encontrado

            else:
                await self.close(code=4001)  # Token inválido ou usuário não autenticado
        else:
            await self.close(code=4000)  # Token não fornecido

    async def silo_update(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }, cls=CustomJSONEncoder))  # Use the custom encoder

    @sync_to_async
    def get_user_from_token(self, key):
        try:
            return Token.objects.get(key=key).user
        except Token.DoesNotExist:
            return AnonymousUser()

    @sync_to_async
    def get_silo_data(self, id_silo):
        try:
            # Buscar o silo pelo ID
            silo = Silo.objects.get(id_silo=id_silo)  # Certifique-se de que o campo ID está correto

            # Serializar o silo para incluir os dados dos sensores
            silo_data = model_to_dict(silo)

            # Adicionar os sensores ao dicionário
            sensors = Sensor.objects.filter(silo_id=id_silo)
            sensors_data = []
            for sensor in sensors:
                sensor_dict = model_to_dict(sensor)
                last_sensor_data = SensorData.objects.filter(sensor=sensor).aggregate(Max('time'))
                if last_sensor_data['time__max']:
                    last_data = SensorData.objects.get(sensor=sensor, time=last_sensor_data['time__max'])
                    sensor_dict['last_data'] = {
                        'valor': last_data.valor,
                        'time': last_data.time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    sensor_dict['last_data'] = None
                sensors_data.append(sensor_dict)

            silo_data['sensors'] = sensors_data

            return silo_data
        except Silo.DoesNotExist:
            return None


class AlertaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.temperatura_group_name = 'temperatura_notifications'

        # Adiciona o consumidor ao grupo
        await self.channel_layer.group_add(
            self.temperatura_group_name,
            self.channel_name
        )

        # Aceita a conexão WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        # Remove o consumidor do grupo
        await self.channel_layer.group_discard(
            self.temperatura_group_name,
            self.channel_name
        )

    async def temperatura_notification(self, event):
        titulo = event['titulo']
        descricao = event['descricao']
        time_isoformat = event['time']

        # Certifique-se de que a hora está no fuso horário correto
        time_corrected = time_isoformat.astimezone(pytz.timezone('America/Sao_Paulo'))

        # Convertendo a data para o formato ISO 8601
        time_iso = time_corrected.strftime('%Y-%m-%dT%H:%M:%S')

        # Envia a temperatura para o cliente
        await self.send(text_data=json.dumps({
            'type': 'temperatura_notification',
            'titulo': titulo,
            'descricao': descricao,
            'time': time_iso,
        }))
