from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def healthcheck(request):
    return JsonResponse({'status': 'ok', 'service': 'reloj-asistencia-zkteco'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', healthcheck, name='healthcheck'),
]

try:
    urlpatterns.append(path('', include('asistencias.urls')))
except ModuleNotFoundError:
    pass
