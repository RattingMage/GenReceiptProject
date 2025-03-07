from django.urls import path
from .views import generate_receipt

urlpatterns = [
    path('cash_machine/', generate_receipt, name='generate_receipt'),
]