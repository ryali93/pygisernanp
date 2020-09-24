//Crear una geometria en la parte inferior ***

var polygons = ee.FeatureCollection(geometry);
var bufferPoly = function(feature) {return feature.buffer(20);};
var geometrybuffer = polygons.map(bufferPoly);

Map.addLayer(geometry,{},'limite');

// Función para enmascarar nubes usando la banda QA60 de nubes
function maskS2clouds(image) {
 var qa = image.select('QA60');

 // Bits 10 and 11 are clouds and cirrus, respectively.
 var cloudBitMask = 1 << 10;
 var cirrusBitMask = 1 << 11;

 // Both flags should be set to zero, indicating clear conditions.
 var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
     .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

 return image.updateMask(mask).divide(10000)}

var dataset = ee.ImageCollection('COPERNICUS/S2_SR')
                 .filterDate('2019-05-01', '2019-09-15')
                 // Pre-filter to get less cloudy granules.
                 .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
                 .map(maskS2clouds)
                 .filterBounds(geometrybuffer);
var SentinelFiltro = ee.Image(dataset.median());

var SentinelClip = SentinelFiltro.clip (geometrybuffer);

var rgbVis = {
 min: 0.0,
 max: 0.7,
 bands: ['B11', 'B8', 'B2'],
};

var Lista = dataset.map(function(img){return img.clip(geometrybuffer)}).toList(dataset.size());
print('Lista', Lista)


Map.addLayer (SentinelClip, {
  max: 0.7, 
  min: 0.0, 
  gamma: 1.0,
  bands: ['B11','B8','B2']},//Combinación de bandas que se quieren visualizar 
  'S2_11-8-2');
  
  Map.addLayer (SentinelClip, {
  max: 0.15, 
  min: 0.0, 
  gamma: 1.0,
  bands: ['B4','B3','B2']},//Combinación de bandas que se quieren visualizar 
  'S2_4-3-2');
  
  Map.addLayer (SentinelClip, {
  max: 0.15, 
  min: 0.0, 
  gamma: 1.0,
  bands: ['B8A','B11','B4']},//Combinación de bandas que se quieren visualizar 
  'S2_8A-11-4',false);
  
//Visualización de la imagen Sentinel centrada en área de estudio
Map.centerObject (geometrybuffer);

Export.image.toDrive({
  image: SentinelClip.select("B11", "B8", "B4", "B3", "B2"),//Bandas con las que se exportará
  description: 'Sentinel2_10m',//Nombre con el que se guarda en el DRIVE
  scale: 10,//Resolución de pixel
  region: geometrybuffer});//Imagen cortada con área de estudio con buffer

// //Fusionar featureclasses (Se fusionan todos los datos de entrenamiento)
// var newfc = Agropecuario.merge(Bosque).merge(Agua).merge(Islas).merge(Nube);
// print(newfc);//Se debe visualizar en el panel de consola que los datos fueron combinados

// // Bandas a usar.
// var bands = ['B2','B3', 'B4', 'B8', 'B12'];//Se seleccionan las bandas que queremos que se integren los valores a los puntos de entrenamiento

// // Crear datos de entrenamiento
// var training = SentinelClip.select(bands).sampleRegions({
//   collection: newfc,
//   properties: ['class'],//el nombre exacto con el que se realiza la clasificación
//   scale: 10//resolución de salida de la clasificación
// });
// //print(training)

// // Clasificación

// var classifier = ee.Classifier.cart().train({
//   features: training,
//   classProperty: 'class',
//   inputProperties: bands
//   });

// // Ejecutar la clasificación

// var classified = SentinelClip.select(bands).classify(classifier);

// Map.centerObject(newfc, 13);
// Map.addLayer(classified, {min:0 , max:5 , palette: ['#d63000','#98ff00','#0b4a8b','#ffc82d','#00ffff','#bf04c2']},
// 'classification');
  
//  // //exportar clasificacion
// Export.image.toDrive({
// image: classified,
//  description: 'Class_Sentinel2_10m',
// scale: 10,
// region: geometrybuffer}); 

// Map.addLayer(geometrybuffer, {},
//   'limite',false); 
