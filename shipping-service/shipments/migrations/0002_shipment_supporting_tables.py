from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('shipments', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShipmentAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient_name', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=32)),
                ('address', models.TextField()),
                ('city', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('shipment', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='delivery_address', to='shipments.shipment')),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentTrackingEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('event_time', models.DateTimeField(auto_now_add=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('shipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracking_events', to='shipments.shipment')),
            ],
            options={
                'ordering': ['-event_time'],
            },
        ),
        migrations.CreateModel(
            name='ShippingRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carrier', models.CharField(max_length=64)),
                ('city', models.CharField(blank=True, max_length=100)),
                ('country', models.CharField(blank=True, max_length=100)),
                ('base_fee', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('estimated_days_min', models.PositiveIntegerField(default=1)),
                ('estimated_days_max', models.PositiveIntegerField(default=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['carrier', 'country', 'city'],
            },
        ),
        migrations.AddIndex(
            model_name='shipmenttrackingevent',
            index=models.Index(fields=['shipment', 'status'], name='shipments_s_shipment_7a6922_idx'),
        ),
        migrations.AddIndex(
            model_name='shipmenttrackingevent',
            index=models.Index(fields=['event_time'], name='shipments_s_event_t_4a494c_idx'),
        ),
        migrations.AddIndex(
            model_name='shippingrate',
            index=models.Index(fields=['carrier', 'country', 'city'], name='shipments_s_carrier_74555b_idx'),
        ),
    ]
