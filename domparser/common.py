import re
import copy
from lxml.etree import Comment
from domparser.utils import simplify_xpath
from typing import (
    List,
    Dict,
    Union,
    Optional,
    IO
)
from domparser.parser import DOMElement
xml_regex = re.compile(r"^\s*(<\?xml[^>]*?>)", flags=re.S | re.I | re.U).match
xml_html4_regex = re.compile(
    r"^\s*(<\?xml[^>]*?>)\s*(<!DOCTYPE[^>]*?>)?\s*(<html[^>]*?>)",
    flags=re.S | re.I | re.U,
).match
xhtml_doctype_regex = re.compile(
    r"^\s*(<!DOCTYPE[^>]*?(?<=xhtml)[^>]*?>)\s*(<html[^>]*?(?<=xmlns)?[^>]*?>)",
    flags=re.S | re.I | re.U,
).match
xhtml5_regex = re.compile(
    r"^\s*(<!DOCTYPE\s+html\s*>)\s*(<html[^>]*?(?<=xmlns)[^>]*?>)",
    flags=re.S | re.I | re.U,
).match

html4_regex = re.compile(
    r"^\s*(<!DOCTYPE[^>]*?(?<=html 4)[^>]*?>)\s*(<html(?!\sxmlns)[^>]*?>)",
    flags=re.S | re.I | re.U,
).match
html5_regex = re.compile(
    r"^\s*(<!DOCTYPE\s+html\s*>)\s*(<html(?!\sxmlns)[^>]*?>)", flags=re.S | re.I | re.U
).match
html5_regex_2 = re.compile(
    r"^\s*(<!DOCTYPE\s+html\s*>).*?(<html(?!\sxmlns)[^>]*?>)", flags=re.S | re.I | re.U
).match

html_regex = re.compile(r"^\s*(<html[^>]*?>)", flags=re.S | re.I | re.U).match

# </?\w+((\s+\w+(\s*=\s*(?:".*?"|'.*?'|[\^'">\s]+))?)+\s*|\s*)/?>
html_fragment_regex = re.compile(
    r"^\s*<[^>]*>.+</[^>]*>", flags=re.S | re.I | re.U
).match
SVG_XHTML_NAMESPACE = "http://www.w3.org/2000/svg"

# A regex matching the "invalid XML character range"
ILLEGAL_XML_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]"
)

NEWLINE_TAGS = frozenset(
    [
        "article",
        "aside",
        "br",
        "dd",
        "details",
        "div",
        "dt",
        "fieldset",
        "figcaption",
        "footer",
        "form",
        "header",
        "hr",
        "legend",
        "li",
        "main",
        "nav",
        "table",
        "tr",
        "td",
    ]
)
DOUBLE_NEWLINE_TAGS = frozenset(
    [
        "blockquote",
        "dl",
        "figure",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ol",
        "p",
        "pre",
        "title",
        "ul",
    ]
)
IGNORE_TAGS = frozenset(["noscript", "script", "style", Comment])
ignore_tags = ["head", "title", "noscript", "script", "style"]
WHITESPACE_NORMALIZED_RE = re.compile(r"\s+", flags=re.U)
WORD_RE = re.compile(r"\w+", flags=re.I | re.U).findall
APOS_RE = re.compile(r"\'", flags=re.U)

_space = re.compile(r" +", flags=re.U).sub
_whitespace = re.compile(r"\s+", flags=re.U).sub
TRAILING_WHITESPACE_RE = re.compile(r"^\s|\s$", flags=re.U).search
PUNCTUATION_SUFFIX_RE = re.compile(r'^[,:;.!?")]', flags=re.U).search
_punct_end = "[%s]$" % (re.escape(',:;.!?")|'))
PUNCTUATION_END_RE = re.compile(_punct_end, flags=re.U | re.S).search
BRACKET_PREFIX_RE = re.compile(r"\($", flags=re.U).search


def normalize_space(text: str) -> str:
    return _space(" ", text.strip())


def normalize_whitespace(text: str) -> str:
    return _whitespace(" ", text.strip())


