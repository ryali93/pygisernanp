import arcpy
import os
import json
import requests
import datetime

main_url = "https://services6.arcgis.com/DWc6sLYN7TTrbI6g/ArcGIS/rest/services/DEFOR_2021_05_25_gdb/FeatureServer/"
fields_monitdefor = ['anp_codi','globalid','md_fuente','zi_codi','md_clase','md_mesrep','md_fecrev','md_fecimg','md_editor','md_sup','md_exa','md_revcam','md_causa','md_actom','md_medver','md_obs']
fields_monitdeforacum = ['anp_codi','globalid','md_fuente','zi_codi','md_clase','md_anno','md_fecrev','md_fecimg','md_sup','md_exa','md_revcam','md_feccam','md_causa','md_actom','md_medver']

def get_service(layer):
    '''
    :param layer: 0=MonitDeforAcum, 1=MonitDefor
    :return:
    '''
    services = {
        "query_url": os.path.join(main_url, layer + "/query"),
        "add_features_url": os.path.join(main_url, layer + "/addFeatures"),
        "delete_features_url": os.path.join(main_url, layer +"/deleteFeatures")
    }
    return services

def count_rows_from_query(url, query="1=1"):
    response = requests.post(
        url,
        data={
            'where': query,
            'outFields': "*",
            'returnCountOnly': 'true',
            'f': 'pjson'
        }
    )
    res = json.loads(response.text)
    cantidad = res["count"]
    return cantidad

def get_oid_list(fc, query=None):
    '''
    Get all records that meet the condition (md_mesrep)
    md_mesrep = 2021054
    fc = r"E:\sernanp\DB_2021_06_25.gdb\MonitDeforAcum"
    '''
    oid_list = [x[0] for x in arcpy.da.SearchCursor(fc, ["objectid"], query)]
    chunks = [oid_list[x:x + 1000] for x in range(0, len(oid_list), 1000)]
    return chunks, len(oid_list)

def create_features_json(fc, fields, oid_sql):
    '''
    :param fc: r"E:\sernanp\DB_2021_06_25.gdb\MonitDeforAcum"
    :param fields: list_fields_acum
    :param oid_sql: get_oid_list(fc)
    :return: features as dict
    '''
    list_features = []
    with arcpy.da.SearchCursor(fc, fields + ["shape@"], oid_sql) as cursor:
        for x in cursor:
            dict_fields = {"attributes": {fields[m]: x[m] for m in range(0, len(fields))}}
            for n in dict_fields["attributes"]:
                if type(dict_fields["attributes"][n]) == datetime.datetime:
                    dict_fields["attributes"][n] = dict_fields["attributes"][n].strftime("%m/%d/%Y")
            dict_fields["geometry"] = json.loads(x[-1].JSON)
            list_features.append(dict_fields)
    features = {'features': json.dumps(list_features), 'f': 'pjson'}
    return features

def upload_features_to_url(url, features):
    '''
    :param url: get_service("0")
    :param features:
    :return:
    '''
    r = requests.post(
        url=url,
        data=features,
        verify=False)
    res = json.loads(r.text)
    # arcpy.AddMessage(res)

def delete_features_from_url(url, query=None):
    sql = query if query else "1=1"
    r = requests.post(
        url,
        data={
            'where': '{}'.format(sql),
            'f': 'pjson'
        }
    )
    res = json.loads(r.text)
    # arcpy.AddMessage(res)

def proccess():
    fc = arcpy.GetParameterAsText(0)
    mesrep = arcpy.GetParameterAsText(1) # 2021062
    # fc = r"E:\sernanp\data\backup_2021_07_13.gdb\MonitDefor"
    # mesrep = 2021062
    code_feature = "1" if fc.endswith("MonitDefor") else "0"
    services = get_service(code_feature) # MonitDefor
    fields = fields_monitdefor if fc.endswith("MonitDefor") else fields_monitdeforacum

    url_query = services["query_url"]
    url_upload = services["add_features_url"]
    url_delete = services["delete_features_url"]

    # get oids
    # mesrep = 2021063
    sql = "md_mesrep = {}".format(mesrep)
    arcpy.AddMessage(sql)
    chunks, len_oid = get_oid_list(fc, sql)

    # Count rows from query
    len_query = count_rows_from_query(url_query, sql)

    if len_query == 0:
        # Upload features from database to agol
        for chunk in chunks:
            oid_sql = "objectid in ({})".format(",".join([str(x) for x in chunk]))
            features = create_features_json(fc, fields, oid_sql)
            upload_features_to_url(url_upload, features)
        arcpy.AddMessage("Se han subido correctamente {} registros al servicio {}".format(len_oid, url_query))
    else:
        arcpy.AddMessage("Posiblemente no tenga registros del Mes de Reporte {} o ya se encuentren subidos".format(mesrep))

def main():
    proccess()

if __name__ == '__main__':
    main()
