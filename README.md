<div style="text-align:center;">
    <img src ="https://github.com/ryali93/pygisernanp/blob/master/Images/sernanp_logo.png">
</div>

# PyGISernanp

## Qué es PyGISernanp
Ver [repositorio](https://github.com/ryali93/pygisernanp)

> PyGISernanp es una extensión desarrollada en [Python 2.7](https://www.python.org/) para [ArcMap 10.X](http://desktop.arcgis.com/es/arcmap/10.3/main/map/what-is-arcmap-.htm), el cual brinda soporte espacial en los Procedimientos de manejo de Sensoramiento Remoto y sirve de funcionalidad a la gestión de la Base de Datos Geográfica de [SERNANP](https://www.sernanp.gob.pe/).

## Estructura

- README.md : Este archivo

- makeaddin.py : Un script que creará un archivo *.esriaddin a partir de este Proyecto, adecuado para compartir o desplegar.

- config.xml : El archivo de configuración del AddIn

- Images/* : Todas las imágenes de la interfaz de usuario para el proyecto (íconos, imágenes para botones, etc)

- Install/* : El proyecto de Python utilizado para la implementación del complemento. La secuencia de comandos de Python específica que se usará como módulo raíz, se especifica en config.xml.



## Instalación
1. Clone el repositorio remoto a un repositorio local con el comando siguiente
        
        git clone https://github.com/ryali93/pygisernanp.git


2. Ejecute el archivo makeaddin.py para generar el archivo *.esriaddin (tenga en cuenta realizar la edición corerspondiente para apuntar la salida del archivo a un directorio conocido de su equipo).

3. Agregar la ruta del directorio donde se aloja el archivo *.esriaddin desde ArcMap > Customize > Add-in Manager > Options > Add Folder.

## Uso
1. Tenga en cuenta que solo es una extensión, por tanto se ejecutará al iniciar ArcMap; si necesita explotar su funcionalidad deberá tener acceso al SIGCATMIN.

## Créditos
* [Roy Yali](https://github.com/ryali93)
* [SERNANP](https://www.sernanp.gob.pe/)