def element_to_table(
    element: DOMElement,
    guess_punct_space: bool=True,
    guess_layout: bool=True,
    newline_tags: Union[List, None]=NEWLINE_TAGS,
    double_newline_tags: Union[List, None]=DOUBLE_NEWLINE_TAGS,
    ignore_tags: Union[List, None]=IGNORE_TAGS,
) -> List:
    # print('Ignore tags ',ignore_tags)
    if ignore_tags is None:
        ignore_tags = IGNORE_TAGS
        # print('Ignore tags ',ignore_tags)

    chunks = []
    chunks_info = []

    _NEWLINE = object()
    _DOUBLE_NEWLINE = object()

    class Context:
        """workaround for missing `nonlocal` in Python 2"""

        # _NEWLINE, _DOUBLE_NEWLINE or content of the previous chunk (str)
        prev = _DOUBLE_NEWLINE
        elem: Union[DOMElement, None] = None
        parents: List = []

    def should_add_space(text: str, prev: object) -> bool:
        """Return True if extra whitespace should be added before text"""
        if prev in {_NEWLINE, _DOUBLE_NEWLINE}:
            return False
        if not guess_punct_space:
            return True
        if not TRAILING_WHITESPACE_RE(prev):
            if PUNCTUATION_SUFFIX_RE(text) or BRACKET_PREFIX_RE(prev):
                return False
        return True

    def get_space_between(text: str, prev: object) -> str:
        if not text:
            return " "
        return " " if should_add_space(text, prev) else ""

    def add_newlines(tag: str, context: Context) -> None:
        if not guess_layout:
            return
        prev = context.prev
        if prev is _DOUBLE_NEWLINE:  # don't output more than 1 blank line
            return
        if tag in double_newline_tags:
            context.prev = _DOUBLE_NEWLINE
            chunks.append("\n" if prev is _NEWLINE else "\n\n")
        elif tag in newline_tags:
            context.prev = _NEWLINE
            if prev is not _NEWLINE:
                chunks.append("\n")

    def add_text(text_content: str, context: Context, is_tail: bool=False) -> None:
        text = normalize_whitespace(text_content) if text_content else ""
        if not text:
            return
        space = get_space_between(text, context.prev)
        element = context.elem

        if element.tag == "br" or is_tail:
            element: DOMElement = element.getparent()
        parent: DOMElement = element.getparent()
        all_parents = copy.deepcopy(context.parents)

        xpath = element.xpath_str
        prev_element: Union[DOMElement, None] = element.getprevious()
        prev_element_xpath = ""
        if prev_element is not None:
            prev_element_xpath = prev_element.xpath_str
        next_element: Union[DOMElement, None] = element.getnext()
        next_element_xpath = ""
        if next_element is not None:
            next_element_xpath = next_element.xpath_str

        chunks.extend(
            [
                {
                    "TEXT": text,
                    "ELEMENT": element.tag,
                    "XPATH": xpath,
                    "NORMALIZED_XPATH": simplify_xpath(xpath),
                    "PARENT": parent.tag if parent is not None else "",
                    "PREVIOUS_SIBILING": prev_element.tag if prev_element is not None else "",
                    "PREVIOUS_SIBILING_XPATH": prev_element_xpath,
                    "NEXT_SIBILING": next_element.tag if next_element is not None else "",
                    "NEXT_SIBILING_XPATH": next_element_xpath,
                    "ALL_PARENTS": " ".join(all_parents),
                }
            ]
        )
        context.prev = text_content

    def traverse_text_fragments(element: DOMElement, context: Context, handle_tail: bool=True) -> None:
        # import pdb

        """Extract text from the ``element``: fill ``chunks`` variable"""
        # print(type(element), element.tag)
        # print(context.parents)
        # if element.tag == 'h1':
        # pdb.set_trace()
        # print("=======**********************")
        if element.tag in ignore_tags:
            return
        parent: DOMElement = element.getparent()
        context.elem = element
        backup_parents = copy.deepcopy(context.parents)

        if element.tag != "br":
            context.parents.append(element.xpath_str)

        add_text(element.text, context)
        for child in element:
            if child.tag == Comment:
                if child.tail:
                    add_text(child.tail, context)
                continue

            context.elem = child
            traverse_text_fragments(child, context)

        if handle_tail and element.tail and element.tail.strip():
            context.elem = element
            add_text(element.tail, context, is_tail=True)
        context.parents = copy.deepcopy(backup_parents)

    traverse_text_fragments(element, context=Context(), handle_tail=True)

    # return ''.join(chunks).strip()
    return chunks


