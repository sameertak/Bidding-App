# Generated by Django 5.0.6 on 2024-06-09 15:14

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination', models.CharField(max_length=255)),
                ('destination_lat', models.FloatField(blank=True, null=True)),
                ('destination_lng', models.FloatField(blank=True, null=True)),
                ('number_of_vehicles', models.IntegerField()),
                ('vehicle_requirements', models.JSONField()),
                ('size_requirements', models.JSONField()),
                ('weight_requirements', models.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
