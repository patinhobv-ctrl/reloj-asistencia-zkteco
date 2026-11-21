import datetime
from functools import cached_property

from django.db import models
from django.db.models import Q


def hora_entrada_default():
    return datetime.time(8, 0)


def hora_salida_default():
    return datetime.time(17, 0)


class Importacion(models.Model):
    ESTADOS = [
        ('OK', 'Procesado'),
        ('ERROR', 'Con error'),
        ('ANULADA', 'Anulada'),
    ]

    archivo = models.CharField('archivo', max_length=255)
    fecha = models.DateTimeField('fecha de proceso', auto_now_add=True)
    estado = models.CharField('estado', max_length=10, choices=ESTADOS, default='OK')
    filas = models.PositiveIntegerField('filas leidas', default=0)
    marcas_creadas = models.PositiveIntegerField('marcas creadas', default=0)
    marcas_duplicadas = models.PositiveIntegerField('marcas duplicadas', default=0)
    omitidas = models.PositiveIntegerField('marcas omitidas', default=0)
    sin_hora = models.PositiveIntegerField('filas sin hora', default=0)
    empleados_nuevos = models.PositiveIntegerField('empleados nuevos', default=0)
    detalle = models.TextField('detalle', blank=True)
    origen = models.CharField('origen', max_length=20, default='carpeta')

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'importacion'
        verbose_name_plural = 'importaciones'

    def __str__(self):
        return f'{self.archivo} ({self.get_estado_display()})'


class MesCerrado(models.Model):
    anio = models.PositiveSmallIntegerField('anio')
    mes = models.PositiveSmallIntegerField('mes')
    cerrado_en = models.DateTimeField('cerrado el', auto_now_add=True)

    class Meta:
        ordering = ['-anio', '-mes']
        unique_together = ('anio', 'mes')
        verbose_name = 'mes cerrado'
        verbose_name_plural = 'meses cerrados'

    def __str__(self):
        return f'{self.anio:04d}-{self.mes:02d}'


