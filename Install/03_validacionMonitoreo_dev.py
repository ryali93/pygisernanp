#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arcpy
import os
import datetime

arcpy.env.overwriteOutput = True

# ---------------------------------------------------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------------------------------------------------
# feature = arcpy.GetParameterAsText(0)
# gdb_template = arcpy.GetParameterAsText(1)

feature = r"E:\sernanp\data\backup_2022_04_04.gdb\MonitDefor"
gdb_template = r'E:\sernanp\proyectos\monitoreo\gdb_monit_template.gdb'

oid = "FID" if feature.endswith(".shp") else "OBJECTID"

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

def update_field_from_ref(fc, fc_field, ref_fc, ref_field):
    fc_pt = arcpy.FeatureToPoint_management(fc, "in_memory\\out_pt", "INSIDE")
    out_pt = arcpy.SpatialJoin_analysis(fc_pt, ref_fc, "in_memory\\out_pt2", "JOIN_ONE_TO_ONE", "KEEP_ALL")
    if fc_field == ref_field:
        ref_field = ref_field + "_1"
    field_eq = {x[0]:x[1] for x in arcpy.da.SearchCursor(out_pt, ["ORIG_FID", ref_field])}
    with arcpy.da.UpdateCursor(fc, [oid, fc_field]) as cursor:
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
    list_oid = [str(x[0]) for x in arcpy.da.SearchCursor(fc_mfl, [oid])]
    sql = "{} in ({})".format(oid, ','.join(list_oid))
    with arcpy.da.UpdateCursor(fc, [fc_field], sql) as cursor:
        for x in cursor:
            x[0] = 2
            cursor.updateRow(x)

def update_field_conf(fc, ref_fc):
    # Por Cercania a la Deforestacion Acumulada
    fc_field = "md_conf"
    fc_mfl = arcpy.MakeFeatureLayer_management(fc, "fc_mfl")
    defor_acum = arcpy.MakeFeatureLayer_management(ref_fc, "defor_acum")
    arcpy.CalculateField_management(fc, fc_field, '2', 'PYTHON_9.3', '#')
    arcpy.SelectLayerByLocation_management(fc_mfl, 'INTERSECT', defor_acum, '1 Kilometers', 'NEW_SELECTION', 'NOT_INVERT')
    list_oid = [str(x[0]) for x in arcpy.da.SearchCursor(fc_mfl, [oid])]
    arcpy.SelectLayerByAttribute_management(fc_mfl, 'CLEAR_SELECTION')
    sql = "{} in ({})".format(oid, ','.join(list_oid))
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

def update_field_sup(fc):
    exp = "!SHAPE.AREA@HECTARES!"
    arcpy.CalculateField_management(fc, "md_sup", exp, "PYTHON_9.3")

def main():
    arcpy.AddMessage("\nInicia de actualizacion")

    arcpy.AddMessage("\tActualizando exa")
    update_field_from_ref(fc=feature,
                          ref_fc=path_exa,
                          ref_field=field_ref_exa, fc_field=field_fc_exa)
    arcpy.AddMessage("\tActualizando zonificacion")
    update_field_from_ref(fc=feature,
                          ref_fc=path_zonif,
                          ref_field=field_ref_zonif, fc_field=field_fc_zonif)
    arcpy.AddMessage("\tActualizando codigo de anp")
    update_field_from_ref(fc=feature,
                          ref_fc=path_anp,
                          ref_field=field_ref_anp, fc_field=field_fc_anp)
    arcpy.AddMessage("\tActualizando codigo de zi")
    update_field_from_ref(fc=feature,
                          ref_fc=path_zi,
                          ref_field=field_ref_zi, fc_field=field_fc_zi)

    arcpy.AddMessage("\tActualizando TIPO BOSQUE")
    update_field_tipobosque(fc=feature, ref_fc=gpo_defor_acum, ref_fc_2=path_nobosque2000)

    arcpy.AddMessage("\tActualizando superficie (hectareas)")
    update_field_sup(fc=feature)

    arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

if __name__ == '__main__':
    main()
