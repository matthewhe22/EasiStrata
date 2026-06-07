"""Compatibility shim for django-weasyprint.

WeasyPrint depends on native Cairo/Pango libraries that are not available in
every environment (notably serverless platforms such as Vercel). Importing it
at module load would crash the whole app on boot. This shim provides the real
``WeasyTemplateResponseMixin`` when WeasyPrint is importable, and otherwise a
fallback mixin that degrades a PDF view to ordinary HTML rendering so the app
still boots and the rest of the site keeps working.
"""

try:
    from django_weasyprint import WeasyTemplateResponseMixin  # noqa: F401
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

    class WeasyTemplateResponseMixin:
        """No-op fallback.

        With WeasyPrint unavailable, a view that mixes this in behaves like its
        underlying ``TemplateView`` and renders the HTML template directly
        instead of producing a PDF. The PDF-specific class attributes
        (``pdf_stylesheets``, ``pdf_attachment``, ``pdf_filename``) are ignored.
        """
        pass
