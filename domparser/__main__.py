# -*- coding: utf-8 -*-
from __future__ import absolute_import
from domparser.dom import DOM
from typing import IO, Union
from requests import get
from urllib.parse import urlparse
import click
from pathlib import Path

def url_check(url: str) -> bool:

    try:
        result = urlparse(url)
        if all([result.scheme, result.netloc]):
            return True
        else:
            return False
    except:
        return False


def get_html_from_url(url: str) -> str:
    _headers = {
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Site": "same-origin",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Accept-Language": "en-US",
    }
    _resp = get(url=url, headers=_headers, verify=True)
    _resp.raise_for_status()
    if "Content-Type" in _resp.headers:
        if (
            "xml" not in _resp.headers["Content-Type"]
            and "html" not in _resp.headers["Content-Type"]
        ):
            raise ValueError(
                "Web response should be HTML/XML. Received content-type is %s"
                % (_resp.headers["Content-Type"])
            )

    return _resp.text


def get_html_from_file(fp: IO) -> str:
    if not (hasattr(fp, "read") and hasattr(fp, "write")):
        raise ValueError("Expected File object")
    return fp.read()


def get_dom(path: Union[str, IO]) -> DOM:
    html_content = None
    if isinstance(path, str) and url_check(url=path):
        html_content = get_html_from_url(path)
    elif hasattr(path, "read") and hasattr(path, "write"):
        html_content = get_html_from_file(path)
    else:
        raise ValueError("Valid arguments are URL/File-like object")
    return DOM(document_content=html_content)


def get_xpath_by_text(path: Union[str, IO], text: str) -> str:
    webdom = get_dom(path)
    for xp in webdom.get_xpath_by_text(text):
        return xp


def get_xpath_by_partial_text(path: Union[str, IO], partial_text: str) -> str:
    webdom = get_dom(path)
    for xp in webdom.get_xpath_by_partial_text(partial_text):
        return xp


@click.command()
@click.option("--url", "url", required=True, help="URL")
@click.option("--text", "search_text", required=True, help="Search Text")
def extract_xpath_from_url(url: str, search_text: str) -> str:
    return get_xpath_by_partial_text(url, search_text)


@click.command()
@click.option("--fp", "file_path", required=True, help="file path")
@click.option("--text", "search_text", required=True, help="Search Text")
def extract_xpath_from_file(file_path, search_text: str) -> str:
    with open(file_path, "r") as fp:
        return get_xpath_by_partial_text(fp, search_text)


@click.command()
@click.option("--fp", "file_path", type=click.Path(), required=True, help="file path")
@click.option(
    "--handle-whitespace",
    "handle_whitespace",
    type=click.Choice(["STRIP", "NORMALIZED", "REPLACE"]),
    default="NORMALIZED",
    required=True,
    help="Handle Whitespace",
)
def html_to_text(file_path: Path, handle_whitespace: str) -> str:
    with open(file_path, "r") as fp:
        webdom = get_dom(fp)
        el = webdom.one("//body", None)
        return el.text(handle_whitespace=handle_whitespace)


if __name__ == "__main__":
    extract_xpath_from_url()
