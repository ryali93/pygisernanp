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


# ---------------------------------------------------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------------------------------------------------
# SCRATCH = arcpy.env.scratchGDB
# folder_salida = arcpy.GetParameterAsText(1)
# fecha_inicio = arcpy.GetParameterAsText(2)
# atd_plantilla = arcpy.GetParameterAsText(3)
fecha_inicio = '01/01/2022'
folder_salida = r'E:\sernanp\proyectos\monitoreo\pncb'
gdb_template = r'E:\sernanp\proyectos\monitoreo\gdb_monit_template.gdb'

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

def download_atd(path):
    url_download = u"http://geobosques.minam.gob.pe/geobosque/descargas_geobosque/alerta/espaciales/Alertas_PNCB_raster_2022.zip"
    response = requests.get(url_download)
    data = response.content
    with open(path, 'wb') as s:
        s.write(data)

def unzip_atd(path, output):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(output)

def raster_to_pol(folder_image):
    atd_file = [os.path.join(folder_image, x) for x in os.listdir(folder_image) if x.endswith(".tif")][0]
    polygon = arcpy.RasterToPolygon_conversion(atd_file, "in_memory\\polygon", 'NO_SIMPLIFY', 'Fecha')
    return polygon

def copy_feature(feature, folder, name):
    if arcpy.Exists(os.path.join(folder, "ATD_Geobosque.gdb")) == False:
        arcpy.CreateFileGDB_management(folder, "ATD_Geobosque", "10.0")
    name_fc = os.path.join(folder, "ATD_Geobosque.gdb", name)
    arcpy.CopyFeatures_management(feature, name_fc)
    return name_fc

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

def update_field_conf(fc, ref_fc):
    # Por Cercania a la Deforestacion Acumulada
    fc_field = "md_conf"
    fc_mfl = arcpy.MakeFeatureLayer_management(fc, "fc_mfl")
    defor_acum = arcpy.MakeFeatureLayer_management(ref_fc, "defor_acum")
    arcpy.CalculateField_management(fc, fc_field, '2', 'PYTHON_9.3', '#')
    arcpy.SelectLayerByLocation_management(fc_mfl, 'INTERSECT', defor_acum, '1 Kilometers', 'NEW_SELECTION', 'NOT_INVERT')
    list_oid = [str(x[0]) for x in arcpy.da.SearchCursor(fc_mfl, ["OBJECTID"])]
    arcpy.SelectLayerByAttribute_management(fc_mfl, 'CLEAR_SELECTION')
    sql = "OBJECTID in ({})".format(','.join(list_oid))
    with arcpy.da.UpdateCursor(fc, [fc_field], sql) as cursor:
        for x in cursor:
            x[0] = 1
            cursor.updateRow(x)
    # Por zonificacion
    sql = "{} = 2".format(fc_field)
    with arcpy.da.UpdateCursor(fc, [fc_field, "md_zonif"], sql) as cursor:
        for x in cursor:
            if x[1] in ["AD", "UE"]:
                x[0] = 1
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

def atd_evaluate(feature):
    # Multipart to SinglePart
    start = datetime.datetime.strptime(fecha_inicio, "%d/%m/%Y")
    end = datetime.datetime.strptime("31/12/2022", "%d/%m/%Y")
    lista_fechas = [(start + datetime.timedelta(days=x)).strftime("%d/%m/%Y") for x in range(0, (end - start).days)]
    lista_fechas = ["{}/{}/{}".format(int(x.split("/")[0]), x.split("/")[1], x.split("/")[2]) for x in lista_fechas]

    # Listado de fechas
    sql = "{} IN ('{}')".format("Fecha", "','".join(lista_fechas))
    # Filtrar por fechas
    mfl_pol = arcpy.MakeFeatureLayer_management(feature, 'mfl_atd', sql)
    anp_mfl = arcpy.MakeFeatureLayer_management(path_anp, "anp_mfl")
    # Cortar por ANP
    atd_clip = arcpy.Clip_analysis(mfl_pol, anp_mfl, "in_memory\\atd_clip", '#')
    arcpy.AddField_management(atd_clip, "md_fecimg", "DATE")
    arcpy.AddField_management(atd_clip, "anp_codi", "STRING")

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

    min_fecha = min(lista_fechas_nombre).strftime("%Y%m%d")
    max_fecha = max(lista_fechas_nombre).strftime("%Y%m%d")

    path_salida = 'gpo_defor_alerta_{}_{}'.format(min_fecha, max_fecha)
    atd_nuevo = copy_feature(atd_plantilla, folder_salida, path_salida)
    arcpy.DeleteRows_management(atd_nuevo)

    arcpy.Append_management(atd_clip, atd_nuevo, "NO_TEST")

    return atd_nuevo


def process():
    # 1. Descargar imagenes
    arcpy.AddMessage("\nInicia descarga: {}".format(datetime.datetime.now()))
    temp_folder = tempfile.mkdtemp()
    path_zip = os.path.join(temp_folder, "atd.zip")
    path_folder = os.path.join(temp_folder, "atd_fecha")
    download_atd(path_zip)
    unzip_atd(path_zip, path_folder)
    arcpy.AddMessage("\nTermina descarga")
    arcpy.AddMessage("Ruta de imagenes: {}".format(path_folder))

    # 2. Se transforma a poligonos
    polygons = raster_to_pol(path_folder)
    arcpy.AddMessage("\nSe transformo a feature")

    # 3. Se evaluan los poligonos
    arcpy.AddMessage("\nSe esta evaluando el ATD")
    polygons = atd_evaluate(polygons)
    arcpy.AddMessage("Se termino la evaluacion del ATD")

    # 4. Actualizar campos importantes
    arcpy.AddMessage("\nActualizando campos")
    arcpy.AddMessage("\tSe termino la evaluacion del ATD")

    # polygons = r'E:\sernanp\proyectos\monitoreo\gdb_monit_template.gdb\MonitDefor_2021'
    # polygons = r'E:\sernanp\proyectos\monitoreo\pncb\ATD_Geobosque.gdb\gpo_defor_alerta_20220105_20220130'

    arcpy.AddMessage("\tActualizando exa")
    update_field_from_ref(fc=polygons,
                          ref_fc=path_exa,
                          ref_field=field_ref_exa, fc_field=field_fc_exa)
    arcpy.AddMessage("\tActualizando zonificacion")
    update_field_from_ref(fc=polygons,
                          ref_fc=path_zonif,
                          ref_field=field_ref_zonif, fc_field=field_fc_zonif)
    arcpy.AddMessage("\tActualizando codigo de anp")
    update_field_from_ref(fc=polygons,
                          ref_fc=path_anp,
                          ref_field=field_ref_anp, fc_field=field_fc_anp)
    arcpy.AddMessage("\tActualizando codigo de zi")
    update_field_from_ref(fc=polygons,
                          ref_fc=path_zi,
                          ref_field=field_ref_zi, fc_field=field_fc_zi)

    arcpy.AddMessage("\tActualizando CONFIABILIDAD")
    update_field_conf(fc=polygons, ref_fc=gpo_defor_acum)

    arcpy.AddMessage("\tActualizando TIPO BOSQUE")
    update_field_tipobosque(fc=polygons, ref_fc=gpo_defor_acum, ref_fc_2 = path_nobosque2000)

    arcpy.AddMessage("\tActualizando superficie (hectareas)")
    update_field_sup(fc=polygons)

    arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

def main():
    process()

if __name__ == '__main__':
    main()
