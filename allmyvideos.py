import urllib2 as urllib
import argparse
import os, sys, time, re
from multiprocessing import Process
import subprocess
import mechanize, cookielib

from simple_downloader import SimpleDownloader

class AllMyVideosDownloader:
	verbose = False
	headers = {
	        'User-Agent'      : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
	        'Connection'      : 'keep-alive'
	}

	@staticmethod
	def setup_parser(parser):
		allmyvideos_parser = parser.add_parser('allmyvideos')	

		# Common stuff
		allmyvideos_parser.add_argument("--out", action="store", type=str, default=None, required=True, help="Path to store output")
		allmyvideos_parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose output")
		allmyvideos_parser.add_argument("--prefix", action="store", type=str, default='out', help="Prefix to use for output files. Default: out")
		allmyvideos_parser.add_argument("--url", action="store", type=str, default=None, required=True, help="URL to use")

		allmyvideos_parser.set_defaults(func=AllMyVideosDownloader.main)

		return parser;

	@staticmethod
	def download(url, out):
		br = mechanize.Browser()
		br.set_cookiejar(cookielib.LWPCookieJar())
		
		page = br.open(url)
		source = page.read().split('\n')

		amv_url = ''
		pattern = re.compile('.*\"(http://allmyvideos.net/.*)\".*')
		for line in source:
			m = pattern.match(line)
			if m:
				amv_url = m.group(1)

		page = br.open(amv_url)
		source = page.read().split('\n')
		
		mp4_url = ''
		mp4_pattern = re.compile('.*\"(http://.*mp4.*)\".*')
		for line in source:
			m = mp4_pattern.match(line)
			if m:
				mp4_url = m.group(1)

		SimpleDownloader.wget_download(mp4_url, out)

	@staticmethod
	def main(args):
		out = '%s/%s' % (args.out, args.prefix)

		AllMyVideosDownloader.download(args.url, out)
