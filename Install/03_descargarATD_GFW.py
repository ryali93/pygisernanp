import requests
import pandas as pd

tmp_csv = r"E:\sernanp\proyectos\monitoreo\gfw\tmp2.csv"

url = "https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts/latest/download/csv?sql=" \
	  "SELECT latitude, longitude, gfw_integrated_alerts__date, umd_glad_landsat_alerts__confidence, umd_glad_sentinel2_alerts__confidence, wur_radd_alerts__confidence, " \
	  "gfw_integrated_alerts__confidence " \
	  "FROM data WHERE " \
	  "gfw_integrated_alerts__date >= '2021-03-19' AND gfw_integrated_alerts__date <= '2022-09-19' " \
	  "AND gfw_integrated_alerts__confidence != 'nominal'&geostore_origin=gfw&geostore_id=ab4d1bd5-0075-cd7a-1913-c77fabb4b67a"

response = requests.get(url)
print(response)

with open(tmp_csv, 'w') as f:
   f.write(response.text)
   f.close()

df = pd.read_csv(tmp_csv)
print(df.head())

