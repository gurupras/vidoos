import urllib2 as urllib
import requests
import argparse
import os, sys, time, re
import multiprocessing
from multiprocessing import Process
import subprocess
import shlex

import pycommons

class CurlAction(argparse.Action):
	def __call__(self, parser, args, values, option_string=None):
		tokens = shlex.split(values)
		headers = []
		idx = 0
		while idx < len(tokens):
			v = tokens[idx]
			if v == '-H':
				# Header..add to headers
				headers.append(tokens[idx + 1])
			if v == 'curl':
				url = tokens[idx + 1]
			idx += 1

		for h in headers:
			name, value = [x.strip() for x in h.split(':', 1)]
			SimpleDownloader.headers[name] = value
		setattr(args, 'url', url)


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
		simple_parser.add_argument("--url", action="store", type=str, default=None, help="URL to use")
		simple_parser.add_argument("--curl", action=CurlAction, type=str, default=None, help="cURL URL to use")

		simple_parser.add_argument('--wget', action="store_true", default=False, help="Use wget instead of urllib2")
		simple_parser.add_argument('-j', '--threads', type=int, default=1, help='Number of chunks to split into and download in parallel')
		simple_parser.add_argument('--buffer-size', action=pycommons.SizeAction, type=str, default='10M', help='Buffer Size')
		simple_parser.set_defaults(func=SimpleDownloader.main)

		return parser;

	@staticmethod
	def wget_download(url, out_path):
		cmdline = 'wget -O %s %s' % (out_path, url)	#TODO: Give proper out path
		proc = subprocess.Popen(cmdline.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = proc.communicate()

		lines_iterator = iter(proc.stdout.readline, "")
		for line in lines_iterator:
			print line.strip()

		lines_iterator = iter(proc.stderr.readline, "")
		for line in lines_iterator:
			print line.strip()

		return None


	@staticmethod
	def urllib_download(url, out, buffer_size, chunks):
		# First get total download size and then split it
		response = requests.head(url)
		size = int(response.headers['Content-Length'])
		start = 0
		chunk_size = size / chunks
		processes = []
		done = multiprocessing.Value('i', 0)
		progress_condition = multiprocessing.Value('i', 1)
		for c in range(chunks):
			# Start a download task
			if c == chunks - 1:
				end = size
			else:
				end = start + chunk_size
			custom_headers = {}
			custom_headers['Range'] = 'bytes=%d-%d' % (start, end)
			p = Process(target=SimpleDownloader._urllib_download, args=(url, out, buffer_size, start, end, done, custom_headers, c,))
			processes.append(p)
			#SimpleDownloader._urllib_download(url, out, start, end, custom_headers, c)
			start += chunk_size
		try:
			for p in processes:
				p.start()

			time.sleep(1)
			progress_proc = Process(target=SimpleDownloader.progress_handler, args=(out, done, size, progress_condition,))
			progress_proc.start()

			for p in processes:
				p.join(99999999999)
		except KeyboardInterrupt, e:
			raise e

		print 'All threads done..terminating progress thread'
		progress_condition.value = 0
		progress_proc.join(5)

		# Sync FS
		print 'sync() ...'
		with open(out) as f:
			os.fsync(f.fileno())

		print 'Done'

	@staticmethod
	def progress_handler(out, progress, total, condition):
		while condition.value == 1:
			#FIXME: Make this OS independent
			os.system('clear')
			print 'Downloading \'%s\' %d/%d (%d%%)' % (out, progress.value, total, ((progress.value * 100) / total))
			time.sleep(1)

	@staticmethod
	def _urllib_download(url, out, buffer_size, start, stop, shared_var, custom_headers={}, idx=-1):
		print 'Starting thread: %d' % (idx)
		try:
			headers = {}
			for key, value in SimpleDownloader.headers.iteritems():
				headers[key] = value
			for key, value in custom_headers.iteritems():
				headers[key] = value

			response = requests.get(url, headers=headers, stream=True)
			size = int(response.headers['content-length'])
			read = 0
			with open(out, 'w') as out:
				out.seek(start)
				size = stop - start
				remaining = size
				while remaining > 0:
					bs = buffer_size if buffer_size < remaining else remaining
					bytez = response.raw.read(bs)
					if not bytez:
						break
					out.write(bytez)
					read += len(bytez)
					remaining -= len(bytez)
					shared_var.value += len(bytez)

				assert read == size, "Read != size (%d != %d)" % (read, size)
		except urllib.HTTPError as e:
			result = '%s :Failed!' % (url)
			print '    %s' % (e.__repr__())
			print '    %s' % (result)
			#results.append(result)
			return

		result = '%s :Succeeded!' % (url)


	@staticmethod
	def main(args):
		out = '%s/%s' % (args.out, args.prefix)

		print 'Using buffer size: %d' % (args.buffer_size)

		if args.wget is True:
			SimpleDownloader.wget_download(args.url, out)
		else:
			SimpleDownloader.urllib_download(args.url, out, args.buffer_size, chunks=args.threads)


