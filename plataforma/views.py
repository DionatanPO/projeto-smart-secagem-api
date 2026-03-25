from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout

from django.contrib.auth import views as auth_views

from plataforma.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, \
    UserPasswordChangeForm, SiloForm, SensorForm, ControladorForm, AeracaoSiloForm

from plataforma import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

from plataforma.models import Silo, Sensor, Controlador, AeracaoSilo, SensorData


# Create your views here.

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username_or_email = request.data.get('username_or_email')
        password = request.data.get('password')

        # Primeiro, tenta autenticar com o email
        user = authenticate(email=username_or_email, password=password)
        if user is None:
            # Se não for bem-sucedido, tenta autenticar com o nome de usuário
            user = authenticate(username=username_or_email, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'name': user.username  # Adiciona o nome do usuário à resposta
            })
        else:
            return Response({'error': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)


# Authentication
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            print('Account created successfully!')
            return redirect('/accounts/login/')
        else:
            print("Registration failed!")
    else:
        form = RegistrationForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


class UserLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm
    success_url = '/'


class UserPasswordResetView(auth_views.PasswordResetView):
    template_name = 'accounts/forgot-password.html'
    form_class = UserPasswordResetForm


class UserPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/recover-password.html'
    form_class = UserSetPasswordForm


class UserPasswordChangeView(auth_views.PasswordChangeView):
    template_name = 'accounts/password_change.html'
    form_class = UserPasswordChangeForm


def user_logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


# pages
def index(request):
    context = {
        'parent': 'index',
        'segment': 'index'
    }
    return render(request, 'index.html', context)


def dashboard(request):
    # Obtém o usuário autenticado
    user = request.user
    # Obtém o token do usuário autenticado
    if request.user.is_authenticated:
        # Obtém o token de autenticação do usuário autenticado
        token, created = Token.objects.get_or_create(user=request.user)
        print(token)

    # silos = models.Silo.objects.filter(user=user)
    try:
        silo = models.Silo.objects.get(id_silo=1)
    except models.Silo.DoesNotExist:
        silo = None

    # Verifica se há silos associados ao usuário
    if silo is not None:

        # Lógica para obter os sensores do silo e o último SensorData de cada um
        sensores_silo = Sensor.objects.filter(silo=silo)
        dados_sensores = []

        for sensor in sensores_silo:
            ultimo_dado_sensor = SensorData.objects.filter(sensor_id=sensor.id_sensor).order_by('-time').first()

            if ultimo_dado_sensor is not None:
                dados_sensores.append({
                    'sensor': sensor,
                    'ultimo_dado': ultimo_dado_sensor
                })

        controladores = Controlador.objects.filter(silo_id=silo.id_silo).all()

        context = {
            'parent': 'dashboard',
            'segment': 'dashboard',
            'silo': silo,
            'token': token,
            'dados_sensores': dados_sensores,
            'controladores': controladores
        }

        return render(request, 'pages/dashboard.html', context)

    else:
        context = {
            'parent': 'dashboard',
            'segment': 'dashboard',
        }
        return render(request, 'pages/dashboard.html', context)


def silos(request):
    user = request.user

    # Filtra os silos com base no usuário autenticado
    silos = models.Silo.objects.filter(user=user)
    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silos': silos
    }
    return render(request, 'pages/silos/silos.html', context)


def cadastrar_silo(request):
    context = {
        'parent': 'silo',
        'segment': 'silos'
    }
    return render(request, 'pages/silos/cadastrar_silo.html', context)


def form_cadastrar_silo(request):
    user = request.user
    if request.method == 'POST':

        form = SiloForm(request.POST)
        if form.is_valid():
            # Crie um objeto Motorista com os dados do formulário
            silo = Silo(
                user=user,
                identificacao=form.cleaned_data['identificacao'],
                observacao=form.cleaned_data['observacao'],
                status=form.cleaned_data['status']
            )
            silo.save()

            return redirect('silos')
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível cadastrar o silo! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('silos')


def editar_silo(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silo': silo
    }
    return render(request, 'pages/silos/editar_silo.html', context)


