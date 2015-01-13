import urllib2 as urllib
import argparse
import os, sys, time, re
from multiprocessing import Process
import subprocess


class SimpleDownloader:
	verbose = False
	headers = {
	        'User-Agent'      : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
	        'Connection'      : 'keep-alive'
	}

	@staticmethod
	def setup_parser(parser):
		simple_parser = parser.add_parser('simple')	

		# Common stuff
		simple_parser.add_argument("--out", action="store", type=str, default=None, required=True, help="Path to store output")
		simple_parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose output")
		simple_parser.add_argument("--prefix", action="store", type=str, default='out', help="Prefix to use for output files. Default: out")
		simple_parser.add_argument("--url", action="store", type=str, default=None, required=True, help="URL to use")

		simple_parser.add_argument('--wget', action="store_true", default=False, help="Use wget instead of urllib2")
		simple_parser.set_defaults(func=SimpleDownloader.main)

		return parser;

	@staticmethod
	def wget_download(url, out_path):
		cmdline = 'wget -O %s %s' % (out_path, url)	#TODO: Give proper out path
		proc = subprocess.Popen(cmdline.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()

		lines_iterator = iter(proc.stderr.readline, "")
		for line in lines_iterator:
			print line.strip()

		return None


	@staticmethod
	def urllib_download(url, out):
		try:
			request  = urllib.Request(url)
			for key, value in SimpleDownloader.headers.iteritems():
				request.add_header(key, value)

				response = urllib.urlopen(request)

			block_size = 10485760
			with open(out, 'w') as out:
				while 1:
					b = response.read(block_size)
					if not b:
						break
					out.write(b)
		except urllib.HTTPError as e:
			result = '%s :Failed!' % (url)
			print '    %s' % (e.__repr__())
			print '    %s' % (result)
			results.append(result)
			return

		result = '%s :Succeeded!' % (url)

	@staticmethod
	def main(args):
		out = '%s/%s' % (args.out, args.prefix)

		if args.wget is True:
			SimpleDownloader.wget_download(args.url, out)
		else:
			SimpleDownloader.urllib_download(args.url, out)
