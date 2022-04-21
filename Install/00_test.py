import arcpy

arcpy.env.overwriteOutput = True

fc1 = r'E:\sernanp\proyectos\monitoreo\2021_07\gpo_def_geob_20210311_20210616_RMYS.shp'
fc2 = r'E:\sernanp\data\DB_TELEDETECCION_new.gdb\gpo_zpaa_monit'
fc3 = r'E:\sernanp\data\gpo_exa.shp'

mfl_fc = arcpy.MakeFeatureLayer_management(fc1, "mfl_fc")
zpaa = arcpy.MakeFeatureLayer_management(fc2, "mfl_zpaa")
exa = arcpy.MakeFeatureLayer_management(fc3, "mfl_exa")

def update_fields(fc1):
    # sql1 = "'{}' = '{}'".format("md_editor", "RYALI")
    sql1 = "1=1"
    list_oid = [x[0] for x in arcpy.da.SearchCursor("mfl_fc", ["OID@"], sql1)]
    for oid in list_oid:
        sql = "{} = {}".format("FID", oid)
        print(sql)
        mfl_def = arcpy.MakeFeatureLayer_management(fc1, "mfl_def", sql)
        sel_zpaa = arcpy.SelectLayerByLocation_management(zpaa, "INTERSECT", mfl_def, "#", "NEW_SELECTION")
        sel_exa = arcpy.SelectLayerByLocation_management(exa, "INTERSECT", mfl_def, "#", "NEW_SELECTION")

        zpaa_data = [m[0] for m in arcpy.da.SearchCursor(sel_zpaa, ["zi_codi"])][0]
        exa_query = [m[0] for m in arcpy.da.SearchCursor(sel_exa, ["g_cofi"])]
        if len(exa_query) > 0:
            exa_data = exa_query[0]
        else:
            exa_data = ""

        # print(zpaa_data)
        # print(exa_data)

        with arcpy.da.UpdateCursor(fc1, ["zi_codi", "md_exa", "md_revcam"], sql) as cursor:
            for x in cursor:
                x[0] = zpaa_data
                x[1] = exa_data
                x[2] = 2
                cursor.updateRow(x)
        arcpy.SelectLayerByAttribute_management(zpaa, "CLEAR_SELECTION")
        arcpy.SelectLayerByAttribute_management(exa, "CLEAR_SELECTION")

def main():
    update_fields(fc1)

if __name__ == '__main__':
    main()