def form_editar_silo(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    if request.method == 'POST':
        form = SiloForm(request.POST)
        if form.is_valid():
            if silo:
                silo.identificacao = form.cleaned_data['identificacao']
                silo.observacao = form.cleaned_data['observacao']
                silo.status = form.cleaned_data['status']
                silo.save()

            return redirect('silos')
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível alterar os dados do silo! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('editar_silo', id_silo)


def sensor_data(request, id_sensor):
    sensor = models.Sensor.objects.get(id_sensor=id_sensor)
    parametros = models.SensorData.objects.filter(sensor_id=id_sensor).order_by('id_sensor_data').all()

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'sensor': sensor,
        'parametros': parametros
    }
    return render(request, 'pages/sensores/sensor_data.html', context)


def sensores(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    # Altere esta linha para incluir a ordenação por tempo (time) decrescente
    sensores = models.Sensor.objects.filter(silo_id=id_silo).order_by('-time').all()

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silo': silo,
        'sensores': sensores
    }
    return render(request, 'pages/sensores/sensores.html', context)


def cadastrar_sensor(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silo': silo
    }
    return render(request, 'pages/sensores/cadastrar_sensor.html', context)


def form_cadastrar_sensor(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    if request.method == 'POST':

        form = SensorForm(request.POST)
        if form.is_valid():
            unidade = ""
            tipo_sensor = form.cleaned_data['tipo']

            if tipo_sensor == "Temperatura":
                unidade = '°C'
            elif tipo_sensor == "Pressão":
                unidade = 'PSI'  # Unidade para pressão
            elif tipo_sensor == "Umidade":
                unidade = '%'  # Unidade para umidade

            sensor = Sensor(
                silo=silo,
                nome=form.cleaned_data['nome'],
                tipo=form.cleaned_data['tipo'],
                unidade=unidade,
                observacao=form.cleaned_data['observacao'],
                status=form.cleaned_data['status']
            )
            sensor.save()

            return redirect('sensores', id_silo)
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível cadastrar o sensor! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('sensores', id_silo)


def editar_sensor(request, id_sensor):
    sensor = models.Sensor.objects.get(id_sensor=id_sensor)

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'sensor': sensor
    }
    return render(request, 'pages/sensores/editar_sensor.html', context)


def form_editar_sensor(request, id_sensor):
    sensor = models.Sensor.objects.get(id_sensor=id_sensor)
    if request.method == 'POST':
        form = SensorForm(request.POST)
        if form.is_valid():
            unidade = ""
            tipo_sensor = form.cleaned_data['tipo']

            if tipo_sensor == "Temperatura":
                unidade = '°C'
            elif tipo_sensor == "Pressão":
                unidade = 'PSI'  # Unidade para pressão
            elif tipo_sensor == "Umidade":
                unidade = '%'  # Unidade para umidade

            if sensor:
                sensor.nome = form.cleaned_data['nome']
                sensor.tipo = form.cleaned_data['tipo']
                sensor.unidade = unidade
                sensor.observacao = form.cleaned_data['observacao']
                sensor.status = form.cleaned_data['status']
                sensor.save()

            return redirect('sensores', sensor.silo_id)
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível alterar os dados do sensor! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('editar_sensor', id_sensor)


# Controladores----------------------------------------------
def controladores(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    controladores = models.Controlador.objects.filter(silo_id=id_silo).all()

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silo': silo,
        'controladores': controladores
    }
    return render(request, 'pages/controladores/controladores.html', context)


