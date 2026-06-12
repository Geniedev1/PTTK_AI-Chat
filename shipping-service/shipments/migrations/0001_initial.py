from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Shipment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.IntegerField(unique=True)),
                ("customer_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=40, null=True)),
                ("recipient_name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=32)),
                ("address", models.TextField()),
                ("city", models.CharField(blank=True, max_length=100)),
                ("country", models.CharField(blank=True, max_length=100)),
                ("carrier", models.CharField(default="mock", max_length=64)),
                ("tracking_number", models.CharField(blank=True, db_index=True, max_length=64)),
                ("shipping_fee", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("READY_TO_SHIP", "Ready to ship"),
                            ("SHIPPED", "Shipped"),
                            ("DELIVERED", "Delivered"),
                            ("FAILED", "Failed"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("failure_reason", models.TextField(blank=True)),
                ("shipped_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="shipment",
            index=models.Index(fields=["customer_id", "status"], name="shipments_s_custome_01dbec_idx"),
        ),
        migrations.AddIndex(
            model_name="shipment",
            index=models.Index(fields=["session_key", "status"], name="shipments_s_session_1f43fb_idx"),
        ),
    ]
