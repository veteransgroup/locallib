# Generated by Django 2.2 on 2020-09-28 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0007_auto_20200927_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatar'),
        ),
    ]
