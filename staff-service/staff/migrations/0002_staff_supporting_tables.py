from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, max_length=100)),
                ('bio', models.TextField(blank=True)),
                ('avatar_url', models.URLField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('staff', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile_detail', to='staff.staff')),
            ],
        ),
        migrations.CreateModel(
            name='StaffRoleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role_name', models.CharField(max_length=100)),
                ('scope', models.CharField(blank=True, max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_assignments', to='staff.staff')),
            ],
            options={
                'ordering': ['-assigned_at'],
            },
        ),
        migrations.CreateModel(
            name='StaffActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('target_type', models.CharField(blank=True, max_length=100)),
                ('target_id', models.CharField(blank=True, max_length=100)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_logs', to='staff.staff')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='staffroleassignment',
            constraint=models.UniqueConstraint(fields=('staff', 'role_name', 'scope'), name='unique_staff_role_scope'),
        ),
        migrations.AddIndex(
            model_name='staffactivitylog',
            index=models.Index(fields=['staff', 'action'], name='staff_staff_staff_i_ea8040_idx'),
        ),
        migrations.AddIndex(
            model_name='staffactivitylog',
            index=models.Index(fields=['created_at'], name='staff_staff_created_d6db2a_idx'),
        ),
    ]
