from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('reporte/', views.reporte, name='reporte'),
    path('api/reporte/', views.reporte_json, name='reporte_json'),
]
