# -*- coding: utf-8 -*-
import os
import tempfile
import datetime
import requests
import pandas as pd
import arcpy
import glob

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------------------------------------------------
arcpy.env.overwriteOutput = True

SCRATCH = arcpy.env.scratchGDB
SCRATCH_FOLDER = arcpy.env.scratchFolder

min_fecha = arcpy.GetParameterAsText(0)
max_fecha = arcpy.GetParameterAsText(1)
folder_salida = arcpy.GetParameterAsText(2)
gdb_template = arcpy.GetParameterAsText(3)
# min_fecha = "2022-09-15"
# max_fecha = "2022-09-30"
# folder_salida = r'F:\sernanp\proyectos\monitoreo\gfw'
# gdb_template = r'F:\sernanp\data\gdb_monit_template.gdb'

atd_plantilla = os.path.join(gdb_template, 'MonitDefor')

anp_dic = {
    "BP06": "662bd81f-680f-14fd-5822-27023fe693e7",     # 01: BP Alto Mayo
    "BP04": "ee00b769-fe76-f362-dc27-e6beff3fb67a",     # 02: BP San Matias - San Carlos
    "PN11": "2e3b97ce-796e-6c9e-b404-4fc767da235d",     # 03: PN Alto Purus
    "PN08": "f97d0ad4-d751-bd5a-03f3-5220742a3fe4",     # 04: PN Bahuaja Sonene
    "PN12": "21f39414-e640-7a2e-0cd3-65ff01cface7",     # 05: PN Ichigkat Muja-Cordillera del Condor
    "PN13": "2700ea2e-c48b-beaf-b69d-03b6e7bb6969",     # 06: PN Gueppi-Sekime
    "PN07": "a3de6fc9-22c6-10a0-41db-661024244210",     # 07: RN Yanachaga Chemillen
    "PN09": "e6bde93e-7229-5c59-ebb3-d301bb8743e1",     # 08: PN Cordillera Azul
    "PN02": "63dbbe19-91f4-74bf-2048-03d082ad1876",     # 09: PN Tingo Maria
    "PN14": "bc0d1959-a1d0-0d57-d101-c90197872d11",     # 10: PN Sierra del Divisor
    "PN10": "1166d8b6-f708-9611-075b-2b0bab0ff500",     # 11: PN Otishi
    "PN03": "9a6a885b-acb0-33c3-404d-56ed62e39c8f",     # 12: PN Manu
    "PN15": "477a77c1-4873-e94a-4ef2-6ce2c9c73bdd",     # 13: PN Yaguas
    "RC05": "6ee037c6-57b0-d366-4516-b3b042ba7449",     # 14: RC Machiguenga
    "RC06": "747891c0-e1f8-6e31-3ccc-c125888aa939",     # 15: RC Purus
    "RC07": "91f53f3e-038a-8d3d-f866-acd6b3c83213",     # 16: RC Tuntanain
    "RC08": "e10eee00-158e-e4db-8fee-0ff9d81c48d5",     # 17: RC Chayu Nain
    "RC10": "95c8aa53-cd6e-2f63-0348-b6d6a143d5c4",     # 18: RC Huimeki
    "RC09": "21baf777-217a-6a02-a5d0-8b8435f04e88",     # 19: RC Airo Pai
    "RC01": "4f22b3d9-2f7f-c852-fea2-fb7ff794b9fd",     # 20: RC Yanesha
    "RC02": "8b1ec3a4-4da7-8e32-e487-8773a38bc12e",     # 21: RC El Sira
    "RC04": "3f0509e8-d538-59de-07a7-2287cb244255",     # 22: RC Ashaninka
    "RC03": "47ae9ebc-4289-9e54-253f-44506d1bee07",     # 23: RC Amarakaeri
    "RN08": "b3e57707-1a52-c4ed-01ef-c0a10ba6bbf9",     # 24: PN Pacaya Samiria
    "RN09": "ad153b1a-43c2-d66a-4ede-d33aefbd918a",     # 25: RN Tambopata
    "RN12": "fe6cfe79-859b-855c-6bb2-513d036dbfc7",     # 26: RN Matses
    "RN14": "b62b8477-5708-ddb7-9df1-d93e9ed40115",     # 27: RN Pucacuro
    "RN10": "298a50ac-b29b-faf9-8949-2988dfc42fbd",     # 28: RN Allpahuayo-Mishana
    "SN06": "5cda4026-c55e-c2d5-3bd5-ea10baaced00",     # 29: SN Megantoni
    "SN09": "0d552ec6-e312-ffd0-41d0-558f3f9dcaf0",     # 30: SN Cordillera Colan
    "ZR03": "f0abc8b5-aabd-3444-ffe2-586646853714",     # 31: ZR Santiago Comaina
    "ZR11": "9ad98ea9-45df-ccc8-440a-29a3412330c3",     # 32: ZR Rio Nieva
    "ZR07": "cd4a3ec0-3b12-37ad-14fa-2c32d5a6b9f0",     # 33: ZR Sierra del Divisor
    "PN06": "ed9c04d9-b0af-7670-8ea3-60de3679ad5e",     # 34: PN Rio Abiseo
    "SN07": "81872a6f-fe17-4bf6-999e-79b1378055c7",     # 35: SN Pampa Hermosa
    "SN08": "c4203a8a-80da-d325-6481-65a85912b16d",     # 36: SN Tabaconas Namballe
    "BP03": "02115bf6-8ef9-acfe-8e06-0a78c6d65be1",     # 37: BP Pui Pui
    "SH03": "965f1e9d-8a22-464f-c97c-487059f44340"      # 38: SH MachuPicchu
}

