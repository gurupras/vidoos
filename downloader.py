import urllib2 as urllib
from multiprocessing import Process, Queue, Pool, cpu_count
import os, sys, time, re, signal, argparse
import urlparse
import posixpath
import atexit

class Main:
    verbose = False

    def setup_parser(parser):
        parser.add_argument("--out", action="store", type=str, default=None, required=True, help="Path to store output")
        parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose output")
        parser.add_argument("--prefix", action="store", type=str, default='out', help="Prefix to use for output files. Default: out")
        parser.add_argument("--url", action="store", type=str, default=None, required=True, help="URL to use")
        return parser


    def main(argv):
        parser = argparse.ArgumentParser()
        setup_parser(parser)
        args   = parser.parse_args(argv[1:])

        out_path_base = args.out
        if not os.path.exists(out_path_base):
            os.makedirs(out_path_base)
        
        Downloader.verbose = args.verbose

        

if __name__ == "__main__":
    main(sys.argv)
