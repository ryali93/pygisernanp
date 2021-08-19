#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import zipfile
import tempfile
import datetime
import arcpy
import os
import uuid

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------------------------------------------------
arcpy.env.overwriteOutput = True

SCRATCH = arcpy.env.scratchGDB
# PATH_GDB = os.path.join(r"E:/sernanp", r"data/DB_TELEDETECCION_new.gdb")
# gpo_deforestacion_acum = os.path.join(PATH_GDB, r"fd_monitoreo/MonitDeforAcum")

# ---------------------------------------------------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------------------------------------------------
class M02_descargaATD_Sentinel2(object):
    def __init__(self):
        self.SCRATCH = arcpy.env.scratchGDB
        self.path_anp = arcpy.GetParameterAsText(0)
        self.path_salida = arcpy.GetParameterAsText(1)
        self.fecha_inicio = arcpy.GetParameterAsText(2)
        self.atd_plantilla = arcpy.GetParameterAsText(3)
        # self.path_anp = os.path.join(PATH_GDB, 'gpo_anp')
        # self.folder_salida = r'E:\sernanp\data'
        # self.fecha_inicio = '01/03/2021'
        # self.atd_plantilla = gpo_deforestacion_acum

    def download_atd_sentinel2(self, path, id_img):
        url_download = u"https://storage.googleapis.com/earthenginepartners-hansen/S2alert/alertDate/%s.tif" % id_img
        response = requests.get(url_download)
        data = response.content
        with open(path, 'wb') as s:
            s.write(data)
        print("\timg descargada")

    def extract_date(self, date):
        '''
        :param date: Fecha con el formato (dia/mes/anno) "%d/%m/%Y"
        :return:
        '''
        fecha_ini = 731
        numdays = 2000
        base = datetime.datetime.strptime("01-01-2019", "%d-%m-%Y")
        date_list = {x: base + datetime.timedelta(days=x) for x in range(fecha_ini, fecha_ini + numdays)}
        date_list_value = {x: (base + datetime.timedelta(days=x)).strftime("%d/%m/%Y") for x in range(fecha_ini, fecha_ini + numdays)}
        treshold = [l[0] for l in date_list_value.items() if l[1] == date][0]
        return treshold, date_list

    def raster_to_pol(self, image):
        polygon = arcpy.RasterToPolygon_conversion(image, "in_memory\\polygon", 'NO_SIMPLIFY', 'Value')
        multipart = arcpy.MultipartToSinglepart_management(polygon, "in_memory\\multipart")
        return multipart

    def clip_to_anp(self, feature):
        gpo_anp = arcpy.MakeFeatureLayer_management(self.path_anp, "gpo_anp")
        clip = arcpy.Clip_analysis(feature, gpo_anp, "in_memory\\clip", '#')
        return clip

    def filter_atd(self, image, treshold):
        print(image)
        filtered_image = arcpy.gp.ExtractByAttributes_sa(image, '"Value" > {}'.format(treshold), os.path.join(self.SCRATCH, "f_image_{}".format(str(uuid.uuid4())[:4])))
        return filtered_image

    def update_fields(self, feature, date_list):
        field_date = "md_fecimg"
        if field_date not in [x.name for x in arcpy.ListFields(feature)]:
            arcpy.AddField_management(feature, field_date, "DATE")
        with arcpy.da.UpdateCursor(feature, ["gridcode", field_date]) as cursor:
            for y in cursor:
                y[1] = date_list[y[0]]
                cursor.updateRow(y)

    def copy_feature(self, feature, folder, name):
        output = arcpy.CopyFeatures_management(feature, os.path.join(folder, "{}.shp".format(name)))
        return output

    def append_feature(self, input, target):
        arcpy.Append_management(input, target, "NO_TEST")

    def main(self):
        id_imgs = ["080W_20S_070W_10S", "080W_10S_070W_00N", "070W_20S_060W_10S"]
        temp_folder = tempfile.mkdtemp()
        atd_nuevo = self.copy_feature(self.atd_plantilla, self.path_salida,
                                      "gpo_defor_sentinel2_{}".format(datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")))
        arcpy.DeleteRows_management(atd_nuevo)
        for id_img in id_imgs:
            arcpy.AddMessage("{}:\nInicio: {}".format(id_img, datetime.datetime.now()))
            path_scene = os.path.join(temp_folder, "{}.tif".format(id_img))
            self.download_atd_sentinel2(path_scene, id_img)
            treshold, date_list = self.extract_date(self.fecha_inicio)
            arcpy.AddMessage("Se calcula el treshold: {}".format(treshold))
            filtered_image = self.filter_atd(path_scene, treshold)
            arcpy.AddMessage("Se calcula el filtro por fechas")
            defor_pol = self.raster_to_pol(filtered_image)
            arcpy.AddMessage("Se transformo a feature")
            defor = self.clip_to_anp(defor_pol)
            arcpy.AddMessage("Se corto por anps")
            self.update_fields(defor, date_list)
            arcpy.AddMessage("Se actualizaron los campos")
            # self.copy_feature(defor, temp_folder, id_img)
            self.append_feature(defor, atd_nuevo)
            arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

if __name__ == '__main__':
    poo = M02_descargaATD_Sentinel2()
    poo.main()

