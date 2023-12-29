import os, sys, re
import codecs
import pathlib

from urllib.parse import urlsplit
from urllib3.util.url import parse_url, LocationParseError
from functools import partial
import requests.utils as req_ut

# monkeypatch requests
from requests.utils import should_bypass_proxies
from domparser.adapters.exception import GWCError




on_win = bool(sys.platform == "win32")
on_mac = bool(sys.platform == "darwin")
on_linux = bool(sys.platform == "linux")

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
FILESYSTEM_ENCODING = sys.getfilesystemencoding()


def hex_octal_to_int(ho):
    ho = ord(ho)
    o0 = ord("0")
    o9 = ord("9")
    oA = ord("A")
    oF = ord("F")
    res = (
        ho - o0
        if ho >= o0 and ho <= o9
        else (ho - oA + 10)
        if ho >= oA and ho <= oF
        else None
    )
    return res


def should_bypass_proxies_patched(should_bypass_proxies_func, url, no_proxy=None):
    # Monkey patch requests, per https://github.com/requests/requests/pull/4723
    if url.startswith("file://"):
        return True
    try:
        return should_bypass_proxies_func(url, no_proxy)
    except TypeError:
        # For versions of requests we shouldn't have to deal with.
        # https://github.com/conda/conda/issues/7503
        # https://github.com/conda/conda/issues/7506
        return should_bypass_proxies_func(url)


req_ut.should_bypass_proxies = partial(
    should_bypass_proxies_patched, should_bypass_proxies
)

file_scheme = "file://"

PATH_MATCH_REGEX = (
    r"\./"  # ./
    r"|\.\."  # ..
    r"|~"  # ~
    r"|/"  # /
    r"|[a-zA-Z]:[/\\]"  # drive letter, colon, forward or backslash
    r"|\\\\"  # windows UNC path
    r"|//"  # windows UNC path
)


def is_path(value):
    if "://" in value:
        return False
    return re.match(PATH_MATCH_REGEX, value)


def urlparse(url):
    if on_win and url.startswith("file:"):
        url.replace("\\", "/")
    return parse_url(url)


def abs_to_url(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def url_to_path(url):
    """Convert a file:// URL to a path.

    Relative file URLs (i.e. `file:relative/path`) are not supported.
    """

    if is_path(url):
        return url
    if not url.startswith("file://"):  # pragma: no cover
        raise GWCError(
            "You can only turn absolute file: urls into paths (not %s)" % url
        )
    _, netloc, path, _, _ = urlsplit(url)

    path = percent_decode(path)
    if netloc not in ("", "localhost", "127.0.0.1", "::1"):
        if not netloc.startswith("\\\\"):
            # The only net location potentially accessible is a Windows UNC path
            netloc = "//" + netloc
    else:
        netloc = ""
        # Handle Windows drive letters if present
        if re.match("^/([a-z])[:|]", path, re.I):
            path = path[1] + ":" + path[3:]
    return netloc + path


def percent_decode(path):

    # This is not fast so avoid when we can.
    if "%" not in path:
        return path
    ranges = []
    for m in re.finditer(r"(%[0-9A-F]{2})", path):
        ranges.append((m.start(), m.end()))
    if not len(ranges):
        return path

    # Sorry! Correctness is more important than speed at the moment.
    # Should use a map + lambda eventually.
    result = b""
    skips = 0
    for i, c in enumerate(path):
        if skips > 0:
            skips -= 1
            continue
        c = c.encode("ascii")
        emit = c
        if c == b"%":
            for r in ranges:
                if i == r[0]:
                    import struct

                    emit = struct.pack(
                        "B",
                        hex_octal_to_int(path[i + 1]) * 16
                        + hex_octal_to_int(path[i + 2]),
                    )
                    skips = 2
                    break
        if emit:
            result += emit
    return codecs.utf_8_decode(result)[0]


def url_to_s3_info(url):
    """Convert an s3 url to a tuple of bucket and key.

    Examples:
        >>> url_to_s3_info("s3://bucket-name.bucket/here/is/the/key")
        ('bucket-name.bucket', '/here/is/the/key')
    """
    parsed_url = parse_url(url)
    assert parsed_url.scheme == "s3", "You can only use s3: urls (not %r)" % url
    bucket, key = parsed_url.host, parsed_url.path
    return bucket, key


def is_url(url):
    """
    Examples:
        >>> is_url(None)
        False
        >>> is_url("s3://some/bucket")
        True
    """
    if not url:
        return False
    try:
        return urlparse(url).scheme is not None
    except LocationParseError:
        return False


def ensure_binary(value):
    try:
        return value.encode("utf-8")
    except AttributeError:  # pragma: no cover
        # AttributeError: '<>' object has no attribute 'encode'
        # In this case assume already binary type and do nothing
        return value