class Empleado(models.Model):
    codigo = models.CharField('codigo', max_length=20, blank=True, default='')
    nombre = models.CharField('nombre', max_length=100)
    activo = models.BooleanField('activo', default=True)
    tiene_almuerzo = models.BooleanField(
        'tiene almuerzo', default=True,
        help_text='si esta marcado el turno se parte por el almuerzo y se controla '
                  'el regreso; si no, las horas son continuas')
    creado_en = models.DateTimeField('creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('actualizado en', auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'empleado'
        verbose_name_plural = 'empleados'
        constraints = [
            models.UniqueConstraint(fields=['codigo'], condition=~Q(codigo=''),
                                    name='empleado_codigo_unico'),
        ]

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip()
        self.codigo = self.codigo.strip()
        super().save(*args, **kwargs)
        Horario.objects.get_or_create(empleado=self)

    @cached_property
    def horario(self):
        horario, _ = Horario.objects.get_or_create(empleado=self)
        return horario

    def __str__(self):
        return self.nombre if not self.codigo else f'{self.codigo} - {self.nombre}'


class Horario(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='horario_base')
    hora_entrada = models.TimeField('hora de entrada', default=hora_entrada_default)
    hora_salida = models.TimeField('hora de salida', default=hora_salida_default)
    tolerancia_min = models.PositiveIntegerField('tolerancia (min)', default=5)
    dias = models.CharField('dias laborales', max_length=30, default='0,1,2,3,4,5',
                            help_text='0=lunes ... 6=domingo, separados por coma')

    class Meta:
        verbose_name = 'horario'
        verbose_name_plural = 'horarios'

    def dias_activos(self):
        try:
            return {int(x) for x in self.dias.split(',') if x.strip() != ''}
        except ValueError:
            return set()

    def es_dia_laboral(self, fecha):
        return fecha.weekday() in self.dias_activos()

    def __str__(self):
        return f'{self.hora_entrada.strftime("%H:%M")} - {self.hora_salida.strftime("%H:%M")}'


class HorarioDia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='horarios_dia')
    fecha = models.DateField('fecha')
    hora_entrada = models.TimeField('hora de entrada', default=hora_entrada_default)
    hora_salida = models.TimeField('hora de salida', default=hora_salida_default)
    tolerancia_min = models.PositiveIntegerField('tolerancia (min)', default=5)
    libre = models.BooleanField('dia libre', default=False,
                            help_text='si esta marcado, el dia no cuenta como laboral')
    motivo = models.CharField('motivo', max_length=40, default='', blank=True,
                            help_text='si esta marcado, el dia no cuenta como laboral')
    almuerzo_inicio = models.TimeField('almuerzo desde', null=True, blank=True,
                                       help_text='inicio del almuerzo (pausa); vacio = sin pausa')
    almuerzo_fin = models.TimeField('almuerzo hasta', null=True, blank=True,
                                    help_text='fin del almuerzo (pausa); vacio = sin pausa')
    creado_en = models.DateTimeField('creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('actualizado en', auto_now=True)

    class Meta:
        ordering = ['-fecha', 'empleado__nombre']
        verbose_name = 'horario asignado'
        verbose_name_plural = 'horarios asignados'
        constraints = [
            models.UniqueConstraint(fields=['empleado', 'fecha'],
                                    name='horariodia_unica'),
        ]

    @property
    def pausa(self):
        if self.almuerzo_inicio and self.almuerzo_fin:
            return self.almuerzo_inicio, self.almuerzo_fin
        return None

    @property
    def rango(self):
        if self.libre:
            return 'Libre'
        base = (f'{self.hora_entrada.strftime("%H:%M")} - '
                f'{self.hora_salida.strftime("%H:%M")}')
        pausa = self.pausa
        if pausa:
            base += (f' (pausa {pausa[0].strftime("%H:%M")}-'
                     f'{pausa[1].strftime("%H:%M")})')
        return base

    def __str__(self):
        return f'{self.empleado.nombre} {self.fecha} {self.rango}'


class Marcacion(models.Model):
    ESTADOS = [
        ('', 'Sin estado'),
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
        ('PRESENTE', 'Presente'),
        ('LLEGADO TARDE', 'Llegado tarde'),
        ('SALIDA ANTICIPADA', 'Salida anticipada'),
        ('AUSENTE', 'Ausente'),
        ('OTRO', 'Otro'),
    ]

    fecha = models.DateField('fecha')
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='marcaciones')
    hora = models.TimeField('hora')
    estado = models.CharField('estado del reloj', max_length=30, choices=ESTADOS, blank=True, default='')
    importacion = models.ForeignKey(Importacion, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='marcaciones')
    creado_en = models.DateTimeField('creado en', auto_now_add=True)

    class Meta:
        ordering = ['-fecha', 'hora']
        verbose_name = 'marcacion'
        verbose_name_plural = 'marcaciones'
        indexes = [models.Index(fields=['fecha', 'empleado'])]
        constraints = [
            models.UniqueConstraint(fields=['fecha', 'empleado', 'hora'],
                                    name='marcacion_unica'),
        ]

    def __str__(self):
        return f'{self.empleado.nombre} {self.fecha} {self.hora.strftime("%H:%M")}'


class Configuracion(models.Model):
    """Datos de la empresa: una sola fila, usada en el PDF y en las pantallas."""
    nombre = models.CharField('nombre de la empresa', max_length=120,
                              default='', blank=True)
    ruc = models.CharField('RUC', max_length=40, blank=True, default='')
    direccion = models.CharField('direccion', max_length=160, blank=True,
                                 default='')
    telefono = models.CharField('telefono', max_length=40, blank=True, default='')
    correo = models.CharField('correo', max_length=80, blank=True, default='')
    encargado = models.CharField('responsable del area', max_length=120,
                                 blank=True, default='')
    pie = models.CharField('nota al pie del reporte', max_length=200,
                           blank=True, default='',
                           help_text='se imprime al final del PDF')

    class Meta:
        verbose_name = 'configuracion'
        verbose_name_plural = 'configuracion'

    @classmethod
    def get(cls):
        instancia, _ = cls.objects.get_or_create(pk=1)
        return instancia

    def save(self, *args, **kwargs):
        self.pk = 1
        self.nombre = (self.nombre or '').strip()
        for campo in ('ruc', 'direccion', 'telefono', 'correo', 'encargado',
                      'pie'):
            setattr(self, campo, (getattr(self, campo) or '').strip())
        super().save(*args, **kwargs)

    @property
    def titulo(self):
        """Nombre para mostrar; si no esta cargado usa el reloj."""
        return self.nombre or 'Reloj LX50'

    def linea_contacto(self):
        partes = [f'RUC {self.ruc}' if self.ruc else '']
        partes += [self.direccion, self.telefono, self.correo]
        return '  ·  '.join(p for p in partes if p)

    def __str__(self):
        return self.nombre
