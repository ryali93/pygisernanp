library(rgee)
library(rgeeExtra)
library(mapview)
library(sf)
library(mapedit)
ee_Initialize()

GAUL = ee$FeatureCollection("FAO/GAUL/2015/level1")
Sentinel = ee$ImageCollection("COPERNICUS/S2_SR")
geometry = editMap()
geometry_ee = sf_as_ee(geometry)

# LimaBnd = GAUL$filterMetadata('ADM1_NAME', 'equals', 'Lima')
MdDBnd = GAUL$filterMetadata('ADM1_NAME', 'equals', 'Madre de Dios')

SentinelLima = Sentinel$filterBounds(MdDBnd)$
  filterDate('2020-01-01', '2020-12-31')$
  filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 50)

maskS2clouds <- function(image){
  mask = image$select('SCL')$remap(c(0,1,2,3,4,5,6,7,8,9,10,11), 
                                   c(0,0,0,0,1,1,1,0,0,0,0,1))$select(list(0), list('cloudM'))
  return(image$updateMask(mask))
}

scaling <- function(img){
  scaleFactorA = img$select('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11', 'B12')$divide(10000)
  scaleFactorB = img$select('AOT', 'WVP')$divide(1000)
  return(img$addBands(scaleFactorA, NULL, T)$addBands(scaleFactorB, NULL, T))
}

calcVIsSen <- function(img){
  ndvi = img$normalizedDifference(c('B8', 'B4'))$select(list(0), list('ndvi'))
  lswi = img$normalizedDifference(c('B8', 'B11'))$select(list(0), list('lswi'))
  return(img$addBands(ndvi)$addBands(lswi))
}

SentinelLimapreprocessed = SentinelLima$map(maskS2clouds)$map(scaling)$map(calcVIsSen)

# Convertir la colección a una imagen usando estadisticas basadas en pixel y recortar la imagén a la región de Madre de Dios
medianSEN = SentinelLimapreprocessed$median()$clip(MdDBnd)
# medianSEN = ee$Image('users/an-sig/MDDmedianSentinel2020')

# Definir parámetros de visualización
vizParamsSEN = list(bands = c('B12', 'B8', 'B3'),
                    min = c(0,0,0),
                    max = c(0.3,0.5,0.3))

# Anãdir imagen al mapa
Map$centerObject(MdDBnd,8)
Map$addLayer(medianSEN, vizParamsSEN, 'median SEN')

m1 = Map$addLayer(medianSEN, vizParamsSEN, 'median SEN')
m2 = Map$addLayer(puntos, list(), 'Puntos SEN')
m1 + m2

puntos_sf = ee_as_sf(puntos)

##########################################################################################
# CLASIFICACION SUPERVISADA
puntos = ee$FeatureCollection('projects/servir-amazonia/MDD_training_pts')
puntos = puntos$remap(c(3,6,11,12,14,24,25,30,33),
                      c(0,1,2,3,4,5,6,7,8),'classifica')

puntos$aggregate_histogram('classifica')$getInfo() %>% as.data.frame() %>% t()

bandasPredicion = c('B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A', 'B9', 'B11','B12')

entrenamiento = medianSEN$select(bandasPredicion)$sampleRegions(
  collection = puntos, 
  properties = list('classifica'),
  scale = 30,
  tileScale = 8
)

CARTclassifier = ee$Classifier$smileCart()$train(
  features = entrenamiento, 
  classProperty = 'classifica',
  inputProperties = bandasPredicion
)

paletaColor = c('47892B', '70AB9F', '5900CF', 'A6AA03', 'F7A708', 'B8B5AE', '000000', 'F8FF0D', '0D1AFF')#; //https://htmlcolorcodes.com/

classificacionCART = medianSEN$select(bandasPredicion)$classify(CARTclassifier)
Map$addLayer(classificacionCART$clip(geometry_ee), list(min=0, max=8, palette=paletaColor), 'classificacion CART')



# Random Forest Classifier
# RFclassifier = ee.Classifier.smileRandomForest({numberOfTrees:100,seed:5}).train({
#   features:entrenamiento, 
#   classProperty: 'classifica',
#   inputProperties: bandasPredicion
# });
# 
# var RFclassificacion = medianSEN.select(bandasPredicion).classify(RFclassifier);
# Map.addLayer(RFclassificacion.clip(geometry), {min: 0, max: 8, palette: paletaColor}, 'classificación RF');



# Clasificación no supervisionada

# novos dados de entrenamiento
entrenamientoAgrupador = medianSEN$select(bandasPredicion)$sample(
  region = MdDBnd,
  scale = 30,
  numPixels = 1000,
  tileScale = 8
)

# Selecionar classifier y entrenarlo
clusterer = ee$Clusterer$wekaKMeans(9)$train(entrenamientoAgrupador)

# Agrupar la imagen (clasificación)
Kclassificacion = medianSEN$cluster(clusterer)

# Añadir el resultado con colores aleatorios
Map$addLayer(Kclassificacion$clip(geometry_ee)$randomVisualizer(), list(), 'clasificación K-means - colores aleatorios')
