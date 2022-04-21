#!/usr/bin/env python
# -*- coding: utf-8 -*-
import arcpy
import os
from datetime import datetime

now = datetime.now()
fecha_hoy = now.strftime("%m/%d/%Y")

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------------------------------------------------
arcpy.env.overwriteOutput = True

# PATH_GDB = arcpy.GetParameterAsText(0)                   # Ruta de la gdb
# gpo_zona_interes = arcpy.GetParameterAsText(1)           # Feature del grillado
# path_template = arcpy.GetParameterAsText(2)              # Mxd plantilla
# OUTPUT_DIR = arcpy.GetParameterAsText(3)                 # Ruta de los reportes
# REPORTE = arcpy.GetParameterAsText(4)

# ------------------------------------ PARA CORRER DESDE SCRIPT -------------------------------------------------------
BASE_DIR = r"E:\sernanp"
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
TEMPLATES_DIR = os.path.join(SCRIPTS_DIR, "templates")
OUTPUT_DIR = os.path.join(SCRIPTS_DIR, "output") # Obligatorio

SCRATCH = arcpy.env.scratchGDB
PATH_GDB = os.path.join(BASE_DIR, r"data/DB_TELEDETECCION_new.gdb") # Obligatorio
gpo_zona_interes = os.path.join(PATH_GDB, r"gpo_zpaa_monit") # Obligatorio
gpo_deforestacion = os.path.join(PATH_GDB, r"MonitDefor") # Dependiente
gpo_deforestacion_acum = os.path.join(PATH_GDB, r"MonitDeforAcum") # Dependiente
path_template = os.path.join(TEMPLATES_DIR, r"reportes_18s_202009_n.mxd") # Obligatorio
REPORTE = "202106_2"

# ---------------------------------------------------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------------------------------------------------
def read_templates(path_mxd):
    mxd = arcpy.mapping.MapDocument(path_mxd)
    df_anp = arcpy.mapping.ListDataFrames(mxd, "anp")[0]
    df_capas = arcpy.mapping.ListDataFrames(mxd, "capas")[0]
    return mxd, df_anp, df_capas

def select_codes(MES_REV):
    MESREP = MES_REPORTE(MES_REV)
    sql_mesrev = "{} = {}".format("MD_MESREP", MESREP)
    print(sql_mesrev)
    lista_codigos_zi = list(set([x[0] for x in arcpy.da.SearchCursor(gpo_deforestacion, ["ZI_CODI"], sql_mesrev)]))
    sql_codigos = "{} in ('{}')".format("ZI_CODI", "','".join(lista_codigos_zi))
    print(sql_codigos)
    domains = [x.codedValues for x in arcpy.da.ListDomains(PATH_GDB) if x.name == "ANP"][0]
    lista_codigos = [[x[0], domains[x[0].split("_")[0]]] for x in arcpy.da.SearchCursor(gpo_zona_interes, ["ZI_CODI"], sql_codigos)]
    return lista_codigos

def create_folder(MES_REV):
    dir_path = os.path.join(OUTPUT_DIR, "reportes_{}".format(MES_REV))
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

def MES_REPORTE(MES_REV):
    a = int(MES_REV.replace("_", ""))
    print(a)
    return a

