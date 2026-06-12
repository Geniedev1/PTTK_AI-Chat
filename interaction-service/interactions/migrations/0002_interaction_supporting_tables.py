from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('interactions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BehaviorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('profile_json', models.JSONField(blank=True, default=dict)),
                ('event_count', models.PositiveIntegerField(default=0)),
                ('last_event_at', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='SearchQueryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('query_text', models.CharField(max_length=255)),
                ('result_count', models.PositiveIntegerField(default=0)),
                ('product_ids', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='EventAggregate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_name', models.CharField(max_length=100)),
                ('metric_date', models.DateField()),
                ('dimension', models.CharField(blank=True, max_length=100)),
                ('metric_value', models.IntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-metric_date', 'metric_name'],
            },
        ),
        migrations.AddIndex(
            model_name='behaviorprofile',
            index=models.Index(fields=['user_id', 'session_id'], name='interactio_user_id_8a4d5f_idx'),
        ),
        migrations.AddIndex(
            model_name='searchquerylog',
            index=models.Index(fields=['query_text'], name='interactio_query_t_d38f28_idx'),
        ),
        migrations.AddIndex(
            model_name='searchquerylog',
            index=models.Index(fields=['created_at'], name='interactio_created_0b4041_idx'),
        ),
        migrations.AddConstraint(
            model_name='eventaggregate',
            constraint=models.UniqueConstraint(fields=('metric_name', 'metric_date', 'dimension'), name='unique_event_aggregate_dimension'),
        ),
    ]