def element_to_text(
    element: DOMElement,
    guess_punct_space: bool=True,
    guess_layout: bool=True,
    newline_tags: Union[List, None]=NEWLINE_TAGS,
    double_newline_tags: Union[List, None]=DOUBLE_NEWLINE_TAGS,
    ignore_tags: Union[List, None]=IGNORE_TAGS,
) -> List:
    if ignore_tags is None:
        ignore_tags = IGNORE_TAGS

    chunks = []

    _NEWLINE = object()
    _DOUBLE_NEWLINE = object()

    class Context:
        """workaround for missing `nonlocal` in Python 2"""

        # _NEWLINE, _DOUBLE_NEWLINE or content of the previous chunk (str)
        prev = _DOUBLE_NEWLINE

    def should_add_space(text: str, prev: object):
        """Return True if extra whitespace should be added before text"""
        if prev in {_NEWLINE, _DOUBLE_NEWLINE}:
            return False
        if not guess_punct_space:
            return True
        if not TRAILING_WHITESPACE_RE(prev):
            if PUNCTUATION_SUFFIX_RE(text) or BRACKET_PREFIX_RE(prev):
                return False
        return True

    def get_space_between(text: str, prev: object):
        if not text:
            return " "
        return " " if should_add_space(text, prev) else ""

    def add_newlines(tag: str, context: Context):
        if not guess_layout:
            return
        prev = context.prev
        if prev is _DOUBLE_NEWLINE:  # don't output more than 1 blank line
            return
        if tag in double_newline_tags:
            context.prev = _DOUBLE_NEWLINE
            chunks.append("\n" if prev is _NEWLINE else "\n\n")
        elif tag in newline_tags:
            context.prev = _NEWLINE
            if prev is not _NEWLINE:
                chunks.append("\n")

    def add_text(text_content: str, context: Context):
        text = normalize_whitespace(text_content) if text_content else ""
        if not text:
            return
        space = get_space_between(text, context.prev)
        chunks.extend([space, text])
        context.prev = text_content

    def traverse_text_fragments(element: DOMElement, context: Context, handle_tail: bool=True):
        """Extract text from the ``element``: fill ``chunks`` variable"""
        if element.tag in ignore_tags:
            return
        add_newlines(element.tag, context)
        add_text(element.text, context)
        for child in element:
            if child.tag == Comment:
                if child.tail:
                    add_text(child.tail, context)
                continue
            traverse_text_fragments(child, context)
        add_newlines(element.tag, context)
        if handle_tail:
            add_text(element.tail, context)

    traverse_text_fragments(element, context=Context(), handle_tail=False)
    return chunks


def is_text_substring_in_list(txt: str, txt_list: List[str]) -> bool:
    is_substr = False
    for txt_i in txt_list:
        if txt == txt_i:
            continue
        elif txt in txt_i and txt != txt_i:
            is_substr = True
            break
    return is_substr


def remove_control_characters(html: str):
    """
    Strip invalid XML characters that `lxml` cannot parse.
    """

    # See: https://github.com/html5lib/html5lib-python/issues/96
    #
    # The XML 1.0 spec defines the valid character range as:
    # Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
    #
    # We can instead match the invalid characters by inverting that range into:
    # InvalidChar ::= #xb | #xc | #xFFFE | #xFFFF | [#x0-#x8] | [#xe-#x1F] | [#xD800-#xDFFF]
    #
    # Sources:
    # https://www.w3.org/TR/REC-xml/#charsets,
    # https://lsimons.wordpress.com/2011/03/17/stripping-illegal-characters-out-of-xml-in-python/

    def strip_illegal_xml_characters(s, default, base=10):
        # Compare the "invalid XML character range" numerically
        n = int(s, base)
        if (
            n in (0xB, 0xC, 0xFFFE, 0xFFFF)
            or 0x0 <= n <= 0x8
            or 0xE <= n <= 0x1F
            or 0xD800 <= n <= 0xDFFF
        ):
            return ""
        return default

    ctrl_chars = ["\f", "\r", "\v"]
    for char in ctrl_chars:
        html = html.replace(char, "")
    # return html
    # We encode all non-ascii characters to XML char-refs, so for example "💖" becomes: "&#x1F496;"
    # Otherwise we'd remove emojis by mistake on narrow-unicode builds of Python
    html = html.encode("ascii", "xmlcharrefreplace").decode("utf-8")
    html = re.sub(
        r"&#(\d+);?",
        lambda c: strip_illegal_xml_characters(c.group(1), c.group(0)),
        html,
    )
    html = re.sub(
        r"&#[xX]([0-9a-fA-F]+);?",
        lambda c: strip_illegal_xml_characters(c.group(1), c.group(0), base=16),
        html,
    )
    html = ILLEGAL_XML_CHARS_RE.sub("", html)
    return html
