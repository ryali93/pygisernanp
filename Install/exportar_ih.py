import arcpy
import os
import json

arcpy.env.overwriteOutput = True
SCRATCH_GDB = arcpy.env.scratchGDB
SCRATCH_Folder = arcpy.env.scratchFolder

HFp = r'E:\sernanp\proyectos\bdg\HF_Peru_2018_GHF.tif'
anp = r'E:\sernanp\data\DB_TELEDETECCION_new.gdb\gpo_anp'
gdb = r'E:\sernanp\proyectos\bdg\anp\indice_humano.gdb'
ih = r'E:\sernanp\proyectos\bdg\anp\indice_humano.gdb\ih'

list_anp_codi = [x[0] for x in arcpy.da.SearchCursor(anp, ["anp_codi"])]
list_anp_codi_error = []

anp_18s = arcpy.Project_management(anp, os.path.join(gdb, "gpo_anp_18s"), arcpy.SpatialReference(32718))

for anp_codi in list_anp_codi:
    print(anp_codi)
    # anp_codi = "RN08"
    try:
        mfl = arcpy.MakeFeatureLayer_management(anp_18s, "mfl_anp", "anp_codi = '{}'".format(anp_codi))
        mfl_buffer = arcpy.Buffer_analysis(mfl, os.path.join(SCRATCH_GDB, "mfl_buffer"), "5 Kilometers")
        ext_ = arcpy.Describe(mfl_buffer).extent
        j = json.loads(ext_.JSON)
        ext_n = "{} {} {} {}".format(j["xmin"], j["ymin"], j["xmax"], j["ymax"])
        rec_v = arcpy.sa.RemapRange([[0,0.2,2],[0.2,0.4,4],[0.4,0.6,6],[0.6,0.8,8],[0.8,1,10],[1,2.5,25],[2.5,5,50],[5,15,150],[15,30,300],[30,50,500]])
        hf_clip = arcpy.Clip_management(HFp, ext_n, os.path.join(gdb, "hf_clip"), mfl_buffer, '#', 'ClippingGeometry', 'NO_MAINTAIN_EXTENT')
        hf_reclass = arcpy.sa.Reclassify(hf_clip, 'Value', rec_v, "DATA")
        hf_reclass_pol = arcpy.RasterToPolygon_conversion(hf_reclass, os.path.join(gdb, "hf_reclass_pol"), 'NO_SIMPLIFY', 'Value', 'MULTIPLE_OUTER_PART', '#')
        arcpy.AddField_management(hf_reclass_pol, "anp_codi", "TEXT")
        with arcpy.da.UpdateCursor(hf_reclass_pol, ["anp_codi"]) as cursor:
            for x in cursor:
                x[0] = anp_codi
                cursor.updateRow(x)
        arcpy.Append_management(hf_reclass_pol, ih, "NO_TEST")
    except:
        list_anp_codi_error.append(anp_codi)

print(list_anp_codi_error)