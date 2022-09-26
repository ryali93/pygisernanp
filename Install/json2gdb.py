import arcpy
import os
arcpy.env.workspace = "c:/data"
arcpy.JSONToFeatures_conversion("myjsonfeatures.json", os.path.join("outgdb.gdb", "myfeatures"))

r'E:\sernanp\proyectos\catalogo_objetos\gdb.gdb'

