from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order_id", models.IntegerField(db_index=True)),
                ("customer_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("session_key", models.CharField(blank=True, db_index=True, max_length=40, null=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("provider", models.CharField(default="mock", max_length=32)),
                ("provider_reference", models.CharField(blank=True, max_length=128)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("PROCESSING", "Processing"),
                            ("PAID", "Paid"),
                            ("FAILED", "Failed"),
                            ("CANCELLED", "Cancelled"),
                            ("REFUNDED", "Refunded"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("failure_reason", models.TextField(blank=True)),
                ("idempotency_key", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("failed_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("refunded_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["order_id", "status"], name="payments_pa_order_i_b1da04_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["customer_id", "status"], name="payments_pa_custome_404c93_idx"),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["session_key", "status"], name="payments_pa_session_26309c_idx"),
        ),
    ]