def crear_mapa(MES_REV, codigo_zi, nombre_anp):
    MESREP = MES_REPORTE(MES_REV)
    lyr1 = "MonitoreoDeforestacion"
    lyr2 = "MonitoreoDeforestacionAcumuladoHist"
    lyr3 = "MonitoreoDeforestacionAcumulado2021"
    mxd, df_anp, df_capas = read_templates(path_template)

    sql = "{} = '{}'".format("ZI_CODI", codigo_zi)
    sql_acum = "{} = '{}' AND {} = {}".format("ZI_CODI", codigo_zi, "MD_MESREP", MESREP)
    sql_ult_ano = "{} = '{}' AND {} <> {}".format("ZI_CODI", codigo_zi, "MD_MESREP", MESREP)
    print(sql)
    print(sql_acum)
    date_satimg_current = [x[0] for x in arcpy.da.SearchCursor(gpo_deforestacion, ["MD_FECIMG"], sql_acum)]
    fecha_isat_historico = [x[0] for x in arcpy.da.SearchCursor(gpo_deforestacion_acum, ["MD_FECIMG"], sql)]
    fecha_isat_historico_2021 = [x[0] for x in arcpy.da.SearchCursor(gpo_deforestacion, ["MD_FECIMG"], sql_ult_ano)]
    mfl_zi = arcpy.MakeFeatureLayer_management(gpo_zona_interes, "mfl_zi", sql)
    anp_codi = [x[0] for x in arcpy.da.SearchCursor(mfl_zi, ["ANP_CODI"])][0]

    print("LLEEEEEEEEEEGOOOOO")
    suma_area_actual = 0
    if len(date_satimg_current)>0:
        sql_area = "{} = '{}' AND {} = {}".format("ZI_CODI", codigo_zi, "MD_MESREP", MESREP)
        print(sql_area)
        areas_actuales = [x[0] for x in arcpy.da.SearchCursor(gpo_deforestacion, ["MD_SUP"], sql_area)]
        suma_area_actual = round(sum(areas_actuales),2)

    for i in arcpy.mapping.ListLayers(mxd):
        if i.name == 'gpo_zpaa_monit':
            i.definitionQuery = "{} = '{}'".format("ZI_CODI", codigo_zi)
            df_capas.extent = i.getSelectedExtent()
            df_capas.scale = 42000
            print("df_capas.scale 1")
            print(df_capas.scale)
            arcpy.RefreshActiveView()
        if i.name == "gpo_anp_current":
            i.definitionQuery = "{} = '{}'".format("ANP_CODI", anp_codi)
            df_anp.extent = i.getSelectedExtent()
            df_anp.scale = df_anp.scale*1.4
            arcpy.RefreshActiveView()
        if i.name == "MonitoreoDeforestacion":
            i.definitionQuery = sql_acum
            arcpy.RefreshActiveView()

    legend = arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[1]

    for lyr in legend.listLegendItemLayers():
        if lyr.name == lyr1:
            lyr1 = u"Defor. al {} | {} ha".format(date_satimg_current[-1].strftime("%d/%m/%Y"), suma_area_actual)
            lyr.name = lyr1
            print(lyr.name)
        if lyr.name == lyr2:
            if len(fecha_isat_historico) > 0:
                lyr2 = u"Defor. acum. al 2020"
                lyr.name = lyr2
            else:
                lyr2 = u"Sin Deforestación histórica"
                lyr.name = lyr2
            print(lyr.name)
        if lyr.name == lyr3:
            if len(fecha_isat_historico_2021) > 0:
                lyr3 = u'Defor. acum. 2021 {}'.format(max(fecha_isat_historico_2021).strftime("%d/%m/%Y"))
                lyr.name = lyr3
            else:
                lyr3 = u'Sin Deforestación 2021'
                lyr.name = lyr3
            print(lyr.name)

    arcpy.RefreshActiveView()
    # Cambiar elementos de texto
    ElementoTexto_Titulo = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "TITULO")[0]
    if len(nombre_anp) > 27:
        ElementoTexto_Titulo.text = u'{}\n{}'.format(" ".join(nombre_anp.split(" ")[:3]), " ".join(nombre_anp.split(" ")[3:]))
    else:
        ElementoTexto_Titulo.text = u'{}'.format(nombre_anp)
    arcpy.RefreshActiveView()
    ElementoTexto_ZI_Fecha = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "ZI_FECHA")[0]
    ElementoTexto_ZI_Fecha.text = u'{} - {}'.format(codigo_zi, date_satimg_current[-1].strftime("%d/%m/%Y"))
    print("df_capas.scale 2")
    print(df_capas.scale)

    # Exportar mapa
    print(mxd)
    print(codigo_zi)
    print(date_satimg_current[-1].strftime("%Y%m%d"))
    # mxd.saveACopy(r'E:\sernanp\proyectos\mapas\{}_{}.mxd'.format(codigo_zi, date_satimg_current[-1].strftime("%Y%m%d")))
    # anp_codigo = codigo_zi.split("_")[1]
    folder_anp = os.path.join(OUTPUT_DIR, "reportes_{}".format(MES_REV)) #, codigo_zi.split("_")[1])
    if not os.path.exists(folder_anp):
        os.mkdir(folder_anp)
    arcpy.mapping.ExportToJPEG(mxd, os.path.join(folder_anp, "{}_{}.jpg".format(codigo_zi,date_satimg_current[-1].strftime("%Y%m%d"))))
    del mxd
    del df_anp
    del df_capas

def create_copy(feature, MES_REV, lista_codigos, output):
    folder_anp = os.path.join(OUTPUT_DIR, "reportes_{}".format(MES_REV))
    if not os.path.exists(folder_anp):
        os.mkdir(folder_anp)
    MESREP = MES_REPORTE(MES_REV)
    codigos_zi = "','".join(lista_codigos)
    sql = "{} IN ('{}') AND {} = {}".format("ZI_CODI", codigos_zi, "MD_MESREP", MESREP)
    mfl = arcpy.MakeFeatureLayer_management(feature, "mfl", sql)
    arcpy.CopyFeatures_management(mfl, output)

def process():
    MES_REV = REPORTE
    arcpy.AddMessage(MES_REV)
    lista_codigos = select_codes(MES_REV)
    print(lista_codigos)
    create_folder(MES_REV)
    lista_fallas = []
    for i in lista_codigos:
        arcpy.AddMessage(i)
        crear_mapa(MES_REV, i[0], i[1])
    print(lista_fallas)

def main():
    process()

if __name__ == "__main__":
    main()
