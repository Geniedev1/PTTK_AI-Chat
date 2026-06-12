from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='RecommendationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('strategy', models.CharField(max_length=64)),
                ('context', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(blank=True, db_index=True, null=True)),
                ('session_id', models.CharField(blank=True, db_index=True, max_length=64, null=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('last_message_at', models.DateTimeField(auto_now=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'ordering': ['-last_message_at'],
            },
        ),
        migrations.CreateModel(
            name='RecommendationResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.IntegerField(db_index=True)),
                ('score', models.FloatField(default=0)),
                ('deep_model_score', models.FloatField(blank=True, null=True)),
                ('reason_codes', models.JSONField(blank=True, default=list)),
                ('source_signals', models.JSONField(blank=True, default=dict)),
                ('rank_position', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='recommendations.recommendationrequest')),
            ],
            options={
                'ordering': ['rank_position', '-score'],
            },
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant')], max_length=20)),
                ('message', models.TextField()),
                ('retrieval_mode', models.CharField(blank=True, max_length=64)),
                ('sources', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chat_session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='recommendations.chatsession')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='recommendationrequest',
            index=models.Index(fields=['strategy', 'created_at'], name='recommendat_strategy_e3415a_idx'),
        ),
        migrations.AddIndex(
            model_name='recommendationresult',
            index=models.Index(fields=['product_id', 'score'], name='recommendat_product_b4762a_idx'),
        ),
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['user_id', 'session_id'], name='recommendat_user_id_013c44_idx'),
        ),
    ]
