"""
Vistas de configuración del proyecto (ej. servir SPA en raíz).
"""
from django.http import HttpResponse, FileResponse, Http404
from django.conf import settings
from django.views.generic import View


class FrontendIndexView(View):
    """
    Sirve el index.html del frontend (React) en la ruta raíz /.
    Necesario para que la SPA cargue al acceder a https://dominio/ o https://ip/
    """
    def get(self, request):
        index_path = settings.FRONTEND_BUILD_DIR / 'index.html'
        if not index_path.exists():
            return HttpResponse(
                '<h1>Frontend no generado</h1>'
                '<p>Ejecute en el servidor: <code>cd frontend && npm run build</code></p>'
                '<p>Luego: <code>python manage.py collectstatic --noinput</code></p>',
                status=503,
                content_type='text/html',
            )
        content = index_path.read_text(encoding='utf-8')
        return HttpResponse(content, content_type='text/html')


def serve_frontend_asset(request, filename):
    """Sirve manifest.json, favicon.ico, etc. desde la raíz del build del frontend."""
    path = settings.FRONTEND_BUILD_DIR / filename
    if not path.exists() or not path.is_file():
        raise Http404
    content_type = 'application/json' if filename.endswith('.json') else None
    return FileResponse(path.open('rb'), content_type=content_type)
