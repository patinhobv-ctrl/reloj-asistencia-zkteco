from datetime import date, datetime
from django.http import JsonResponse
from django.shortcuts import render
from .models import Empleado
from .services import resumen_diario


def inicio(request):
    return render(request, 'asistencias/inicio.html', {'empleados': Empleado.objects.filter(activo=True)})


def reporte(request):
    fecha_texto = request.GET.get('fecha', '')
    try:
        fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date() if fecha_texto else date.today()
    except ValueError:
        fecha = date.today()
    datos = [resumen_diario(empleado, fecha) for empleado in Empleado.objects.filter(activo=True)]
    return render(request, 'asistencias/reporte.html', {'fecha': fecha, 'datos': datos})


def reporte_json(request):
    fecha_texto = request.GET.get('fecha', '')
    try:
        fecha = datetime.strptime(fecha_texto, '%Y-%m-%d').date() if fecha_texto else date.today()
    except ValueError:
        fecha = date.today()
    datos = []
    for empleado in Empleado.objects.filter(activo=True):
        item = resumen_diario(empleado, fecha)
        datos.append({
            'id': empleado.pk,
            'nombre': empleado.nombre,
            'fecha': str(fecha),
            'entrada': item['entrada'].strftime('%H:%M') if item['entrada'] else None,
            'salida_almuerzo': item['salida_almuerzo'].strftime('%H:%M') if item['salida_almuerzo'] else None,
            'regreso_almuerzo': item['regreso_almuerzo'].strftime('%H:%M') if item['regreso_almuerzo'] else None,
            'salida': item['salida'].strftime('%H:%M') if item['salida'] else None,
            'hora_asignada': item['hora_asignada'].strftime('%H:%M') if item['hora_asignada'] else None,
            'minutos_atraso': item['minutos_atraso'],
            'estado': item['estado'],
        })
    return JsonResponse({'fecha': str(fecha), 'datos': datos})
