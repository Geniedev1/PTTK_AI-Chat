from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shipments", "0002_shipment_supporting_tables"),
    ]

    operations = [
        migrations.AddField(
            model_name="shipment",
            name="accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="shipment",
            name="assigned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="shipment",
            name="assignment_source",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="shipment",
            name="delivery_lat",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="shipment",
            name="delivery_lng",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name="shipment",
            name="distance_km_snapshot",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name="shipment",
            name="shipper_id",
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.CreateModel(
            name="ShipperProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("staff_id", models.IntegerField(unique=True)),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("current_lat", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("current_lng", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("is_available", models.BooleanField(default=True)),
                ("last_location_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name", "staff_id"],
            },
        ),
        migrations.AddIndex(
            model_name="shipment",
            index=models.Index(fields=["shipper_id", "status"], name="shipments_s_shipper_2ceabd_idx"),
        ),
        migrations.AddIndex(
            model_name="shipperprofile",
            index=models.Index(fields=["is_available"], name="shipments_s_is_avai_0a5984_idx"),
        ),
        migrations.AddIndex(
            model_name="shipperprofile",
            index=models.Index(fields=["staff_id"], name="shipments_s_staff_i_124f76_idx"),
        ),
    ]