# ---------------------------------------------------------------------------------------------------------------------
# FUNCIONES
# ---------------------------------------------------------------------------------------------------------------------
def reorder_date(fecha):
    f = fecha.split("/")
    return "-".join([f[2], f[1].zfill(2), f[0].zfill(2)])

def copy_feature(feature, folder, name):
    if arcpy.Exists(os.path.join(folder, "GFW.gdb")) == False:
        arcpy.CreateFileGDB_management(folder, "GFW", "10.0")
    name_fc = os.path.join(folder, "GFW.gdb", name)
    arcpy.CopyFeatures_management(feature, name_fc)
    return name_fc

def create_tmp_feature(sr):
    fc = arcpy.CreateFeatureclass_management(SCRATCH_FOLDER, "tmp2.shp", "POLYGON", "#", "#", "#", arcpy.SpatialReference(sr))
    return fc

def get_data(anp, anp_codi, folder, min_fecha, max_fecha):
    url = "https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts/latest/download/csv?sql=" \
        "SELECT latitude, longitude, gfw_integrated_alerts__date " \
        "FROM data WHERE " \
        "gfw_integrated_alerts__date >= '{}' AND gfw_integrated_alerts__date <= '{}' " \
        "AND gfw_integrated_alerts__confidence = 'highest'&geostore_id={}".format(min_fecha, max_fecha, anp)

    response = requests.get(url)
    data = response.text
    path_file = os.path.join(folder, anp_codi+".csv")
    if len(data) > 0:
        if data[1:17] == '"status":"error"':
            arcpy.AddMessage("\t\t\tERROR CON EL AREA")
        else:
            with open(path_file, 'w') as f:
                    f.write(data)
            f.close()

def create_polygon(df):
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.dropna()

    tmp = create_tmp_feature(4326)
    arcpy.AddField_management(tmp, "md_fecimg", "DATE")

    cursor = arcpy.da.InsertCursor(tmp, ['SHAPE@', "md_fecimg"])
    for i in range(df.shape[0]):
        x = float(df.iloc[i, 1])
        y = float(df.iloc[i, 0])
        md_fecimg = df.iloc[i, 2]
        w_m = 0.00005 # 10
        h_m = 0.00005 # 10

        array = arcpy.Array([arcpy.Point(x - w_m, y + h_m), 
                                arcpy.Point(x + w_m, y + h_m),
                                arcpy.Point(x + w_m, y - h_m),
                                arcpy.Point(x - w_m, y - h_m)
                            ])
        polygon = arcpy.Polygon(array, arcpy.SpatialReference(4326))
        # polygon_proj = polygon.projectAs(arcpy.SpatialReference(32718))
        cursor.insertRow([polygon, md_fecimg])
    del cursor

    return tmp

def update_data(tmp):
    tmp2 = arcpy.Dissolve_management(tmp, "in_memory\\dissol", ['md_fecimg'], '#', 'MULTI_PART', 'DISSOLVE_LINES')
    tmp3 = arcpy.MultipartToSinglepart_management(tmp2, "in_memory\\mp2sp")
    return tmp3

def generar_objeto(data, min_fecha, max_fecha):
    # fecha = datetime.date.today().strftime("%Y_%m_%d_%H_%M_%S")
    fecha_min = min_fecha.replace("-","")
    fecha_max = max_fecha.replace("-","")
    path_salida = 'gpo_gfw_{}_{}'.format(fecha_min, fecha_max)
    atd_nuevo = copy_feature(atd_plantilla, folder_salida, path_salida)
    arcpy.DeleteRows_management(atd_nuevo)

    arcpy.Append_management(data, atd_nuevo, "NO_TEST")
    return atd_nuevo

def actualizar_campos(data, anp_codi):
    with arcpy.da.UpdateCursor(data, ["anp_codi"]) as cursor:
        for x in cursor:
            x[0] = anp_codi
            cursor.updateRow(x)

def process():
    arcpy.AddMessage("\nInicio de proceso: {}".format(datetime.datetime.now()))
    fechamin = reorder_date(min_fecha)
    fechamax = reorder_date(max_fecha)
    temp_folder = tempfile.mkdtemp()
    arcpy.AddMessage("Se ha creado una carpeta temporal en la siguiente ruta: {}".format(temp_folder))

    arcpy.AddMessage("\tPaso 1")
    for anp_codi in anp_dic.keys():
        arcpy.AddMessage("\t\tDescargando datos para {}".format(anp_codi))
        # 1. Obtener la data de GFW a traves del API
        get_data(anp_dic[anp_codi], anp_codi, temp_folder, fechamin, fechamax)
    # Leer todos los csv de la carpeta temporal
    all_files = glob.glob(os.path.join(temp_folder , "*.csv"))
    li = []
    for filename in all_files:
        df = pd.read_csv(filename, index_col=None, header=0)
        li.append(df)
    df = pd.concat(li, axis=0, ignore_index=True)
    
    # 2. Crear poligonos a partir de coordenadas
    arcpy.AddMessage("\tPaso 2")
    tmp = create_polygon(df)
    total_tmp = update_data(tmp)
    # 3. Dar el formato de defor segun metadatos
    arcpy.AddMessage("\tPaso 3")
    generar_objeto(total_tmp, fechamin, fechamax)

    arcpy.AddMessage("\tRUTA SALIDA")
    arcpy.AddMessage("Fin: {}".format(datetime.datetime.now()))

    arcpy.AddMessage("\n\nSE RECOMIENDA BORRAR LOS ARCHIVOS TEMPORALES")

def main():
    process()

if __name__ == '__main__':
    main()
