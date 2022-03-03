# -*- coding: utf-8 -*-
import os
import arcpy

arcpy.env.overwriteOutput = True

# template_v = r"E:\sernanp\proyectos\cobertura\templates\MODELO_A3_VERTICAL.mxd"
template_h = r"E:\sernanp\proyectos\cobertura\templates\MODELO_A3_HORIZONTAL_105.mxd"
# template_h = r"E:\sernanp\proyectos\cobertura\templates\MODELO_A3_HORIZONTAL_105_R.mxd"

capa_coberturas = "E:\sernanp\proyectos\cobertura\gpo_coberturas_v4.shp"
capa_provincias = r'E:\BASE_DATOS\BASE GIS ANA\Data_Peru_Geografico\Provincias.shp'
capa_anps = r'E:\sernanp\data\DB_TELEDETECCION.gdb\gpo_anp'

OUTPUT_DIR = r'E:\sernanp\proyectos\cobertura\mapas_2022'

# lista_anp = ['BP03', 'BP04', 'BP06', 'PN02', 'PN03', 'PN06', 'PN07', 'PN08', 'PN09', 'PN10', 'PN12', 'PN11', 'PN13',
#              'PN14', 'PN15', 'RC01', 'RC02', 'RC03', 'RC04', 'RC05', 'RC06', 'RC07', 'RC08', 'RC09', 'RC10', 'RN08',
#              'RN09', 'RN10', 'RN12', 'RN14', 'SH03', 'SN06', 'SN07', 'SN08', 'SN09', 'ZR03', 'ZR07', 'ZR11']

# Leyenda a la izquierda
# lista_anp = ['BP03', 'BP04', 'BP06', 'PN03', 'PN07', 'PN08', 'PN09', 'PN10', 'PN13',
#              'PN15', 'RC01', 'RC02', 'RC04', 'RC06', 'RC07', 'RC08', 'RC10',
#              'RN09', 'RN12', 'RN14', 'SN06', 'SN07', 'SN09', 'ZR03', 'ZR07']
# # Leyenda a la derecha
# lista_anp = ['PN12', 'PN14', 'RC03', 'RC09', 'RN08', 'RN10', 'SH03', 'SN08', 'ZR11']

# # Mas zoom (acercar) 0.60
# lista_anp = ['PN02']
#
# # Menos zoom (alejar un poco) 1.20
# lista_anp = ['PN11']
#
# # Exportar mxd
lista_anp = ['PN06', 'RC05']

# Leer plantilla
def read_templates():
    mxd = template_h
    mxd = arcpy.mapping.MapDocument(mxd)
    df_capas = arcpy.mapping.ListDataFrames(mxd, "Capas")[0]
    return mxd, df_capas

def crear_mapa(anp_codi):
    lyr_coberturas = "coberturas"
    lyr_anp = "gpo_anp"
    mxd, df_capas = read_templates()
    sql = "{} = '{}'".format("ANP_CODI", anp_codi)
    print(sql)

    # Extraer prov y dep
    mfl_anp = arcpy.MakeFeatureLayer_management(capa_anps, "mfl_zi", sql)
    mfl_prov = arcpy.MakeFeatureLayer_management(capa_provincias, "mfl_prov")
    arcpy.SelectLayerByLocation_management(mfl_prov, "INTERSECT", mfl_anp, "#", 'NEW_SELECTION')

    prov_dep = [[x[0], x[1]] for x in arcpy.da.SearchCursor(mfl_prov, ["PRONOM98", "DEPNOM"])]
    provincias = [x[0] for x in prov_dep][0]
    departamentos = [x[1] for x in prov_dep][0]
    anp_nombre = [u"{} {}".format(x[0], x[1]) for x in arcpy.da.SearchCursor(mfl_anp, ["anp_cate", "anp_nomb"], sql)][0]

    escala = ""
    for i in arcpy.mapping.ListLayers(mxd):
        if i.name == lyr_coberturas:
            i.definitionQuery = "{} = '{}'".format("anp_codi", anp_codi)
            arcpy.RefreshActiveView()
        if i.name == lyr_anp:
            i.definitionQuery = "{} = '{}'".format("anp_codi", anp_codi)
            df_capas.extent = i.getSelectedExtent()
            df_capas.scale = int(round(df_capas.scale*1.00, -3))
            escala = df_capas.scale
            arcpy.RefreshActiveView()

    arcpy.RefreshActiveView()
    # Cambiar elementos de texto
    ElementoTexto_MAPA_NOMBRE = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "MAPA_NOMBRE")[0]
    ElementoTexto_ANP_CODI = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "ANP_CODI")[0]
    ElementoTexto_DEPARTAMENTO = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "DEPARTAMENTO")[0]
    ElementoTexto_PROVINCIA = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "PROVINCIA")[0]
    ElementoTexto_ESCALA = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT", "ESCALA")[0]

    ElementoTexto_MAPA_NOMBRE.text = anp_nombre
    ElementoTexto_ANP_CODI.text = anp_codi
    ElementoTexto_DEPARTAMENTO.text = departamentos
    ElementoTexto_PROVINCIA.text = provincias
    ElementoTexto_ESCALA.text = "1:{}".format(escala)

    arcpy.RefreshActiveView()

    # mxd.saveACopy(r'E:\sernanp\proyectos\mapas\{}_{}.mxd'.format(codigo_zi, date_satimg_current[-1].strftime("%Y%m%d")))
    mxd.saveACopy(r'E:\sernanp\proyectos\cobertura\mapas_2022_mxd\{}.mxd'.format(anp_codi))

    arcpy.mapping.ExportToJPEG(mxd, os.path.join(OUTPUT_DIR, "{}.jpg".format(anp_codi)))
    # arcpy.mapping.ExportToPDF(mxd, os.path.join(OUTPUT_DIR, "{}.pdf".format(anp_codi)))
    del mxd
    del df_capas


def process():
    for anp in lista_anp:
        crear_mapa(anp)

def main():
    process()

if __name__ == "__main__":
    main()
