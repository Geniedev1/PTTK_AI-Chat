from django.db import models


class Cart(models.Model):
    customer_id = models.IntegerField(null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True, db_index=True)
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=1)
    price_snapshot = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['session_key', 'product_id'], name='unique_cart_session_product'),
        ]
    
    def __str__(self):
        return f"Cart - Session {self.session_key or 'legacy'} - product:{self.product_id}"

class CartSession(models.Model):
    """Track carts by session if needed"""
    session_key = models.CharField(max_length=40, unique=True)
    customer_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"CartSession - {self.customer_id or self.session_key}"
