from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0031_alter_secador_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='telefone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone'),
        ),
    ]
