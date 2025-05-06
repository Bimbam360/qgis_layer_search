def classFactory(iface): 
	"""Load LayerSearchPlugin from layersearch module."""
	from .layersearch import LayerSearchPlugin
	return LayerSearchPlugin(iface)