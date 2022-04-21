import arcpy
import os
import json
import requests
import datetime

main_url = "https://geospatial.sernanp.gob.pe/arcgis_server/rest/services/sernanp_monitoreo/deforestacion/FeatureServer/"
fields_monitdefor = ['anp_codi','md_fuente','zi_codi','md_clase','md_mesrep','md_fecrev','md_fecimg','md_editor','md_sup','md_exa','md_revcam','md_causa','md_actom','md_medver','md_obs']
fields_monitdeforacum = ['anp_codi','md_fuente','zi_codi','md_clase','md_anno','md_fecrev','md_fecimg','md_sup','md_exa','md_revcam','md_feccam','md_causa','md_actom','md_medver']

def get_service(layer):
    '''
    :param layer: 0=MonitDeforAcum, 1=MonitDefor
    :return:
    '''
    services = {
        "query_url": os.path.join(main_url, layer + "/query"),
        "add_features_url": os.path.join(main_url, layer + "/addFeatures"),
        "delete_features_url": os.path.join(main_url, layer + "/deleteFeatures")
    }
    return services

def get_oid_list(fc, query=None):
    '''
    Get all records that meet the condition (md_mesrep)
    md_mesrep = 2021054
    fc = r"E:\sernanp\DB_2021_06_25.gdb\MonitDeforAcum"
    '''
    oid_list = [x[0] for x in arcpy.da.SearchCursor(fc, ["objectid"], query)]
    chunks = [oid_list[x:x + 1000] for x in range(0, len(oid_list), 1000)]
    return chunks

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
    fc = "MonitDefor" #arcpy.GetParameterAsText(0) # "MonitDefor" | "MonitDeforAcum"
    # fc ="MonitDeforAcum"
    mesrep = "" #arcpy.GetParameterAsText(1) # 2021062

    code_feature = "0" if fc == "MonitDefor" else "1"
    services = get_service(code_feature) # MonitDefor

    url_query = services["query_url"]
    url_upload = services["add_features_url"]
    url_delete = services["delete_features_url"]

    # get oids
    sql = "md_mesrep = {}".format(mesrep)

    # Delete features from agol
    sql_delete = None if mesrep in [None, ""] else sql
    delete_features_from_url(url_delete, sql_delete)
    if mesrep not in ["", None]:
        arcpy.AddMessage("Se han borrado satisfactoriamente los registros del Mes de Reporte {}".format(mesrep))
    else:
        arcpy.AddMessage("Se han borrado todos los registros de la capa {}".format(fc))

def main():
    proccess()

if __name__ == '__main__':
    main()
