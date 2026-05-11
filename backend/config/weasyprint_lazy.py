"""Importación diferida de WeasyPrint para que Django arranque sin Pango/GObject en el PATH."""


def get_html():
    """
    Devuelve la clase HTML de WeasyPrint, importándola solo al usar PDFs.

    En macOS suele hacer falta: brew install pango cairo gdk-pixbuf libffi
    """
    try:
        from weasyprint import HTML
    except OSError as exc:
        raise RuntimeError(
            "WeasyPrint no pudo cargar las bibliotecas del sistema (p. ej. libgobject / Pango). "
            "Instala dependencias nativas o usa un entorno donde WeasyPrint esté configurado. "
            "En macOS con Homebrew suele bastar: brew install pango cairo gdk-pixbuf libffi"
        ) from exc
    return HTML
