import arcpy
import os
import json
import requests
import datetime

main_url = "http://geospatial.sernanp.gob.pe/arcgis_server/rest/services/sernanp_monitoreo/deforestacion/FeatureServer/"
fields_monitdefor = ['anp_codi','md_fuente','zi_codi','md_causa','md_mesrep','md_fecrev','md_fecimg','md_sup','md_exa','md_obs','md_conf','md_bosque','md_zonif']
fields_monitdeforacum = ['anp_codi','md_fuente','zi_codi','md_causa','md_anno','md_fecimg','md_sup','md_exa','md_obs','md_conf','md_bosque','md_zonif']

def get_service(layer):
    '''
    :param layer: 0=MonitDefor, 1=MonitDeforAcum
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
    oid_sql = 'objectid in (54263,54264,54265,54266,54267)'
    :return: features as dict
    '''
    list_features = []
    with arcpy.da.SearchCursor(fc, fields + ["shape@"], oid_sql) as cursor:
        for x in cursor:
            dict_fields = {"attributes": {fields[m]: x[m] for m in range(0, len(fields))}}
            for n in dict_fields["attributes"]:
                if type(dict_fields["attributes"][n]) == datetime.datetime:
                    fecha_ini = dict_fields["attributes"][n]
                    if fecha_ini.year > 2000:
                        fecha_fin = int(time.mktime(fecha_ini.timetuple()))
                        expon = len(str(fecha_fin)) % 13
                        dict_fields["attributes"][n] = fecha_fin * (10 ** (13 - expon))
                    else:
                        dict_fields["attributes"][n] = None

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
    arcpy.AddMessage(res)

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
    fc = r'Database Connections\gdb.sde\gdb.sde.MonitoreoCobertura\gdb.sde.MonitoreoDeforestacion'
    mesrep = 2022091
    code_feature = "0" if fc.endswith("MonitoreoDeforestacion") or fc.endswith("MonitDefor")  else "1"
    services = get_service(code_feature) # MonitoreoDeforestacion
    fields = fields_monitdefor if fc.endswith("MonitoreoDeforestacion") or fc.endswith("MonitDefor") else fields_monitdeforacum

    url_query = services["query_url"]
    url_upload = services["add_features_url"]
    url_delete = services["delete_features_url"]

    # get oids
    # sql = "1 = 1"
    sql = "md_mesrep = {}".format(mesrep)
    arcpy.AddMessage(sql)
    chunks, len_oid = get_oid_list(fc, sql)
    arcpy.AddMessage(len_oid)

    # Count rows from query
    len_query = count_rows_from_query(url_query, sql)

    if len_query == 0:
        # Upload features from database to agol
        i = 1
        for chunk in chunks:
            print(i)
            oid_sql = "objectid in ({})".format(",".join([str(x) for x in chunk]))
            features = create_features_json(fc, fields, oid_sql)
            upload_features_to_url(url_upload, features)
            i += 1
        arcpy.AddMessage("Se han subido correctamente {} registros al servicio {}".format(len_oid, url_query))
        print("Se han subido correctamente {} registros al servicio {}".format(len_oid, url_query))
    else:
        arcpy.AddMessage("Posiblemente no tenga registros del Mes de Reporte {} o ya se encuentren subidos".format(mesrep))

def main():
    proccess()

if __name__ == '__main__':
    main()
