#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import zipfile
import tempfile
import datetime
import arcpy
import os

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------------------------------------------------
arcpy.env.overwriteOutput = True

SCRATCH = arcpy.env.scratchGDB
PATH_GDB = r'E:\sernanp\data\DB_TELEDETECCION.gdb'
# atd_plantilla = os.path.join(PATH_GDB, r"fd_monitoreo\MonitDeforAcum")
atd_plantilla = r'E:\sernanp\proyectos\monitoreo\historico\gdb_monit.gdb\MonitoreoDeforestacion\MonitDefor'
gpo_anp = os.path.join(PATH_GDB, 'gpo_anp_monit')
path_salida = r'E:\sernanp\proyectos\monitoreo\pncb'

# ---------------------------------------------------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------------------------------------------------
class M01_descargaATD_Geobosques(object):
    def __init__(self):
        # self.SCRATCH = arcpy.env.scratchGDB
        # self.path_anp = arcpy.GetParameterAsText(0)
        # self.folder_salida = arcpy.GetParameterAsText(1)
        # self.fecha_inicio = arcpy.GetParameterAsText(2)
        # self.atd_plantilla = arcpy.GetParameterAsText(3)
        self.path_anp = gpo_anp
        self.folder_salida = path_salida
        self.fecha_inicio = '01/01/2022'
        self.atd_plantilla = atd_plantilla

    def download_atd(self, path):
        url_download = u"http://geobosques.minam.gob.pe/geobosque/descargas_geobosque/alerta/espaciales/Alertas_PNCB_raster_2022.zip"
        response = requests.get(url_download)
        data = response.content
        with open(path, 'wb') as s:
            s.write(data)

    def unzip_atd(self, path, output):
        with zipfile.ZipFile(path, 'r') as zip_ref:
            zip_ref.extractall(output)

    def raster_to_pol(self, folder_image):
        atd_file = [os.path.join(folder_image, x) for x in os.listdir(folder_image) if x.endswith(".tif")][0]
        polygon = arcpy.RasterToPolygon_conversion(atd_file, "in_memory\\polygon", 'NO_SIMPLIFY', 'Fecha')
        return polygon

    def atd_evaluate(self, feature):
        anp = self.path_anp
        atd_plantilla = self.atd_plantilla

        # Multipart to SinglePart
        start = datetime.datetime.strptime(self.fecha_inicio, "%d/%m/%Y")
        end = datetime.datetime.strptime("31/12/2022", "%d/%m/%Y")
        lista_fechas = [(start + datetime.timedelta(days=x)).strftime("%d/%m/%Y") for x in range(0, (end - start).days)]
        lista_fechas = ["{}/{}/{}".format(int(x.split("/")[0]), x.split("/")[1], x.split("/")[2]) for x in lista_fechas]

        # Listado de fechas
        sql = "{} IN ('{}')".format("Fecha", "','".join(lista_fechas))
        # Filtrar por fechas
        mfl_pol = arcpy.MakeFeatureLayer_management(feature, 'mfl_atd', sql)
        anp_mfl = arcpy.MakeFeatureLayer_management(anp, "anp_mfl")
        # Cortar por ANP
        atd_clip = arcpy.Clip_analysis(mfl_pol, anp_mfl, "in_memory\\atd_clip", '#')
        arcpy.AddField_management(atd_clip, "md_fecimg", "DATE")
        arcpy.AddField_management(atd_clip, "anp_codi", "STRING")

        print([x.name for x in arcpy.ListFields(atd_clip)])
        lista_fechas_nombre = []

        with arcpy.da.UpdateCursor(atd_clip, ["Fecha", "md_fecimg", "anp_codi", "OBJECTID"]) as cursor:
            for x in cursor:
                sql_mfl = "{} = {}".format("OBJECTID", x[3])
                atd_clip_mfl = arcpy.MakeFeatureLayer_management(atd_clip, "atd_clip_mfl", sql_mfl)
                x[1] = datetime.datetime.strptime(x[0], "%d/%m/%Y")
                lista_fechas_nombre.append(x[1])

                anp_mfl_sel = arcpy.SelectLayerByLocation_management(anp_mfl, "INTERSECT", atd_clip_mfl, "#", 'NEW_SELECTION')
                x[2] = [y[0] for y in arcpy.da.SearchCursor(anp_mfl_sel, ["anp_codi"])][0]
                arcpy.SelectLayerByAttribute_management(anp_mfl_sel, 'CLEAR_SELECTION')
                cursor.updateRow(x)

        print(lista_fechas_nombre)
        min_fecha = min(lista_fechas_nombre).strftime("%Y%m%d")
        max_fecha = max(lista_fechas_nombre).strftime("%Y%m%d")

        path_salida = 'gpo_defor_alerta_{}_{}'.format(min_fecha, max_fecha)
        atd_nuevo = self.copy_feature(atd_plantilla, self.folder_salida, path_salida)
        arcpy.DeleteRows_management(atd_nuevo)

        arcpy.Append_management(atd_clip, atd_nuevo, "NO_TEST")

    def copy_feature(self, feature, folder, name):
        return arcpy.CopyFeatures_management(feature, os.path.join(folder, "{}.shp".format(name)))

    def main(self):
        arcpy.AddMessage("\nInicio: {}".format(datetime.datetime.now()))
        temp_folder = tempfile.mkdtemp()
        path_zip = os.path.join(temp_folder, "atd.zip")
        path_folder = os.path.join(temp_folder, "atd_fecha")
        arcpy.AddMessage("Se creo la carpeta temporal y se guardo el tif en: {}".format(path_folder))
        self.download_atd(path_zip)
        self.unzip_atd(path_zip, path_folder)
        arcpy.AddMessage("Se transformo a feature")
        polygons = self.raster_to_pol(path_folder)
        arcpy.AddMessage("Se esta evaluando el ATD")
        self.atd_evaluate(polygons)
        arcpy.AddMessage("Se termino la evaluacion del ATD")
        arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

if __name__ == '__main__':
    poo = M01_descargaATD_Geobosques()
    poo.main()
