from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0002_order_lifecycle_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderStatusHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(blank=True, max_length=20)),
                ('new_status', models.CharField(max_length=20)),
                ('changed_by', models.CharField(default='system', max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_history', to='orders.order')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OrderNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('created_by', models.CharField(default='system', max_length=100)),
                ('is_internal', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='orders.order')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='orderstatushistory',
            index=models.Index(fields=['order', 'new_status'], name='orders_orde_order_i_0db477_idx'),
        ),
        migrations.AddIndex(
            model_name='orderstatushistory',
            index=models.Index(fields=['created_at'], name='orders_orde_created_e22cbf_idx'),
        ),
    ]
