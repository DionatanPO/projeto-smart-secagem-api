import os
import django
import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Telemetry, SensorData
from api.serializers import TelemetrySerializer
from django.conf import settings

print(f"DEBUG: settings.USE_TZ={settings.USE_TZ}")
print(f"DEBUG: settings.TIME_ZONE={settings.TIME_ZONE}")

sensor, _ = SensorData.objects.get_or_create(sensor_id="test_sensor_01", defaults={"description": "Test Sensor"})

# Simulating data arriving from the device
# Let's say the device sends "2026-03-18T17:08:02" (no TZ)
input_time_str = "2026-03-18T17:08:02"

tel = Telemetry.objects.create(
    sensor=sensor,
    temperatura=25.0,
    umidade=50.0,
    timestamp=timezone.make_aware(datetime.datetime.strptime(input_time_str, "%Y-%m-%dT%H:%M:%S"))
)

print(f"Saved Telemetry timestamp (field value): {tel.timestamp}")

# Serialization
serializer = TelemetrySerializer(tel)
print(f"Serialized Data (what API sends back): {serializer.data['timestamp']}")
print(f"Serialized Data (received_at): {serializer.data['received_at']}")

tel.delete()
