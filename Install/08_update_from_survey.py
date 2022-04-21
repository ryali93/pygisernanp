import requests
import json

MonitDefor = "http://geospatial.sernanp.gob.pe/arcgis_server/rest/services/sernanp_monitoreo/deforestacion/FeatureServer/0"
ConfirmacionDefor = "http://geospatial.sernanp.gob.pe/arcgis_server/rest/services/Hosted/service_832d07b827f34c2292b0db146e6ecc48/FeatureServer/0"


def oidsOnly(url, coords, distance):
    response = requests.post(
        url + "/query",
        data={
            "where": "1=1",
            "geometry": "{}, {}".format(coords[0], coords[1]),
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": "{}".format(distance),
            "units": "esriSRUnit_Kilometer",
            "outFields": "*",
            "outSR": "4326",
            "returnIdsOnly": "true",
            "f": "pjson"
        }
    )
    res = json.loads(response.text)
    lista_oids = list(set(res["objectIds"]))
    return lista_oids


def actualizar_servicio(url, datos):
    url_update = '{}/updateFeatures'.format(url)
    res_update = requests.post(
        url_update,
        data={
            'features': json.dumps(datos),
            'f': 'pjson'
        }
    )
    print(datos)
    resup = json.loads(res_update.text)
    print(resup)


def consulta_esquema(url):
    url = '{}/query'.format(url)
    response = requests.post(
        url,
        data={
            'where': '1=1',
            'outFields': "*",
            'f': 'pjson'
        }
    )
    res = json.loads(response.text)
    return res


confirm = consulta_esquema(ConfirmacionDefor)

new_features = []
for confirmado in confirm["features"]:
    coords = [confirmado["geometry"]["x"], confirmado["geometry"]["y"]]
    oid_list = oidsOnly(MonitDefor, coords, 5)
    for oid in oid_list:
        feature = {}
        row = {}
        row["objectid"] = oid
        for feat in confirm["features"]:
            row["md_feccam"] = feat["attributes"]["md_feccam"]
            row["md_actom"] = feat["attributes"]["md_actom"]
            row["md_medver"] = feat["attributes"]["md_medver"]
            row["anp_codi"] = feat["attributes"]["anp_codi"]
            row["md_causa"] = feat["attributes"]["md_causa"]
            row["md_obs"] = feat["attributes"]["md_obs"]
            row["md_revcam"] = feat["attributes"]["md_revcam"]
        feature["attributes"] = row
        new_features.append(feature)

actualizar_servicio(MonitDefor, new_features)