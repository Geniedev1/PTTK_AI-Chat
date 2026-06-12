from django.urls import path, include

urlpatterns = [
    path('api/staff/', include('staff.urls')),
]
