import urllib2 as urllib
import os, sys, re
from multiprocessing import Process, Queue, Pool, cpu_count
import urlparse
import posixpath
import subprocess


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

    @staticmethod
    def download(url, out_path, results):
        # Ignore interrupt
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        filename = posixpath.basename(urlparse.urlsplit(url).path)
        try:
            request  = urllib.Request(url)
            for key, value in Downloader.headers.iteritems():
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
        result = '%s :Succeeded!' % (filename)
		results.append(result)
        print result

	@staticmethod
	def frag_download(args, out_path_base, urls, results):
		Downloader.pool    = Pool(cpu_count() * 2)

		# We have to demangle the URL to pass in frag and num
		pattern = re.compile('(?P<url_head>http://.*)(?P<frag>Frag\d+)(?P<num>Num\d+)(?P<url_tail>.*)')
		m = pattern.match(args.url)
		if m is None or m.group('url_head') is None or m.group('frag') is None or m.group('num') is None or m.group('url_tail') is None:
			print 'Did not parse URL correctly! \nURL pattern :%s' % (pattern.__repr__())
			sys.exit(-1)

		for frag in range(1, args.num_frags):
			for num in range(0, args.num_nums):
				url = '%sFrag%dNum%d%s' % (m.group('url_head'), frag, num, m.group('url_tail'))
				urls.append(url)
				out_path = os.path.join(out_path_base, '%s.mp4Frag%04dNum%04d.ts' % (args.prefix, frag, num))
				Downloader.pool.apply_async(Downloader.download, [url, out_path, results]).get(99999)
				#Downloader.download(url, out_path, results)

		Downloader.pool.close()
		Downloader.pool.join()

	@staticmethod
	def custom_range(string):
		try:
			range_pattern = re.compile('\[(?P<lower>\d)+:(?P<upper>\d+)]')
			range_match   = range_pattern.match(string)
			if range_match is not None:
				return range(int(lower), int(upper))
			else:
				return range(1, int(string))
		except ValueError as e:
			print 'Expected integer instead found %s' % (e.__repr__())
			sys.exit(-1)

	@staticmethod
	def setup_parser(parser):
		sub_parser = parser.add_subparsers()
		netu_parser = sub_parser.add_parser('netu')

        netu_parser.add_argument('--num-frags', action="store", type=custom_range, required=True, help="Number of fragments")
        netu_parser.add_argument('--num-nums', action="store", type=custom_range, required=True, help="Number of 'Num'")
        netu_parser.add_argument('--stitch', action="store_true", default=False, help="Stitch the results together - ONLY for frag mode")
		netu_parser.set_defaults(func=NetuDownloader.main)

		return parser;

	@staticmethod
	def stitch(out_path_base, args.prefix):
		pass

	@staticmethod
	def main(args):
		frag_download(args, out_path_base, urls, results)
		if args.stitch is True:
			stitch_cmdline = 'stitch.sh %s %s' % (out_path_base, args.prefix).split(' ')
			p = subprocess.Popen(stitch_cmdline)
			p.wait()
