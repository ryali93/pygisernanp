import arcpy
import os
import json
import requests

arcpy.env.overwriteOutput = True

main_url = "https://services6.arcgis.com/DWc6sLYN7TTrbI6g/ArcGIS/rest/services/DEFOR_2021_05_25_gdb/FeatureServer/"
fields_monitdefor = ['anp_codi','md_fuente','zi_codi','md_clase','md_mesrep','md_fecrev','md_fecimg','md_editor','md_sup','md_exa','md_revcam','md_feccam','md_causa','md_actom','md_medver','md_obs']
fields_monitdeforacum = ['anp_codi','md_fuente','zi_codi','md_clase','md_anno','md_fecrev','md_fecimg','md_sup','md_exa','md_revcam','md_feccam','md_causa','md_actom','md_medver']
SCRATCH = arcpy.env.scratchGDB
SCRATCH_FOLDER = arcpy.env.scratchFolder

def get_service(layer):
    '''
    :param layer: 0=MonitDeforAcum, 1=MonitDefor
    :return:
    '''
    services = {
        "query_url": os.path.join(main_url, layer + "/query"),
        "add_features_url": os.path.join(main_url, layer  + "/addFeatures"),
        "delete_features_url": os.path.join(main_url, layer + "/deleteFeatures")
    }
    return services

def get_updated_data(url, query):
    sql = query
    r = requests.post(
        url,
        data={
            'where': '{}'.format(sql),
            'outFields': "*",
            'f': 'pjson'
        }
    )
    res = json.loads(r.text)
    return res

def proccess():
    # fc = arcpy.GetParameterAsText(0)
    fc = r"E:\sernanp\data\backup_2021_07_13.gdb\MonitDefor"
    code_feature = "1" if fc.endswith("MonitDefor") else "0"
    services = get_service(code_feature) # MonitDefor
    fields = fields_monitdefor if fc.endswith("MonitDefor") else fields_monitdeforacum

    url_query = services["query_url"]

    # get globalid
    sql = "md_revcam = 1"
    arcpy.AddMessage(sql)
    data_json = get_updated_data(url_query, sql)
    data_json_1 = json.dumps(data_json)
    path_json = os.path.join(SCRATCH_FOLDER, "data_json.json")
    with open(path_json, "w") as f:
        f.write(data_json_1)
    f.close()
    data_fc_1 = arcpy.JSONToFeatures_conversion(path_json, "in_memory\\data_json_1")

    list_data = [x for x in arcpy.da.SearchCursor(data_fc_1, fields)]
    arcpy.AddMessage(list_data)

    with arcpy.da.UpdateCursor(fc, fields) as cursor:
        for x in cursor:
            for i in list_data:
                if u"_".join([str(m) for m in x[:9]]) == u"_".join([str(p) for p in i[:9]]):
                    x[9] = i[9]
                    x[10] = i[10]
                    x[11] = i[11]
                    x[12] = i[12]
                    x[13] = i[13]
                    x[14] = i[14]
                    cursor.updateRow(x)
    arcpy.AddMessage("Se han actualizado {} registros".format(len(list_data)))

def main():
    proccess()

if __name__ == '__main__':
    main()
