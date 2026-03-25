from django.urls import re_path

from plataforma import consumers

websocket_urlpatterns = [
    re_path(r'ws/alertas/$', consumers.AlertaConsumer.as_asgi()),
    re_path(r'ws/silos/$', consumers.SiloConsumer.as_asgi()),
]
