from ConfigParser import RawConfigParser

class LayerConfigParser(RawConfigParser):

	def __init__(self):
		RawConfigParser.__init__(self)
		self.layers = []

	def read(self, filenames):
		if type(filenames) is not list:
			filenames = [filenames]
		for filename in filenames:
			cp = RawConfigParser()
			cp.read(filename)
			self.layers.append((cp, filename, None))
		return RawConfigParser.read(self, filenames)

	def readfp(self, fp, filename=None):
		cp = RawConfigParser()
		fp.seek(0)
		cp.readfp(fp, filename)
		self.layers.append((cp, filename, fp))
		fp.seek(0)
		ret = RawConfigParser.readfp(self, fp, filename)
		return ret

	def whereset(self, section, option):
		for cp, filename, fp in reversed(self.layers):
			if cp.has_option(section, option):
				return filename
		raise ShutItFailException('[%s]/%s was never set' % (section, option))

	def get_config_set(self, section, option):
		"""Returns a set with each value per config file in it.
		"""
		values = set()
		for cp, filename, fp in self.layers:
			if cp.has_option(section, option):
				values.add(cp.get(section, option))
		return values

	def reload(self):
		"""
		Re-reads all layers again. In theory this should overwrite all the old
		values with any newer ones.
		It assumes we never delete a config item before reload.
		"""
		oldlayers = self.layers
		self.layers = []
		for cp, filename, fp in oldlayers:
			if fp is None:
				self.read(filename)
			else:
				self.readfp(fp, filename)

	def remove_section(self, *args, **kwargs):
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')
	def remove_option(self, *args, **kwargs):
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')
	def set(self, *args, **kwargs):
		raise NotImplementedError('Layer config parsers aren\'t directly mutable')


