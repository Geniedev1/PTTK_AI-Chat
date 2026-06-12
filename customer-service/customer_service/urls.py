from django.urls import path, include

urlpatterns = [
    path('api/customers/', include('customer.urls')),
]
