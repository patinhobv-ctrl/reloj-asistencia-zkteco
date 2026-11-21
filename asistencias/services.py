from datetime import datetime, timedelta
from .models import Empleado, Horario, HorarioDia, Marcacion


def horario_para(empleado, fecha):
    """Devuelve el horario específico de la fecha o el horario base."""
    especifico = HorarioDia.objects.filter(empleado=empleado, fecha=fecha).first()
    if especifico:
        return especifico
    return empleado.horario


def minutos_desde_medianoche(hora):
    return hora.hour * 60 + hora.minute


def calcular_atraso(entrada, hora_asignada, tolerancia=0):
    if not entrada or not hora_asignada:
        return 0
    diferencia = minutos_desde_medianoche(entrada) - minutos_desde_medianoche(hora_asignada)
    return max(0, diferencia - int(tolerancia or 0))


def clasificar_marcaciones(empleado, fecha):
    """Ordena las marcas del día y las asigna a entrada, almuerzo y salida."""
    marcas = list(Marcacion.objects.filter(empleado=empleado, fecha=fecha).order_by('hora'))
    resultado = {
        'entrada': marcas[0].hora if marcas else None,
        'salida_almuerzo': None,
        'regreso_almuerzo': None,
        'salida': marcas[-1].hora if len(marcas) >= 2 else None,
        'marcaciones': marcas,
    }
    if len(marcas) >= 4:
        resultado['salida_almuerzo'] = marcas[1].hora
        resultado['regreso_almuerzo'] = marcas[-2].hora
    return resultado


def resumen_diario(empleado, fecha):
    horario = horario_para(empleado, fecha)
    marcas = clasificar_marcaciones(empleado, fecha)
    libre = getattr(horario, 'libre', False)
    hora_entrada = getattr(horario, 'hora_entrada', None)
    tolerancia = getattr(horario, 'tolerancia_min', 0)
    atraso = 0 if libre else calcular_atraso(marcas['entrada'], hora_entrada, tolerancia)
    return {
        'empleado': empleado,
        'fecha': fecha,
        'entrada': marcas['entrada'],
        'salida_almuerzo': marcas['salida_almuerzo'],
        'regreso_almuerzo': marcas['regreso_almuerzo'],
        'salida': marcas['salida'],
        'hora_asignada': hora_entrada,
        'minutos_atraso': atraso,
        'estado': 'DIA_LIBRE' if libre else ('PRESENTE' if marcas['entrada'] else 'SIN_MARCACION'),
    }
