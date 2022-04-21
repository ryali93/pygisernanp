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
SCRATCH_Folder = arcpy.env.scratchFolder
PATH_GDB = os.path.join(r"E:/sernanp", r"data/DB_TELEDETECCION_new.gdb")
gpo_deforestacion = os.path.join(PATH_GDB, r"fd_monitoreo/MonitDefor")
gpo_deforestacion_acum = os.path.join(PATH_GDB, r"fd_monitoreo/MonitDeforAcum")

# ---------------------------------------------------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------------------------------------------------
class M02_descargaATD_Sentinel2(object):
    def __init__(self):
        self.SCRATCH = arcpy.env.scratchGDB
        self.SCRATCH_FOLDER = arcpy.env.scratchFolder
        # self.path_anp = arcpy.GetParameterAsText(0)
        # self.path_salida = arcpy.GetParameterAsText(1)
        # self.fecha_inicio = arcpy.GetParameterAsText(2)
        # self.atd_plantilla = arcpy.GetParameterAsText(3)
        self.path_anp = os.path.join(PATH_GDB, 'gpo_anp_monit')
        self.path_salida = r'E:\sernanp'
        self.fecha_inicio = '01/01/2022'
        self.atd_plantilla = gpo_deforestacion

    def download_atd_sentinel2(self, source, path, id_img):
        url_download = u"https://storage.googleapis.com/earthenginepartners-hansen/S2alert/{}/{}.tif".format(source, id_img)
        response = requests.get(url_download)
        data = response.content
        with open(path, 'wb') as s:
            s.write(data)
        print("\timg {} descargada".format(source))

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
        polygon = arcpy.RasterToPolygon_conversion(image, os.path.join(self.SCRATCH_FOLDER, "polygon_{}".format(str(uuid.uuid4())[:4])), 'NO_SIMPLIFY', 'Value')
        multipart = arcpy.MultipartToSinglepart_management(polygon, os.path.join(self.SCRATCH_FOLDER, "multipart_{}".format(str(uuid.uuid4())[:4])))
        return multipart

    def clip_to_anp(self, feature):
        # gpo_feature = arcpy.MakeFeatureLayer_management(feature, "gpo_feature")
        gpo_anp = arcpy.MakeFeatureLayer_management(self.path_anp, "gpo_anp")
        # clip = arcpy.Clip_analysis(feature, gpo_anp, "in_memory\\clip", '#')
        clip = arcpy.Clip_analysis(feature, gpo_anp, os.path.join(self.SCRATCH_FOLDER, "image_clip")) # "image_clip_{}".format(str(uuid.uuid4())[:4])
        return clip

    def filter_atd(self, image, treshold):
        print(image)
        print(treshold)
        filtered_image = arcpy.gp.ExtractByAttributes_sa(image, '"Value" > {}'.format(treshold), os.path.join(SCRATCH_Folder, "f_image_{}.tif".format(str(uuid.uuid4())[:4])))
        return filtered_image

    def reclass_atd_alert(self, image):
        reclass_image = arcpy.gp.Reclassify_sa(image, 'Value', '0 0;1 0;2 0;3 1;4 1',
                                               os.path.join(
                                                   self.SCRATCH,
                                                   "reclass_image_{}".format(str(uuid.uuid4())[:4])), 'DATA')
        return reclass_image

    def calc_and_filter_raster(self, filtered_image_alertdate, filtered_image_alert):
        filtered_image = arcpy.sa.Raster(filtered_image_alertdate) * arcpy.sa.Raster(filtered_image_alert)
        arcpy.management.CopyRaster(filtered_image, os.path.join(
                                                   self.SCRATCH,
                                                   "filtered_image_{}".format(str(uuid.uuid4())[:4])))
        return filtered_image

    def update_fields(self, feature, date_list):
        field_date = "md_fecimg"
        if field_date not in [x.name for x in arcpy.ListFields(feature)]:
            arcpy.AddField_management(feature, field_date, "DATE")
        with arcpy.da.UpdateCursor(feature, ["gridcode", field_date], "gridcode <> 0") as cursor:
            for y in cursor:
                y[1] = date_list[y[0]]
                cursor.updateRow(y)

    def copy_feature(self, feature, folder, name):
        output = arcpy.CopyFeatures_management(feature, os.path.join(folder, "{}.shp".format(name)))
        return output

    def append_feature(self, input, target):
        arcpy.Append_management(input, target, "NO_TEST")

    def main(self):
        id_imgs = ["070W_20S_060W_10S"] # , "080W_10S_070W_00N", "080W_20S_070W_10S", "070W_20S_060W_10S"
        # temp_folder = tempfile.mkdtemp()
        temp_folder = r"C:\Users\ryali93\AppData\Local\Temp\tmpuxbj_0"
        # atd_nuevo = self.copy_feature(self.atd_plantilla, self.path_salida, "gpo_defor_sentinel2_{}".format(datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S")))
        # arcpy.DeleteRows_management(atd_nuevo)
        atd_nuevo = "E:\sernanp\gpo_defor_sentinel2_2022_02_09_17_32_47.shp"
        # 1. Extraer treshold de fechas
        treshold_date, date_list = self.extract_date(self.fecha_inicio)
        arcpy.AddMessage("Se calcula el treshold_date de fechas: {}".format(treshold_date))
        for id_img in id_imgs:
            arcpy.AddMessage("{}:\nInicio: {}".format(id_img, datetime.datetime.now()))

            # 2. Descarga de imagenes
            # path_scene_alertDate = r"E:\sernanp\proyectos\monitoreo\sentinel\2022_02_10\ALERTA_080W_20S_070W_10S.tif"
            path_scene_alertDate = os.path.join(temp_folder, "alertDate{}.tif".format(id_img))
            # path_scene_alert = os.path.join(temp_folder, "alert{}.tif".format(id_img))
            # self.download_atd_sentinel2("alertDate", path_scene_alertDate, id_img)
            # self.download_atd_sentinel2("alert", path_scene_alert, id_img)

            # 2. Filtro de ATDs
            # filtered_image_alertdate = self.filter_atd(path_scene_alertDate, treshold=treshold_date)
            # filtered_image_alert = self.reclass_atd_alert(path_scene_alert)
            filtered_image = self.filter_atd(path_scene_alertDate, treshold=treshold_date) ## <-----
            # #
            # filtered_image = self.calc_and_filter_raster(filtered_image_alertdate, filtered_image_alert)
            # arcpy.AddMessage("Se calcula el filtro por fechas")
            # #
            # # 4. ## <-----
            defor_pol = self.raster_to_pol(filtered_image)
            arcpy.AddMessage("Se transformo a feature")
            # defor_pol = r"E:\sernanp\proyectos\monitoreo\sentinel.gdb\gpo_sentinel"
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

