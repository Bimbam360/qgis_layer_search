from .layersearch import LayerSearchPlugin

def classFactory(iface):
    return LayerSearchPlugin(iface)