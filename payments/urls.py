from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('invoices/', views.UserInvoicesListView.as_view(), name='invoices'),
]
