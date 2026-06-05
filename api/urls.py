from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import SensorDataViewSet, UserViewSet, logout_view, me_view, SiloViewSet, TelemetryViewSet, UnidadeArmazenadoraViewSet, LoteViewSet, SecadorViewSet, ProcessoViewSet, ClienteViewSet, chat_view, custos_secagem_view

router = DefaultRouter()
router.register(r'sensores', SensorDataViewSet)
router.register(r'usuarios', UserViewSet)
router.register(r'silos', SiloViewSet)
router.register(r'unidades-armazenadoras', UnidadeArmazenadoraViewSet, basename='unidade-armazenadora')
router.register(r'telemetria', TelemetryViewSet)
router.register(r'lotes', LoteViewSet)
router.register(r'secadores', SecadorViewSet, basename='secador')
router.register(r'processos', ProcessoViewSet, basename='processo')
router.register(r'clientes', ClienteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', obtain_auth_token, name='api_token_auth'),
    path('logout/', logout_view, name='api_logout'),
    path('custos/secagem/', custos_secagem_view, name='custos_secagem'),
    path('chat/', chat_view, name='chat'),
    path('chat-stream/', chat_view, name='chat-stream'),
    path('me/', me_view, name='me'),
]