def cadastrar_controlador(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    context = {
        'parent': 'silo',
        'segment': 'silos',
        'silo': silo
    }
    return render(request, 'pages/controladores/cadastrar_controlador.html', context)


def form_cadastrar_controlador(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    if request.method == 'POST':

        form = ControladorForm(request.POST)
        if form.is_valid():
            controlador = Controlador(
                silo=silo,
                nome=form.cleaned_data['nome'],
                tipo=form.cleaned_data['tipo'],
                observacao=form.cleaned_data['observacao'],
                status=form.cleaned_data['status']
            )
            controlador.save()

            return redirect('controladores', id_silo)
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível cadastrar o controlador! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('controladores', id_silo)


def editar_controlador(request, id_controlador):
    controlador = models.Controlador.objects.get(id_controlador=id_controlador)

    context = {
        'parent': 'silo',
        'segment': 'silos',
        'controlador': controlador
    }
    return render(request, 'pages/controladores/editar_controlador.html', context)


def form_editar_controlador(request, id_controlador):
    controlador = models.Controlador.objects.get(id_controlador=id_controlador)
    if request.method == 'POST':
        form = ControladorForm(request.POST)
        if form.is_valid():
            if controlador:
                controlador.nome = form.cleaned_data['nome']
                controlador.tipo = form.cleaned_data['tipo']
                controlador.observacao = form.cleaned_data['observacao']
                controlador.status = form.cleaned_data['status']
                controlador.save()

            return redirect('controladores', controlador.silo_id)
        else:
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível alterar os dados do controlador! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('editar_controlador', id_controlador)


def atividades(request):
    context = {
        'parent': 'silo',
        'segment': 'atividades'
    }
    return render(request, 'pages/silos/atividades.html', context)


def parametros(request, silo_id):
    silo = models.Silo.objects.get(id_silo=silo_id)
    parametros = models.SiloParametros.objects.filter(silo_id=silo_id).order_by('-time')

    context = {
        'parent': 'silo',
        'segment': 'parametros',
        'silo': silo,
        'parametros': parametros
    }
    return render(request, 'pages/silos/parametros.html', context)


def gerenciar(request, silo_id):
    silo = models.Silo.objects.get(id_silo=silo_id)
    parametros = models.SiloParametros.objects.filter(silo_id=silo_id).last()

    context = {
        'parent': 'silo',
        'segment': 'gerenciar',
        'silo': silo,
        'parametros': parametros
    }
    return render(request, 'pages/silos/gerenciar.html', context)


def aeracao(request, id_silo):
    # Verifica se o Silo existe
    silo = models.Silo.objects.get(id_silo=id_silo)

    # Tenta recuperar o objeto AeracaoSilo associado ao Silo
    aeracao = AeracaoSilo.objects.filter(silo_id=id_silo).first()

    # Verifica se o objeto AeracaoSilo foi encontrado
    if aeracao:
        print(aeracao.temperatura_desejada)
        context = {
            'parent': 'silo',
            'segment': 'silos',
            'silo': silo,
            'aeracao': aeracao
        }
    else:
        print("Nenhuma aeracao encontrada para este silo.")
        context = {
            'parent': 'silo',
            'segment': 'silos',
            'silo': silo
        }

    return render(request, 'pages/silos/aeracao/aeracao.html', context)


def form_aeracao(request, id_silo):
    silo = models.Silo.objects.get(id_silo=id_silo)
    aeracao = models.AeracaoSilo.objects.filter(silo_id=id_silo).last()
    if request.method == 'POST':
        form = AeracaoSiloForm(request.POST)
        if form.is_valid():
            if aeracao:
                aeracao.temperatura_desejada = form.cleaned_data['temperatura_desejada']
                aeracao.save()
                print("sasdfsdaf")
            else:
                print("kkkkkk")
                aeracao = AeracaoSilo(
                    silo=silo,
                    temperatura_desejada=form.cleaned_data['temperatura_desejada'],
                )
                aeracao.save()

            return redirect('aeracao', id_silo)
        else:
            print("ooo")
            return HttpResponse(f"""
                   <script>
                       alert("Não foi possível inserir os dados! Verifique se todos os campos foram preenchidos");
                       history.back()
                   </script>
               """)
    else:
        return redirect('form_aeracao', silo.id_silo)


def alertas(request):
    user = request.user  # Filtra os silos com base no usuário autenticado
    silos = models.Silo.objects.filter(user=user)

    # Obtém os IDs dos silos filtrados
    silo_ids = silos.values_list('id_silo', flat=True)

    # Filtra os alertas com base nos IDs dos silos e trazendo informações do silo e do sensor
    alertas = models.Alerta.objects.filter(silo_id__in=silo_ids).select_related('silo', 'sensor')

    context = {
        'parent': 'alerta',
        'segment': 'alertas',
        'alertas': alertas,
    }
    return render(request, 'pages/alertas/alertas.html', context)
