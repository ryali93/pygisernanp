library(rgee)
library(sf)
library(tidyverse)
library(raster)
library(mapview)
library(mapedit)

ee_Initialize("ryali93")

setwd("E:/sernanp/recibido/Informacion_Teledeteccion/Ambitos_monitoreo")
ZI_marco <- st_read("E:/sernanp/recibido/Informacion_Teledeteccion/Ambitos_monitoreo/ZI_marco.shp")
ZI_RCH <- ZI_marco %>% filter(str_detect(Codigo, "ZI_RCH")) %>% dplyr::select(geometry)
ee_ZI_RCH_1 <- sf_as_ee(ZI_RCH[1,])

polygons <- ee$FeatureCollection(ee_ZI_RCH_1)
bufferPoly <- function(feature) {feature$buffer(20)}
geometrybuffer <- polygons$map(bufferPoly)

maskS2clouds <- function(img){
  qa = img$select('QA60')
  cloudBitMask = bitwShiftL(1,10)
  cirrusBitMask = bitwShiftL(1,11)
  mask = qa$bitwiseAnd(cloudBitMask)$eq(0)$And(qa$bitwiseAnd(cirrusBitMask)$eq(0))
  img$updateMask(mask)$divide(10000)
}

dataset <- ee$ImageCollection('COPERNICUS/S2_SR')$
  filterDate('2019-05-01', '2019-09-15')$
  filter(ee$Filter$lt('CLOUDY_PIXEL_PERCENTAGE', 30))$
  map(maskS2clouds)$
  filterBounds(geometrybuffer)

SentinelFiltro <- ee$Image(dataset$median())
SentinelClip <- SentinelFiltro$clip(geometrybuffer)

rgbVis <- list(bans=c('B11', 'B8', 'B2'), min=0, max=0.7)

Lista <- dataset$map(function(img){img$clip(geometrybuffer)})$toList(dataset$size())

Map$centerObject(geometrybuffer)
Map$addLayer(ee_ZI_RCH_1, list(), name='limite')
Map$addLayer(SentinelClip, list(max= 0.7, min= 0.0, gamma= 1.0,
                                bands= c('B11','B8','B2')), name='S2_11-8-2')
Map$addLayer(SentinelClip, list(max= 0.15, min= 0.0, gamma= 1.0,
                                bands= c('B4','B3','B2')), name='S2_4-3-2')
Map$addLayer (SentinelClip, list(max= 0.15, min= 0.0, gamma= 1.0,
                                 bands= c('B8A','B11','B4')), 'S2_8A-11-4', FALSE)

# ************************************************************************
ee$Image$getInfo(SentinelClip)
Sentinel2_10m <- ee_as_raster(image = SentinelClip$select("B11", "B8", "B4", "B3", "B2"),
                           region = geometrybuffer$geometry(), via = "drive")
writeRaster(Sentinel2_10m, "Sentinel2_ZI_RCH_01_10m.tif")
# ************************************************************************

puntos <- mapview(Sentinel2_10m) %>% editMap()

plot(Sentinel2_10m)
