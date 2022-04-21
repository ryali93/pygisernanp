library(rgee)
library(rgeeExtra)
library(mapview)
library(sf)
library(mapedit)
ee_Initialize()

radd = ee$Image('projects/radar-wur/raddalert/v1/sa_20220414')$select(1)
geometry = editMap()
geometry_ee = sf_as_ee(geometry)$first()

ee_as_raster(image = radd, 
             dsn = "E:/sernanp/proyectos/monitoreo/radd/sa_20220414_2.tif", 
             via = "drive", region = geometry_ee$geometry())

