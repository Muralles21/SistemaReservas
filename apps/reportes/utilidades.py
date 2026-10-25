"""
Generador generico de reportes en PDF (DRY): recibe un titulo, encabezados
de columna y filas de datos, y produce un PDF tabular con el mismo formato
corporativo para todos los reportes del sistema.
"""
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

COLOR_PRIMARIO = colors.HexColor('#0F6E56')
COLOR_ENCABEZADO_TEXTO = colors.white
COLOR_FILA_ALTERNA = colors.HexColor('#E1F5EE')


def generar_pdf_tabular(titulo, encabezados, filas, nombre_archivo='reporte.pdf'):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer, pagesize=letter,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(titulo, estilos['Title']),
        Paragraph(f"Generado el {timezone.now():%d/%m/%Y %H:%M}", estilos['Normal']),
        Spacer(1, 0.5 * cm),
    ]

    datos_tabla = [encabezados] + filas
    tabla = Table(datos_tabla, repeatRows=1)
    estilo_tabla = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARIO),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_ENCABEZADO_TEXTO),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#B4B2A9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_FILA_ALTERNA]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    tabla.setStyle(estilo_tabla)
    elementos.append(tabla)

    documento.build(elementos)
    buffer.seek(0)
    respuesta = HttpResponse(buffer, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return respuesta
