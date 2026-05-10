from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('cart', '0004_add_price_snapshot'),
    ]

    operations = [
        migrations.CreateModel(
            name='CartSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('customer_id', models.IntegerField(blank=True, null=True)),
                ('item_count', models.PositiveIntegerField(default=0)),
                ('total_quantity', models.PositiveIntegerField(default=0)),
                ('subtotal_amount', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('snapshot', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CartEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(db_index=True, max_length=40)),
                ('customer_id', models.IntegerField(blank=True, null=True)),
                ('event_type', models.CharField(max_length=64)),
                ('product_id', models.IntegerField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='cartsnapshot',
            index=models.Index(fields=['session_key', 'created_at'], name='cart_carts_session_55131e_idx'),
        ),
        migrations.AddIndex(
            model_name='cartevent',
            index=models.Index(fields=['session_key', 'event_type'], name='cart_carte_session_12f37e_idx'),
        ),
        migrations.AddIndex(
            model_name='cartevent',
            index=models.Index(fields=['created_at'], name='cart_carte_created_7523e1_idx'),
        ),
    ]
