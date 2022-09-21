# -*- coding: utf-8 -*-
import requests
import tempfile
import datetime
import arcpy
import os

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------------------------------------------------
arcpy.env.overwriteOutput = True

SCRATCH = arcpy.env.scratchGDB
SCRATCH_FOLDER = arcpy.env.scratchFolder

# fecha_inicio = arcpy.GetParameterAsText(0)
# folder_salida = arcpy.GetParameterAsText(1)
# gdb_template = arcpy.GetParameterAsText(2)
fecha_inicio = '25/07/2022'
folder_salida = r'E:\sernanp\proyectos\monitoreo\sentinel'
gdb_template = r'E:\sernanp\proyectos\monitoreo\gdb_monit_template.gdb'

# Capas para obtener informacion
atd_plantilla = os.path.join(gdb_template, 'MonitDefor')
path_exa = os.path.join(gdb_template, 'gpo_exa')
field_ref_exa, field_fc_exa = "g_cofi", "md_exa"

path_zonif = os.path.join(gdb_template, 'gpo_zonif_anp')
field_ref_zonif, field_fc_zonif = "z_tipo", "md_zonif"

path_anp = os.path.join(gdb_template, 'gpo_anp_monit')
field_ref_anp, field_fc_anp = "anp_codi", "anp_codi"

path_zi = os.path.join(gdb_template, 'gpo_zpaa_monit')
field_ref_zi, field_fc_zi = "zi_codi", "zi_codi"

gpo_defor_acum = os.path.join(gdb_template, 'MonitoreoDeforestacionAcumulado')
path_nobosque2000 = os.path.join(gdb_template, 'gpo_nobosque2000')

# ---------------------------------------------------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------------------------------------------------
def download_atd_sentinel2(source, path, id_img):
    url_download = u"https://storage.googleapis.com/earthenginepartners-hansen/S2alert/{}/{}.tif".format(source, id_img)
    response = requests.get(url_download)
    data = response.content
    with open(path, 'wb') as s:
        s.write(data)
    print("\timg {} descargada".format(source))

def extract_date(date):
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

def raster_to_pol(image):
    polygon = arcpy.RasterToPolygon_conversion(image, os.path.join(SCRATCH_FOLDER, "polygon"), 'NO_SIMPLIFY', 'Value')
    multipart = arcpy.MultipartToSinglepart_management(polygon, os.path.join(SCRATCH_FOLDER, "multipart"))
    return multipart

def clip_to_anp(feature):
    gpo_anp = arcpy.MakeFeatureLayer_management(path_anp, "gpo_anp")
    clip = arcpy.Clip_analysis(feature, gpo_anp, os.path.join(SCRATCH_FOLDER, "image_clip"))
    return clip

def filter_atd(image, treshold):
    filtered_image = arcpy.gp.ExtractByAttributes_sa(image, '"Value" > {}'.format(treshold), os.path.join(SCRATCH_FOLDER, "f_image.tif"))
    return filtered_image

def reclass_atd_alert(image):
    reclass_image = arcpy.gp.Reclassify_sa(image, 'Value', '0 0;1 0;2 0;3 1;4 1',
                                            os.path.join(
                                            SCRATCH,
                                            "reclass_image"), 'DATA')
    return reclass_image

def calc_and_filter_raster(filtered_image_alertdate, filtered_image_alert):
    filtered_image = arcpy.sa.Raster(filtered_image_alertdate) * arcpy.sa.Raster(filtered_image_alert)
    arcpy.management.CopyRaster(filtered_image, os.path.join(
                                                SCRATCH,
                                                "filtered_image"))
    return filtered_image

def update_fields(feature, date_list):
    field_date = "md_fecimg"
    if field_date not in [x.name for x in arcpy.ListFields(feature)]:
        arcpy.AddField_management(feature, field_date, "DATE")
    with arcpy.da.UpdateCursor(feature, ["gridcode", field_date], "gridcode <> 0") as cursor:
        for y in cursor:
            y[1] = date_list[y[0]]
            cursor.updateRow(y)

def copy_feature(feature, folder, name):
    if arcpy.Exists(os.path.join(folder, "ATD_GLAD.gdb")) == False:
        arcpy.CreateFileGDB_management(folder, "ATD_GLAD", "10.0")
    name_fc = os.path.join(folder, "ATD_GLAD.gdb", name)
    arcpy.CopyFeatures_management(feature, name_fc)
    return name_fc

