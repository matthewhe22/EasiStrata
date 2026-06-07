from django.template.loader import render_to_string

from my_project import settings

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    HTML = CSS = None
    WEASYPRINT_AVAILABLE = False


def pdf_to_file(template_name, context, filename, css_path, tmp_folder="/temp_agm/", request=None):
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError(
            "PDF generation is unavailable: WeasyPrint and its native "
            "dependencies (Cairo/Pango) are not installed in this environment."
        )
    # css_path example '/css/agm.css'
    filename = tmp_folder + filename
    html_string = render_to_string(template_name, context)
    if request is not None:
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
    else:
        html = HTML(string=html_string)

    save_location = settings.MEDIA_ROOT + filename
    html.write_pdf(target=save_location, stylesheets=[CSS(settings.STATIC_DIR + css_path)], presentational_hints=True)

    return save_location
