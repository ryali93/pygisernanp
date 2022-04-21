import threading
import os, sys
import webbrowser

sys.path.insert(0, os.path.dirname(__file__))

from config import *
from messages import Messages

msg = Messages

class ActualizarDeforAcum(object):
    """Implementation for addin_addin.ActualizarDeforAcum (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class DescargarATD(object):
    """Implementation for addin_addin.DescargarATD (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class FichasPlanet(object):
    """Implementation for addin_addin.FichasPlanet (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

class ValidarDefor(object):
    """Implementation for addin_addin.ValidarDefor (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pass

def OpenBrowserURL():
    url = 'https://geo.sernanp.gob.pe/visorsernanp/'
    webbrowser.open(url,new=0)

class AbrirUrl(object):
    """Implementation for addin_addin.AbrirUrl (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        t = threading.Thread(target=OpenBrowserURL)
        t.start()
        t.join()
