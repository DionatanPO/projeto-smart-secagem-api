import os
import django
import datetime
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import Telemetry, SensorData

# Get current time in defined timezone
now = timezone.now()
local_now = timezone.localtime(now)

print(f"Timezone setting: {os.getenv('TIME_ZONE')}")
print(f"Current UTC time (timezone.now()): {now}")
print(f"Current Local time (timezone.localtime()): {local_now}")

# Let's see what happens if we create a record
# First ensure we have a sensor
sensor, created = SensorData.objects.get_or_create(sensor_id="test_sensor_01", defaults={"description": "Test Sensor"})

tel = Telemetry.objects.create(
    sensor=sensor,
    temperatura=25.0,
    umidade=50.0,
    timestamp=now
)

print(f"Saved Telemetry timestamp: {tel.timestamp}")
print(f"Saved Telemetry received_at: {tel.received_at}")

# Read it back
tel_read = Telemetry.objects.get(id=tel.id)
print(f"Read Telemetry timestamp: {tel_read.timestamp}")
print(f"Read Telemetry timestamp (local): {timezone.localtime(tel_read.timestamp)}")

# Clean up
tel.delete()
if created:
    sensor.delete()
