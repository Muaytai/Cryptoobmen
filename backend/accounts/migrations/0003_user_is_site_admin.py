# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_remove_user_has_2fa'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_site_admin',
            field=models.BooleanField(
                default=False,
                help_text='Designates this user as a site administrator who can manage the platform.',
                verbose_name='Site Administrator'
            ),
        ),
    ]
