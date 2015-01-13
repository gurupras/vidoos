import os, sys, time, re, signal, argparse

from netu import NetuDownloader
from simple_downloader import SimpleDownloader
from allmyvideos import AllMyVideosDownloader

class Downloader:
	verbose = False

	@staticmethod
	def setup_parser(parser):
		subparsers = parser.add_subparsers(dest='command', title='subcommands', description='Type of downloader', help='Type of downloader to use')
		# Add the subparsers
		NetuDownloader.setup_parser(subparsers)
		SimpleDownloader.setup_parser(subparsers)
		AllMyVideosDownloader.setup_parser(subparsers)

		return parser


	@staticmethod
	def main(argv):
		parser = argparse.ArgumentParser(add_help=False)
		Downloader.setup_parser(parser)
		args   = parser.parse_args(argv[1:])

		out_path_base = args.out
		if not os.path.exists(out_path_base):
			os.makedirs(out_path_base)

		Downloader.verbose = args.verbose

		args.func(args)



if __name__ == "__main__":
	Downloader.main(sys.argv)
