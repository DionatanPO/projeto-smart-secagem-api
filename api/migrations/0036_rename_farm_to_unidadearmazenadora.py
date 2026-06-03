import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0035_cliente_farm_alter_user_account_type'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Farm',
            new_name='UnidadeArmazenadora',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.RenameField(
            model_name='sensordata',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.RenameField(
            model_name='silo',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.RenameField(
            model_name='lote',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.RenameField(
            model_name='secador',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.RenameField(
            model_name='cliente',
            old_name='farm',
            new_name='unidade_armazenadora',
        ),
        migrations.AlterModelOptions(
            name='unidadearmazenadora',
            options={'ordering': ['name'], 'verbose_name': 'Unidade Armazenadora', 'verbose_name_plural': 'Unidades Armazenadoras'},
        ),
        migrations.AlterField(
            model_name='unidadearmazenadora',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unidades_armazenadoras', to='api.user', verbose_name='Dono/Usuário'),
        ),
        migrations.AlterField(
            model_name='unidadearmazenadora',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Nome da Unidade Armazenadora'),
        ),
        migrations.AlterField(
            model_name='user',
            name='unidade_armazenadora',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='operadores', to='api.unidadearmazenadora', verbose_name='Unidade Armazenadora Vinculada'),
        ),
        migrations.AlterField(
            model_name='sensordata',
            name='unidade_armazenadora',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sensors', to='api.unidadearmazenadora'),
        ),
        migrations.AlterField(
            model_name='silo',
            name='unidade_armazenadora',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='silos', to='api.unidadearmazenadora', verbose_name='Unidade Armazenadora'),
        ),
        migrations.AlterField(
            model_name='lote',
            name='unidade_armazenadora',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lotes', to='api.unidadearmazenadora', verbose_name='Unidade Armazenadora'),
        ),
        migrations.AlterField(
            model_name='secador',
            name='unidade_armazenadora',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='secadores', to='api.unidadearmazenadora', verbose_name='Unidade Armazenadora'),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='unidade_armazenadora',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clientes', to='api.unidadearmazenadora', verbose_name='Unidade Armazenadora'),
        ),
    ]
