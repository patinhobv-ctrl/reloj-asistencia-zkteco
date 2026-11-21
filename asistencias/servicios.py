"""Compatibilidad con el nombre original del proyecto.

La lógica principal está en services.py. Este módulo la reexporta para
mantener compatibles las importaciones existentes que usan servicios.py.
"""
from .services import (
    calcular_atraso,
    clasificar_marcaciones,
    horario_para,
    minutos_desde_medianoche,
    resumen_diario,
)

__all__ = [
    'calcular_atraso',
    'clasificar_marcaciones',
    'horario_para',
    'minutos_desde_medianoche',
    'resumen_diario',
]
