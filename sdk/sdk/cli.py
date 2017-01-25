# -*- coding: utf-8 -*-

import hashlib, os, sys, zipfile, yaml
import xml.etree.cElementTree as ET

def writePluginsXml(files):
	root = ET.Element("plugins")
	for filename in files:
		with zipfile.ZipFile(filename, 'r') as z:
			cfg = yaml.load(z.read('manifest.yml'))
			plugin = ET.SubElement(root, "plugin", name=cfg['name'])
			if 'color' in cfg:
				plugin.attrib['color'] = cfg['color']
			ET.SubElement(plugin, "description").text = cfg['description']
			if 'author' in cfg:
				ET.SubElement(plugin, 'author', name=cfg['author'], email=cfg['author-email'])
			edition = ET.SubElement(plugin, "edition", version=cfg['version'])
			if 'icon' in cfg:
				# Exctract icon
				iconFilename = '%s.png' % os.path.splitext(filename)[0]
				with open(iconFilename, 'wb') as icon:
					icon.write(z.read(cfg['icon']))
				ET.SubElement(edition, 'icon').text = 'http://fw.telldus.com/plugins/%s' % iconFilename
			sha1 = hashlib.sha1()
			f = open(filename, 'rb')
			try:
				sha1.update(f.read())
			finally:
				f.close()
			url = 'http://fw.telldus.com/plugins/%s' % filename
			ET.SubElement(edition, "file", size=str(os.path.getsize(filename)), sha1=sha1.hexdigest()).text = url
			# TODO: Add <compatibility /> from compatible_platforms and require_features instead
			compatibility = ET.SubElement(edition, "compatibility")
			for hw in ['tellstick-desktop', 'tellstick-net-v2', 'tellstick-znet-lite', 'tellstick-znet-lite-v2']:
				ET.SubElement(compatibility, "hardware").text = hw
	tree = ET.ElementTree(root)
	tree.write('plugins.xml', encoding='utf-8', xml_declaration=True)
	return 0
writePluginsXml.description = 'Generate a plugins.xml file from a set of plugins'

commands = {'writePlugins': writePluginsXml}

def printUsage():
	print "Usage: %s command" % sys.argv[0]
	print "Available commands:"
	for command in commands:
		print "  %s - %s" % (command, commands[command].description)

def main():
	if len(sys.argv) < 2:
		printUsage()
		sys.exit(1)
	if sys.argv[1] not in commands:
		printUsage()
		print "Unknown command: %s" % sys.argv[1]
		sys.exit(1)
	sys.exit(commands[sys.argv[1]](sys.argv[2:]))
