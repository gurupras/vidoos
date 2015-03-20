import urllib2 as urllib
import urlparse
import os, sys, re
from multiprocessing import Process, Queue, Pool, cpu_count
import argparse
import posixpath
import subprocess
import signal

def download(url, out_path, results):
	filename = posixpath.basename(urlparse.urlsplit(url).path)
	try:
		request  = urllib.Request(url)
		for key, value in NetuDownloader.headers.iteritems():
			request.add_header(key, value)

		response = urllib.urlopen(request)

		out = open(out_path, 'wb')
		for b in response.read():
			out.write(b)
		out.close()
	except urllib.HTTPError as e:
		result = '%s :Failed!' % (filename)
		print '    %s' % (e.__repr__())
		print '    %s' % (result)
		results.append(result)
		return
	except KeyboardInterrupt:
		raise KeyboardInterruptException()
	result = '%s :Succeeded!' % (filename)
	results.append(result)
	print result


class KeyboardInterruptException(Exception) : pass

class NetuDownloader:
	verbose = False
	headers = {
			'User-Agent'      : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
			'Accept'          : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
			'Accept-Language' : 'en-US,en;q=0.5',
			'Accept-Encoding' : 'gzip, deflate',
			'Referer'         : 'http://c.hqq.tv/player/cbplayer/uppod_1.7.0.6.swf',
			'Connection'      : 'keep-alive'
	}
	pool = None

	@staticmethod
	def setup_parser(parser):
		netu_parser = parser.add_parser('netu')

		# Common stuff
		netu_parser.add_argument("--out", action="store", type=str, default=None, required=True, help="Path to store output")
		netu_parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose output")
		netu_parser.add_argument("--prefix", action="store", type=str, default='out', help="Prefix to use for output files. Default: out")
		netu_parser.add_argument("--url", action="store", type=str, default=None, required=True, help="URL to use")

		netu_parser.add_argument('--num-frags', action="store", type=NetuDownloader.custom_range, required=True, help="Number of fragments")
		netu_parser.add_argument('--num-nums', action="store", type=NetuDownloader.custom_range, required=True, help="Number of 'Num'")
		netu_parser.add_argument('--stitch', action="store_true", default=False, help="Stitch the results together - ONLY for frag mode")
		netu_parser.set_defaults(func=NetuDownloader.main)

		return parser;

	@staticmethod
	def custom_range(string):
		try:
			range_pattern = re.compile('\[(?P<lower>\d+):(?P<upper>\d+)]')
			range_match   = range_pattern.match(string)
			if range_match:
				return range(int(range_match.group('lower')), int(range_match.group('upper')))
			else:
				return range(1, int(string))
		except ValueError as e:
			print 'Expected integer instead found %s' % (e)
			sys.exit(-1)


	@staticmethod
	def frag_download(args, out_path_base, urls, results):
		NetuDownloader.pool    = Pool(cpu_count() * 2)

		# We have to demangle the URL to pass in frag and num
		pattern = re.compile('(?P<url_head>http://.*)(?P<frag>Frag\d+)(?P<num>Num\d+)(?P<url_tail>.*)')
		m = pattern.match(args.url)
		if m is None or m.group('url_head') is None or m.group('frag') is None or m.group('num') is None or m.group('url_tail') is None:
			print 'Did not parse URL correctly! \nURL pattern :%s' % (pattern.__repr__())
			sys.exit(-1)

		for frag in args.num_frags:
			for num in args.num_nums:
				url = '%sFrag%dNum%d%s' % (m.group('url_head'), frag, num, m.group('url_tail'))
				urls.append(url)
				out_path = os.path.join(out_path_base, '%s.mp4Frag%04dNum%04d.ts' % (args.prefix, frag, num))
				try:
					NetuDownloader.pool.apply_async(download, [url, out_path, results])
				except Exception as e:
					raise e

				#Downloader.download(url, out_path, results)

		NetuDownloader.pool.close()
		NetuDownloader.pool.join()


	@staticmethod
	def stitch(out_path_base, prefix):
		pass

	@staticmethod
	def main(args):
		NetuDownloader.frag_download(args, args.out, [], [])
		if args.stitch is True:
			stitch_cmdline = 'stitch.sh %s %s' % (out_path_base, args.prefix).split(' ')
			p = subprocess.Popen(stitch_cmdline)
			p.wait()
