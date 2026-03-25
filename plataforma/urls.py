from django.contrib.auth.decorators import login_required
from django.urls import path, include

from django.contrib.auth import views as auth_views
from . import views


from rest_framework import routers

from plataforma.api.viewsets import AlertaViewSet, SilosViewSet, SensoresViewSet, \
    SensorDataViewSet, ControladoresViewSet

from .views import LogoutView

router = routers.DefaultRouter()

router.register(r'silos',SilosViewSet, basename="Silos")
router.register(r'sensores', SensoresViewSet, basename="Sensores")
router.register(r'controladores', ControladoresViewSet, basename="Controladores")
router.register(r'sensordata', SensorDataViewSet, basename="SensorData")
router.register(r'alertas', AlertaViewSet, basename="Alertas")

urlpatterns = [

    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('api/', include(router.urls)),
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # # Para obter um par de tokens (acesso e atualização)
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Para atualizar o token de acesso

    path('', views.index),
    path('dashboard/', login_required(views.dashboard), name='dashboard'),
    path('silos/', login_required(views.silos), name='silos'),
    path('silo/cadastrar/', login_required(views.cadastrar_silo), name='cadastrar_silo'),
    path('silo/cadastrar/form_cadastrar_silo', login_required(views.form_cadastrar_silo), name='form_cadastrar_silo'),
    path('silo/editar/<int:id_silo>/', login_required(views.editar_silo), name='editar_silo'),
    path('silo/form_editar/<int:id_silo>/', login_required(views.form_editar_silo), name='form_editar_silo'),

    path('silo/sensores/<int:id_silo>/', login_required(views.sensores), name='sensores'),
    path('silo/sensores/sensor_data/<int:id_sensor>/', login_required(views.sensor_data), name='sensor_data'),
    path('silo/sensores/cadastrar/<int:id_silo>/', login_required(views.cadastrar_sensor), name='cadastrar_sensor'),
    path('silo/sensores/cadastrar/form_cadastrar_sensor/<int:id_silo>/', login_required(views.form_cadastrar_sensor),
         name='form_cadastrar_sensor'),
    path('silo/sesnor/editar/<int:id_sensor>/', login_required(views.editar_sensor), name='editar_sensor'),
    path('silo/sensor/form_editar/<int:id_sensor>/', login_required(views.form_editar_sensor),
         name='form_editar_sensor'),

    path('silo/controladores/<int:id_silo>/', login_required(views.controladores), name='controladores'),
    path('silo/controladores/cadastrar/<int:id_silo>/', login_required(views.cadastrar_controlador),
         name='cadastrar_controlador'),
    path('silo/controladores/cadastrar/form_cadastrar_controlador/<int:id_silo>/',
         login_required(views.form_cadastrar_controlador),
         name='form_cadastrar_controlador'),
    path('silo/controlador/editar/<int:id_controlador>/', login_required(views.editar_controlador),
         name='editar_controlador'),
    path('silo/controlador/form_editar/<int:id_controlador>/', login_required(views.form_editar_controlador),
         name='form_editar_controlador'),

    path('silo/aeracao/<int:id_silo>/', login_required( views.aeracao), name='aeracao'),
    path('silo/form_aeracao/<int:id_silo>/', login_required(views.form_aeracao), name='form_aeracao'),
    path('alertas/', login_required(views.alertas), name='alertas'),


    path('silos/gerenciar/<int:silo_id>', views.gerenciar, name='gerenciar'),
    path('atividades/', views.atividades, name='atividades'),
    path('parametros/<int:silo_id>', views.parametros, name='parametros'),

    # Authentication
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', views.UserLoginView.as_view(), name='login'),
    path('accounts/logout/', views.user_logout_view, name='logout'),
    path('accounts/password-change/', views.UserPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name="password_change_done"),
    path('accounts/password-reset/', views.UserPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         views.UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password-reset-done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]