def append_feature(input, target):
    arcpy.Append_management(input, target, "NO_TEST")

def update_field_from_ref(fc, fc_field, ref_fc, ref_field):
    fc_pt = arcpy.FeatureToPoint_management(fc, "in_memory\\out_pt", "INSIDE")
    out_pt = arcpy.SpatialJoin_analysis(fc_pt, ref_fc, "in_memory\\out_pt2", "JOIN_ONE_TO_ONE", "KEEP_ALL")
    if fc_field == ref_field:
        ref_field = ref_field + "_1"
    field_eq = {x[0]:x[1] for x in arcpy.da.SearchCursor(out_pt, ["ORIG_FID", ref_field])}
    with arcpy.da.UpdateCursor(fc, ["OBJECTID", fc_field]) as cursor:
        for x in cursor:
            x[1] = field_eq[x[0]]
            cursor.updateRow(x)

def update_field_tipobosque(fc, ref_fc, ref_fc_2):
    fc_field = "md_bosque"
    arcpy.CalculateField_management(fc, fc_field, '1', 'PYTHON_9.3', '#')
    # Por superposicion 2001-2020 y antes de 2000
    fc_mfl = arcpy.MakeFeatureLayer_management(fc, "fc_mfl")
    defor_acum = arcpy.MakeFeatureLayer_management(ref_fc, "defor_acum")
    defor_antes_2000 = arcpy.MakeFeatureLayer_management(ref_fc_2, "defor_acum_2")
    arcpy.SelectLayerByLocation_management(fc_mfl, 'INTERSECT', defor_acum, '0 Kilometers', 'NEW_SELECTION', 'NOT_INVERT')
    arcpy.SelectLayerByLocation_management(fc_mfl, 'INTERSECT', defor_antes_2000, '0 Kilometers', 'ADD_TO_SELECTION', 'NOT_INVERT')
    list_oid = [str(x[0]) for x in arcpy.da.SearchCursor(fc_mfl, ["OBJECTID"])]
    sql = "OBJECTID in ({})".format(','.join(list_oid))
    with arcpy.da.UpdateCursor(fc, [fc_field], sql) as cursor:
        for x in cursor:
            x[0] = 2
            cursor.updateRow(x)

def update_field_sup(fc):
    exp = "!SHAPE.AREA@HECTARES!"
    arcpy.CalculateField_management(fc, "md_sup", exp, "PYTHON_9.3")

def update_field_conf(fc, folder_img):
    fc_conf_mfl = arcpy.MakeFeatureLayer_management(fc, "fc_conf_mfl")
    fc_pt = arcpy.FeatureToPoint_management(fc_conf_mfl, os.path.join(SCRATCH, "fc_pt"), "INSIDE")
    arcpy.gp.ExtractMultiValuesToPoints_sa(fc_pt,
                                           '{} conf1;{} conf2;{} conf3'.format(
                                               os.path.join(folder_img, "alert080W_20S_070W_10S.tif"),
                                               os.path.join(folder_img, "alert080W_20S_070W_10S.tif"),
                                               os.path.join(folder_img, "alert080W_20S_070W_10S.tif")
                                               ),
                                           'NONE')
    field_conf = "conf"
    if field_conf not in [x.name for x in arcpy.ListFields(fc_pt)]:
        arcpy.AddField_management(fc_pt, field_conf, "SHORT")

    arcpy.CalculateField_management(fc_pt, 'conf', 'fff(!conf1!, !conf2! , !conf3! )  ', 'PYTHON_9.3',
                                    """
                                    def fff(x,y,z):
                                        if x != None and x != 0:
                                            return x
                                        if y != None and y != 0:
                                            return y
                                        if z != None  and z != 0:
                                            return z
                                    """)

    arcpy.CalculateField_management(fc_pt, 'md_conf', 'fff( !conf! ) ', 'PYTHON_9.3',
                                    """
                                    def fff(x):
                                        if x in [0,1,2]:
                                            return 2
                                        else:
                                            return 1
                                    """)

