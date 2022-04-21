# -*- coding: utf-8 -*-
import arcpy
import os

arcpy.env.overwriteOutput = True

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BASE_DIR = os.path.dirname(r"E:/sernanp/data")
# BASE_DIR = ws = arcpy.GetParameterAsText(0)
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

TEMPLATES_DIR = os.path.join(SCRIPTS_DIR, "templates")
OUTPUT_DIR = os.path.join(SCRIPTS_DIR, "output")
SCRATCH = arcpy.env.scratchGDB

PATH_GDB = os.path.join(BASE_DIR, r"data/DB_TELEDETECCION_new.gdb")

gpo_zona_interes = os.path.join(PATH_GDB, r"fd_base\gpo_zpaa_monit")
gpo_deforestacion = os.path.join(PATH_GDB, r"fd_monitoreo\MonitDefor")
gpo_deforestacion_acum = os.path.join(PATH_GDB, r"fd_monitoreo\MonitDeforAcum")
gpo_atd = r"E:\sernanp\proyectos\atds\PNCB_ATD_UTM_04_31_R\gpo_defor_alerta_2021_0109_0131.shp"
