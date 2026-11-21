# Sistema de asistencia ZKTeco

Repositorio temporal para revisar y mejorar el sistema de asistencia basado en Django.

Objetivos de la mejora:

- Horarios editables por empleado y por fecha.
- Jornada con entrada, salida a almuerzo, regreso y salida final.
- Cálculo de minutos de atraso con tolerancia configurable.
- Estados: ausencia, día libre, reposo y vacaciones.
- Reporte diario y mensual.

No se incluyen bases de datos, credenciales, archivos `.env` ni datos personales.

Estado actual: se agregó el modelo base compartido por el cliente. Falta incorporar el resto del proyecto, especialmente servicios, vistas, plantillas, configuración y migraciones, antes de desplegarlo en producción o en el subdominio temporal.
