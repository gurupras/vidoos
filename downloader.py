import urllib2 as urllib
from multiprocessing import Process, Queue, Pool, cpu_count
import os, sys, time, re, signal, argparse
import urlparse
import posixpath
import atexit

class Downloader:
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
    def download(url, out_path, result_list):
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
            result_list.append(result)
            print '    %s' % (e.__repr__())
            print '    %s' % (result)
            return
        result = '%s :Succeeded!' % (filename)
        result_list.append(result)
        print result


def download(*args):
    Downloader.download(*args)

def setup_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", action="store", type=str, default=None, required=True, help="Path to store output")
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose output")
    parser.add_argument("--prefix", action="store", type=str, default='out', help="Prefix to use for output files. Default: out")
    parser.add_argument("--url", action="store", type=str, default=None, required=True, help="URL to use")
    parser.add_argument("--type", action="store", type=str, choices=['frag'], default='frag', help="Select which download logic to apply. Default: frag")
    parser.add_argument('--num-frags', action="store", type=int, help="Number of fragments")
    parser.add_argument('--num-nums', action="store", type=int, help="Number of 'Num'")
    parser.add_argument('--stitch', action="store_true", default=False, help="Stitch the results together - ONLY for frag mode")
    return parser


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
            Downloader.pool.apply_async(download, [url, out_path, results]).get(99999)
#            Downloader.download(url, out_path, results)

    Downloader.pool.close()
    Downloader.pool.join()

    return urls, results

@atexit.register
def kill_subprocesses(signal=None, frame=None):
    try:
        Downloader.pool.terminate()
    except Exception:
        pass


def main(argv):
    parser = setup_parser()
    args   = parser.parse_args(argv[1:])

    out_path_base = args.out
    if not os.path.exists(out_path_base):
        os.makedirs(out_path_base)
    
    Downloader.verbose = args.verbose

    urls    = []
    results = []
    if args.type == 'frag':
        frag_download(args, out_path_base, urls, results)
        if args.stitch is True:
            stitch_cmdline = 'stitch.sh %s %s' % (out_path_base, args.prefix).split(' ')
            p = Subprocess.Popen(stitch_cmdline)
            p.wait()


    f = open('log.txt', 'wb')
    results.sort()
    for item in results:
        f.write(item)
    f.close()
    

if __name__ == "__main__":
    main(sys.argv)
