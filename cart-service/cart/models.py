from django.db import models

class Cart(models.Model):
    customer_id = models.IntegerField()
    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['customer_id', 'product_id']
    
    def __str__(self):
        return f"Cart - Customer {self.customer_id} - product:{self.product_id}"

class CartSession(models.Model):
    """Track carts by session if needed"""
    session_key = models.CharField(max_length=40, unique=True)
    customer_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"CartSession - {self.customer_id or self.session_key}"
