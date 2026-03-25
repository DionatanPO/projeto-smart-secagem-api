import os
import django
import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Telemetry, SensorData
from api.serializers import TelemetrySerializer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

# Factory to simulate DRF request
factory = APIRequestFactory()
request = factory.post('/api/telemetry/')

sensor, _ = SensorData.objects.get_or_create(sensor_id="test_sensor_01", defaults={"description": "Test Sensor"})

# Simulating data arriving from the device as a string
input_data = {
    "sensor": sensor.id,
    "temperatura": 25.0,
    "umidade": 50.0,
    "timestamp": "2026-03-18T17:00:00" # Naive string
}

serializer = TelemetrySerializer(data=input_data)
if serializer.is_valid():
    tel = serializer.save()
    print(f"Input string: {input_data['timestamp']}")
    print(f"Saved tel.timestamp: {tel.timestamp}")
    print(f"Serialized tel.timestamp: {serializer.data['timestamp']}")
    
    # Let's try with 'Z' suffix (UTC)
    input_data_utc = input_data.copy()
    input_data_utc["timestamp"] = "2026-03-18T17:00:00Z"
    serializer_utc = TelemetrySerializer(data=input_data_utc)
    if serializer_utc.is_valid():
        tel_utc = serializer_utc.save()
        print(f"\nInput string (UTC): {input_data_utc['timestamp']}")
        print(f"Saved tel_utc.timestamp: {tel_utc.timestamp}")
        print(f"Serialized tel_utc.timestamp: {serializer_utc.data['timestamp']}")
        tel_utc.delete()
    
    tel.delete()
else:
    print(f"Errors: {serializer.errors}")
