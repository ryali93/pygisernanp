#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import zipfile
import tempfile
import datetime
from config import *

arcpy.env.overwriteOutput = True

def download_atd(path):
    url_download = "http://geobosques.minam.gob.pe/geobosque/descargas_geobosque/alerta/espaciales/Alertas_PNCB_raster_2021.zip"
    response = requests.get(url_download)
    data = response.content
    with open(path, 'wb') as s:
        s.write(data)

def unzip_atd(path, output):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(output)

def atd_evaluate(path):
    atd_file = [os.path.join(path, x) for x in os.listdir(path) if x.endswith(".tif")][0]
    anp = r'E:\sernanp\data\DB_TELEDETECCION.gdb\gpo_anp'
    zpaa = r'E:\sernanp\data\DB_TELEDETECCION.gdb\gpo_zpaa'
    atd_plantilla = r'E:\sernanp\data\DB_TELEDETECCION.gdb\gpo_defor_alerta_1709_1310_2020'

    # Transformar de TIF a POLIGONO
    atd_pol = arcpy.RasterToPolygon_conversion(atd_file, "in_memory\\atd_pol", 'NO_SIMPLIFY', 'Fecha')

    # Multipart to SinglePart
    start = datetime.datetime.strptime("01/03/2021", "%d/%m/%Y")
    end = datetime.datetime.strptime("31/12/2021", "%d/%m/%Y")
    lista_fechas = [(start + datetime.timedelta(days=x)).strftime("%d/%m/%Y") for x in range(0, (end - start).days)]
    lista_fechas = ["{}/{}/{}".format(int(x.split("/")[0]), x.split("/")[1], x.split("/")[2]) for x in lista_fechas]

    sql = "{} IN ('{}')".format("Fecha", "','".join(lista_fechas))
    mfl_pol = arcpy.MakeFeatureLayer_management(atd_pol, "mfl_atd", sql)

    zpaa_mfl = arcpy.MakeFeatureLayer_management(zpaa, "zpaa_mfl")

    atd_clip = arcpy.Clip_analysis('mfl_atd', anp, "in_memory\\atd_clip", '#')
    arcpy.AddField_management(atd_clip, "mda_fecimg", "DATE")
    arcpy.AddField_management(atd_clip, "zpaa_codi", "STRING")
    arcpy.AddField_management(atd_clip, "anp_codi", "STRING")

    lista_fechas_nombre = []

    with arcpy.da.UpdateCursor(atd_clip, ["Fecha", "mda_fecimg", "zpaa_codi", "anp_codi", "OID@"]) as cursor:
        for x in cursor:
            sql_mfl = "{} = {}".format("OBJECTID", x[4])
            atd_clip_mfl = arcpy.MakeFeatureLayer_management(atd_clip, "atd_clip_mfl", sql_mfl)
            x[1] = datetime.datetime.strptime(x[0], "%d/%m/%Y")
            lista_fechas_nombre.append(x[1])

            arcpy.SelectLayerByLocation_management(zpaa_mfl, "INTERSECT", atd_clip_mfl, "#", 'NEW_SELECTION')
            zpaa_anp_codi = [[y[0], y[1]] for y in arcpy.da.SearchCursor(zpaa_mfl, ["zpaa_codi", "anp_codi"])][0]
            x[2] = zpaa_anp_codi[0]
            x[3] = zpaa_anp_codi[1]
            arcpy.SelectLayerByAttribute_management(zpaa_mfl, 'CLEAR_SELECTION')

            cursor.updateRow(x)

    min_fecha = min(lista_fechas_nombre).strftime("%Y%m%d")
    max_fecha = max(lista_fechas_nombre).strftime("%Y%m%d")

    atd_nuevo = arcpy.CopyFeatures_management(atd_plantilla,
                                              r'E:\sernanp\data\DB_TELEDETECCION.gdb\gpo_defor_alerta_{}_{}'.format(
                                                  min_fecha, max_fecha))
    arcpy.DeleteRows_management(atd_nuevo)

    arcpy.Append_management(atd_clip, atd_nuevo, "NO_TEST")


def main():
    temp_folder = tempfile.mkdtemp()
    print("temp_folder")
    path_zip = os.path.join(temp_folder, "atd.zip")
    print("path_zip")
    path_folder = os.path.join(temp_folder, "atd_fecha")
    print("path_folder")
    download_atd(path_zip)
    print("download_atd")
    unzip_atd(path_zip, path_folder)
    print("unzip_atd")
    atd_evaluate(path_folder)
    print("atd_evaluate")

if __name__ == '__main__':
    main()



# import arcpy
# arcpy.env.overwriteOutput = True
#
# defor_path = r"E:/sernanp/proyectos/monitoreo/sentinel/def_ANP_I_trim_2021_sen.shp"
# zpaa_path = r'E:/sernanp/data/DB_TELEDETECCION.gdb/gpo_zpaa'
#
# zpaa_codi_list = [x[0] for x in arcpy.da.SearchCursor(zpaa_path, ["zpaa_codi"], "anp_codi in ('PN13','PN15','RC01','RC07','RC08','RC09','RN10','SN07','ZR03')")]
#
# for zpaa_codi in zpaa_codi_list:
#     print(zpaa_codi)
#     sql = "{} = '{}' AND anp_codi in ('PN13','PN15','RC01','RC07','RC08','RC09','RN10','SN07','ZR03')".format("zpaa_codi", zpaa_codi)
#     zpaa_mfl = arcpy.MakeFeatureLayer_management(zpaa_path, "zpaa_mfl", sql)
#     defor_select = arcpy.SelectLayerByLocation_management(defor_path, 'INTERSECT', zpaa_mfl)
#     list_oids = ','.join([str(m[0]) for m in arcpy.da.SearchCursor(defor_select, ["FID"])])
#     print("list_oids = {}".format(len(list_oids)))
#     if len(list_oids) != 0:
#         anp_codi = zpaa_codi.split("_")[0]
#         with arcpy.da.UpdateCursor(defor_select, ["zpaa_codi"], 'FID in ({})'.format(list_oids)) as cursor:
#             for x in cursor:
#                 x[0] = zpaa_codi
#                 cursor.updateRow(x)
#     arcpy.SelectLayerByAttribute_management(defor_select, "CLEAR_SELECTION")