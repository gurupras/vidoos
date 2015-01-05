import urllib2
import os, sys, time, re
from multiprocessing import Process

class SimpleDownloader:
    verbose = False
    headers = {
            'User-Agent'      : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
            'Connection'      : 'keep-alive'
    }

	@staticmethod
	def setup_parser(parser):
		sub_parser = parser.add_subparsers()
		simple_parser = sub_parser.add_parser('simple')

        simple_parser.add_argument('--wget', action="store_true", default=False, help="Use wget instead of urllib2")
		simple_parser.set_defaults(func=SimpleDownloader.main)

		return parser;

	@staticmethod
	def wget_download(url, out_path):
		cmdline = 'wget -O %s %s' % (out_path, url)	#TODO: Give proper out path
		proc = subprocess.Popen(cmdline.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()

		if len(err) != 0:
			print err
			sys.exit(-1)

		lines_iterator = iter(proc.stdout.readline, "")
		for line in lines_iterator:
			print line.strip()

		return None


	@staticmethod
	def urllib_download(url):
		try:
            request  = urllib.Request(url)
            for key, value in Downloader.headers.iteritems():
                request.add_header(key, value)

            response = urllib.urlopen(request)

			out = open(out_path, 'wb')	#TODO: Give proper out path
            for b in response.read():
                out.write(b)
            out.close()
        except urllib.HTTPError as e:
            result = '%s :Failed!' % (url)
            print '    %s' % (e.__repr__())
            print '    %s' % (result)
			results.append(result)
            return

        result = '%s :Succeeded!' % (url)

	@staticmethod
	def main(args):
		if args.wget is True:
			wget_download(args.url, args.out)
		else:
			urllib_download(args.url, args.out)
