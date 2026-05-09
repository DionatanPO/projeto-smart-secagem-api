import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Adicionar o diretório raiz ao path para encontrar o módulo 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import SensorData, Telemetry

def populate():
    sensor = SensorData.objects.first()
    if not sensor:
        print("Nenhum sensor encontrado para associar a telemetria.")
        return

    print(f"Gerando dados para o Sensor: {sensor.sensor_id}")
    
    # Gerar 10 pontos de telemetria (uma a cada hora retroativa)
    agora = timezone.now()
    
    telemetrias = []
    for i in range(10):
        timestamp = agora - timedelta(hours=i)
        
        # Simular dados normais com pequena variação
        temp = round(random.uniform(24.5, 28.2), 1)
        umid = round(random.uniform(12.8, 14.5), 1)
        
        t = Telemetry(
            sensor=sensor,
            temperatura=temp,
            umidade=umid,
            timestamp=timestamp
        )
        telemetrias.append(t)
    
    Telemetry.objects.bulk_create(telemetrias)
    print(f"Sucesso! {len(telemetrias)} registros de telemetria criados.")

if __name__ == '__main__':
    populate()
