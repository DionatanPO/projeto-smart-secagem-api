from django.db import migrations


def fix_operador_is_staff(apps, schema_editor):
    User = apps.get_model('api', 'User')
    User.objects.filter(account_type='operador').update(is_staff=False, is_superuser=False)
    User.objects.filter(account_type='visualizador').update(is_staff=False, is_superuser=False)
    User.objects.filter(account_type='admin').update(is_staff=True, is_superuser=False)
    User.objects.filter(account_type='super_admin').update(is_staff=True, is_superuser=True)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_alter_cliente_unidade_armazenadora_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_operador_is_staff, reverse_code=migrations.RunPython.noop),
    ]
