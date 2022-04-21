# -*- coding: utf-8 -*-
from reportlab.platypus import Image, Spacer, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle as PS
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import arcpy
import os
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.platypus import *

arcpy.env.overwriteOutput = True


################################
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import datetime
from reportlab.lib.utils import ImageReader

LogoSERNANP = r'E:\sernanp\logo_sernanp.jpg'
LogoTeledeteccion = r'E:\sernanp\teledeteccion.jpg'

#   CREADO ESTILOS DE TEXTO
h1 = PS(
    name='Heading1',
    fontSize=7,
    leading=8
)
h3 = PS(
    name='Normal',
    fontSize=6.5,
    leading=10,
    alignment=TA_CENTER
)
h4 = PS(
    name='Normal',
    fontSize=6.5,
    leading=10,
    alignment=TA_LEFT
)
h5 = PS(
    name='Heading1',
    fontSize=7,
    leading=8,
    alignment=TA_RIGHT
)
h_sub_tile = PS(
    name='Heading1',
    fontSize=10,
    leading=14,
    alignment=TA_CENTER
)
h_sub_tile_2 = PS(
    name='Heading1',
    fontSize=8,
    leading=11,
    alignment=TA_CENTER
)

class PDFReport(object):
    def __init__(self):
        self.doc = SimpleDocTemplate("simple_table.pdf", pagesize=A4, rightMargin=65,
                                     leftMargin=65,
                                     topMargin=0.5 * cm,
                                     bottomMargin=0.5 * cm, )
        self.docElements = []
        PDFReport.styles = getSampleStyleSheet()

    def put_dataframe_on_pdfpage(self, df):
        elements = []

        # Titulo = Paragraph(u'<strong>Deforestación en hectáreas en ANP del bioma amazónico del 17 al 28 de Febrero - ATD del PNCB con filtro de la causa de pérdida realizado por el área de teledetección de SERNANP</strong>', h_sub_tile)
        # Titulo2 = Paragraph(u'Deforestación en hectáreas en ANP del bioma amazónico del 17 al 28 de Febrero - ATD del PNCB con filtro de la causa de pérdida realizado por el área de teledetección de SERNANP', h_sub_tile)
        DDE = Paragraph(u'<strong>DIRECCIÓN DE DESARROLLO ESTRATÉGICO\nUOF de Gestión de Información\nTeledetección-SERNANP</strong>', h3)
        SubTitulo = Paragraph( u'<strong>Deforestación en hectáreas en ANP del bioma amazónico del 17 al 28 de Febrero - ATD del PNCB con filtro de la causa de pérdida realizado por el área de teledetección de SERNANP</strong>', h_sub_tile_2)

        CabeceraPrincipal = [[Image(LogoSERNANP, width=140, height=40), Image(LogoTeledeteccion, width=50, height=50), DDE],
                             [SubTitulo, '', '']]

        Tabla0 = Table(CabeceraPrincipal, colWidths=[8 * cm, 4 * cm, 6 * cm])

        Tabla0.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('SPAN', (0, 1), (-1, -1)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))

        elements.append(Tabla0)
        elements.append(Spacer(0, 10))

        t = Table(df)
        t.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), "Helvetica"),
                               ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))
        elements.append(t)
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(PageBreak())

        self.docElements.extend(elements)

        return elements

    def write_pdfpage(self):
        self.doc.build(self.docElements)


fc = r'E:\sernanp\data\backup_2022_03_21.gdb\MonitDefor'
out_path = r'E:\sernanp\proyectos\monitoreo\reporte'
fields = ["anp_codi", "zi_codi", "md_sup", "md_fecimg"]
list_mesrep = list(set([x[0] for x in arcpy.da.SearchCursor(fc, ["md_mesrep"])]))
domains = [x for x in arcpy.da.ListDomains(r'E:\sernanp\data\backup_2022_03_21.gdb') if x.name == "ANP"][0]
mesrep = 2022033
sql = "md_mesrep = {}".format(mesrep)
np_df = arcpy.da.TableToNumPyArray(fc, fields, sql)
df = pd.DataFrame(np_df)
df["anp_nomb"] = df["anp_codi"].apply(lambda x: domains.codedValues[x])
df_f = df.groupby(("anp_codi", "zi_codi")).agg({
    "md_sup": "sum",
    "md_fecimg": "first",
    "anp_nomb": "first"
})
df_n = df_f.reset_index()
df = pd.DataFrame({
    u'Área Natural Protegida': df_n["anp_nomb"],
    u'ANP Código': df_n["anp_codi"],
    u'ZI Código': df_n["zi_codi"],
    u'Fecha ImagSat': df_n["md_fecimg"].apply(lambda x: x.strftime("%d-%m-%Y")),
    u'Área ha': df_n["md_sup"].apply(lambda x:round(x,2))
})

df = df[[u'Área Natural Protegida', u'ANP Código', u'ZI Código', u'Fecha ImagSat', u'Área ha']]

data = [df.columns[:, ].values.tolist()] + df.values.tolist()

################################
p = PDFReport()
p.put_dataframe_on_pdfpage(data)
p.write_pdfpage()
################################