def process():
    id_imgs = ["080W_10S_070W_00N", "080W_20S_070W_10S", "070W_20S_060W_10S"]
    temp_folder = tempfile.mkdtemp()

    # 1. Descargar imagenes
    for id_img in id_imgs:
        arcpy.AddMessage("{}:\nInicio descarga: {}".format(id_img, datetime.datetime.now()))
        path_scene_alertDate = os.path.join(temp_folder, "alertDate{}.tif".format(id_img))
        path_scene_alert = os.path.join(temp_folder, "alert{}.tif".format(id_img))
        download_atd_sentinel2("alertDate", path_scene_alertDate, id_img)
        download_atd_sentinel2("alert", path_scene_alert, id_img)
    arcpy.AddMessage("\nTermina descarga")
    arcpy.AddMessage("Ruta de imagenes: {}" .format(temp_folder))

    # 2. Extraer treshold de fechas
    treshold_date, date_list = extract_date(fecha_inicio)
    arcpy.AddMessage("\nSe calcula el treshold_date de fechas: {}".format(treshold_date))

    path_defor_nuevo = "gpo_defor_sentinel2_{}".format(datetime.datetime.today().strftime("%Y_%m_%d_%H_%M_%S"))
    atd_nuevo = copy_feature(atd_plantilla, folder_salida, path_defor_nuevo)
    arcpy.DeleteRows_management(atd_nuevo)

    field_gridcode = "gridcode"
    if field_gridcode not in [x.name for x in arcpy.ListFields(atd_nuevo)]:
        arcpy.AddField_management(atd_nuevo, field_gridcode, "LONG")

    arcpy.AddMessage("Se Creo nuevo objeto: {}".format(os.path.join(folder_salida, path_defor_nuevo)))

    # 3. Filtro de alertas
    for id_img in id_imgs:
        arcpy.AddMessage("\n{}:\nInicio filtro de alertas: {}".format(id_img, datetime.datetime.now()))
        path_scene_alertDate = os.path.join(temp_folder, "alertDate{}.tif".format(id_img))
        filtered_image = filter_atd(path_scene_alertDate, treshold_date)
        arcpy.AddMessage("\tTermina filtro de alertas")

        defor_pol = raster_to_pol(filtered_image)
        arcpy.AddMessage("\tSe transformo a feature")

        defor = clip_to_anp(defor_pol)
        arcpy.AddMessage("\tSe corto por anps")

        append_feature(defor, atd_nuevo)
        arcpy.AddMessage("\tSe agrego a feature nuevo")
        arcpy.AddMessage("\tTermino la imagen: {}".format(id_img))
    
    update_fields(atd_nuevo, date_list)
    arcpy.AddMessage("\tSe actualizaron los campos")

    arcpy.AddMessage("\tActualizando exa")
    update_field_from_ref(fc=atd_nuevo,
                          ref_fc=path_exa,
                          ref_field=field_ref_exa, fc_field=field_fc_exa)
    arcpy.AddMessage("\tActualizando zonificacion")
    update_field_from_ref(fc=atd_nuevo,
                          ref_fc=path_zonif,
                          ref_field=field_ref_zonif, fc_field=field_fc_zonif)
    arcpy.AddMessage("\tActualizando codigo de anp")
    update_field_from_ref(fc=atd_nuevo,
                          ref_fc=path_anp,
                          ref_field=field_ref_anp, fc_field=field_fc_anp)
    arcpy.AddMessage("\tActualizando codigo de zi")
    update_field_from_ref(fc=atd_nuevo,
                          ref_fc=path_zi,
                          ref_field=field_ref_zi, fc_field=field_fc_zi)

    arcpy.AddMessage("\tActualizando TIPO BOSQUE")
    update_field_tipobosque(fc=atd_nuevo, ref_fc=gpo_defor_acum, ref_fc_2=path_nobosque2000)

    arcpy.AddMessage("\tActualizando superficie (hectareas)")
    update_field_sup(fc=atd_nuevo)

    # arcpy.AddMessage("\tActualizando Confiabilidad")
    # update_field_conf(fc=atd_nuevo, folder_img=temp_folder)

    arcpy.AddMessage("\tRUTA SALIDA: {}".format(path_defor_nuevo))
    arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

    arcpy.AddMessage("\n\nSE RECOMIENDA BORRAR LOS ARCHIVOS TEMPORALES")

def main():
    process()
    # atd_nuevo = r'E:\sernanp\proyectos\monitoreo\sentinel\gpo_defor_sentinel2_2022_02_28_10_58_51'
    # temp_folder = r'c:\users\ryali93\appdata\local\temp\tmpd0oihr'
    # arcpy.AddMessage("\tActualizando Confiabilidad")
    # update_field_conf(fc=atd_nuevo, folder_img=temp_folder)

if __name__ == '__main__':
    main()
