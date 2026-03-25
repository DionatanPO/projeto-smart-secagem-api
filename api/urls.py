from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import SensorDataViewSet, UserViewSet, logout_view, SiloViewSet, TelemetryViewSet

router = DefaultRouter()
router.register(r'sensores', SensorDataViewSet)
router.register(r'usuarios', UserViewSet)
router.register(r'silos', SiloViewSet)
router.register(r'telemetria', TelemetryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', obtain_auth_token, name='api_token_auth'),
    path('logout/', logout_view, name='api_logout'),
]
