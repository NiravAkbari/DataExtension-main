from requests import Session as Sess
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from domparser.adapters.adapter import LocalFileAdapter, S3FileAdapter, FTPFileAdapter

# from hyper.contrib import HTTP20Adapter # to-do Add HTTP/2 support


class Session(Sess):
    def __init__(self):
        super(Session, self).__init__()
        # Configure retries
        retry = Retry(total=3, backoff_factor=1)
        http_adapter = HTTPAdapter(max_retries=retry)
        # http2_adapter = HTTP20Adapter(max_retries=retry) # to-do Add HTTP/2 support

        self.mount("file://", LocalFileAdapter())
        self.mount("ftp://", FTPFileAdapter())
        self.mount("http://", http_adapter)
        self.mount("https://", http_adapter)
        self.mount("s3://", S3FileAdapter())
