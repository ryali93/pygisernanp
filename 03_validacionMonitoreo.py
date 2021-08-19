#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arcpy
import os

arcpy.env.overwriteOutput = True

# ---------------------------------------------------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------------------------------------------------
list_fields = ['objectid', 'globalid', 'anp_codi', 'md_fuente', 'zi_codi', 'md_clase', 'md_mesrep', 'md_fecrev', 'md_fecimg', 'md_editor', 'md_sup', 'shape']

def verify_fields(feature, mes_reporte):
    # No tener datos incongruentes en campos
    sql = "{} = {}".format("md_mesrep", mes_reporte)
    with arcpy.da.SearchCursor(feature, list_fields, sql) as cursors:
        for x in cursors:
            for field_idx in range(0, len(list_fields)):
                if x[field_idx] == None:
                    print("Revisar los datos del campo {}".format(list_fields[field_idx]))


def update_revcam(feature, mes_reporte):
    # actualizar campo revcam a "No"
    sql = "{} = {}".format("md_mesrep", mes_reporte)
    with arcpy.da.UpdateCursor(feature, ["md_revcam"], sql) as cursoru:
        for y in cursoru:
            y[0] = 2
            cursoru.updateRow(y)

def verify_field_from_feature(fc_to_u, field_to_update, fc_source, field_source, mes_reporte):
    sql = "{} = {}".format("md_mesrep", mes_reporte)
    fc_source_mfl = arcpy.MakeFeatureLayer_management(fc_source, "fc_mfl")

    oid_list = [x[0] for x in arcpy.da.SearchCursor(fc_to_u, ["OID@"], sql) if len(x) > 0]

    if len(oid_list) > 0:
        for oid in oid_list:
            sql_oid = "OBJECTID = {}".format(oid)
            arcpy.AddMessage(sql_oid)
            fc_to_u_mfl = arcpy.MakeFeatureLayer_management(fc_to_u, "fc_to_u_mfl", sql_oid)
            defor_select = arcpy.SelectLayerByLocation_management(fc_source_mfl, 'INTERSECT', fc_to_u_mfl)
            with arcpy.da.UpdateCursor(fc_to_u, [field_to_update], sql_oid) as cursor:
                for x in cursor:
                    x[0] = [y[0] for y in arcpy.da.SearchCursor(defor_select, [field_source])][0]
                    cursor.updateRow(x)
            arcpy.SelectLayerByAttribute_management(fc_source_mfl, "CLEAR_SELECTION")
    else:
        arcpy.AddMessage("No se tienen registros en el reporte de mes {}".format(mes_reporte))


def main():
    fc_to_update = arcpy.GetParameterAsText(0)
    field_to_update = arcpy.GetParameterAsText(1)
    fc_source = arcpy.GetParameterAsText(2)
    field_source = arcpy.GetParameterAsText(3)
    mes_reporte = arcpy.GetParameterAsText(4)

    # fc_to_update = r"E:\sernanp\data\backup_2021_07_13.gdb\MonitDefor"
    # field_to_update = "anp_codi"
    # fc_source = r"E:\sernanp\data\DB_TELEDETECCION_new.gdb\gpo_zpaa_monit"
    # field_source = "anp_codi"
    # mes_reporte = "2021071"
    update_revcam(fc_to_update, mes_reporte)
    verify_field_from_feature(fc_to_update, field_to_update, fc_source, field_source, mes_reporte)
    # verify_fields(gpo_deforestacion)

if __name__ == '__main__':
    main()
