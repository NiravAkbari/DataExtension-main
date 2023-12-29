# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
from copy import deepcopy, copy
from typing import (
    List,
    Set,
    Dict,
    Tuple,
    Union,
    Optional,
    NewType,
    Callable,
    Iterator,
    Pattern,
    Match,
    Type,
)
from xml.dom import Node
from xml.dom.minidom import Attr, NamedNodeMap
from html5lib import HTMLParser as _HTMLParser
from lxml import etree as et, html as lh
from lxml.html import (
    HtmlElement,
    HtmlComment,
    HtmlEntity,
    HtmlProcessingInstruction,
    LabelElement,
    InputElement,
    SelectElement,
    TextareaElement,
    FormElement,
    HTMLParser,
    XHTMLParser,
    HtmlElementClassLookup
)

from lxml.etree import (ElementBase, _ElementStringResult,
                        _ElementUnicodeResult, XPath, tostring)

from lxml.html.html5parser import (
    _find_tag,
    _strings,
    document_fromstring as document_fromstring_html5,
    _contains_block_level_tag,
)

from domparser.common import *
from domparser.html5_builder import TreeBuilder as TB5
from functools import partial

_DOMElement = Type["DOMElement"]


class DomElementUnicodeResult(object):
    CDATA_SECTION_NODE = Node.CDATA_SECTION_NODE
    ELEMENT_NODE = Node.ELEMENT_NODE
    TEXT_NODE = Node.TEXT_NODE

    def __init__(self, text):
        self.text = text
        self.nodeType = Node.TEXT_NODE

    @property
    def data(self):
        if isinstance(self.text, _ElementUnicodeResult):
            return self.text
        else:
            raise RuntimeError


class DomTextNode(object):
    CDATA_SECTION_NODE = Node.CDATA_SECTION_NODE
    ELEMENT_NODE = Node.ELEMENT_NODE
    TEXT_NODE = Node.TEXT_NODE

    def __init__(self, text):
        self.data = text
        self.nodeType = Node.TEXT_NODE


def lxmlDomNodeType(node):
    if isinstance(node, ElementBase):
        return Node.ELEMENT_NODE

    elif isinstance(node, (_ElementStringResult, _ElementUnicodeResult)):
        if node.is_attribute:
            return Node.ATTRIBUTE_NODE
        else:
            return Node.TEXT_NODE
    else:
        return Node.NOTATION_NODE


class XmlDomMixin(object):
    CDATA_SECTION_NODE = Node.CDATA_SECTION_NODE
    ELEMENT_NODE = Node.ELEMENT_NODE
    TEXT_NODE = Node.TEXT_NODE

    _xp_childrennodes = XPath('child::node()')

    @property
    def documentElement(self):
        return self.getroottree().getroot()

    @property
    def nodeType(self):
        return Node.ELEMENT_NODE

    @property
    def nodeName(self):
        # FIXME: this is a simpification
        return self.tag

    @property
    def tagName(self):
        return self.tag

    @property
    def localName(self):
        return self.xpath('local-name(.)')

    def hasAttribute(self, name):
        return name in self.attrib

    def getAttribute(self, name):
        return self.get(name)

    def setAttribute(self, name, value):
        self.set(name, value)

    def cloneNode(self, deep):
        return deepcopy(self) if deep else copy(self)

    @property
    def attributes(self):
        attrs = {}
        for name, value in self.attrib.items():
            a = Attr(name)
            a.value = value
            attrs[name] = a
        return NamedNodeMap(attrs, {}, self)

    @property
    def parentNode(self):
        return self.getparent()

    @property
    def childNodes_xpath(self):
        for n in self._xp_childrennodes(self):

            if isinstance(n, ElementBase):
                yield n

            elif isinstance(n, (_ElementStringResult, _ElementUnicodeResult)):

                if isinstance(n, _ElementUnicodeResult):
                    n = DomElementUnicodeResult(n)
                else:
                    n.nodeType = Node.TEXT_NODE
                    n.data = n
                yield n

    @property
    def childNodes(self):
        if self.text:
            yield DomTextNode(self.text)
        for n in self.iterchildren():
            yield n
            if n.tail:
                yield DomTextNode(n.tail)

    def getElementsByTagName(self, name):
        return self.iterdescendants(name)

    def getElementById(self, i):
        return self.get_element_by_id(i)

    @property
    def data(self):
        if isinstance(self, (_ElementStringResult, _ElementUnicodeResult)):
            return self
        else:
            raise RuntimeError

    def toxml(self, encoding=None):
        return tostring(self, encoding=encoding if encoding is not None
            else 'unicode')


class DomMixin(object):

    def _init(self):
        super(DomMixin, self)._init()

        self._span = None
        self._ents = None
        self._xpath = None
        self._span_start = 0
        self._span_end = 0
        self.refresh_xpath = True

    def _setSpan(self, span):
        self._span = span

    def _getSpan(self):
        return self._span

    span = property(_getSpan, _setSpan)

    def _setEnts(self, ents):
        self._ents = ents

    def _getEnts(self):
        return self._ents

    entities = ents = property(_getEnts, _setEnts)

    @property
    def nstag(self) -> str:
        return self.tag

    @property
    def tag_without_ns(self) -> str:
        return self.tag.split('}')[-1] # strip ns

    def _setXPath(self, xpath):
        self._xpath = xpath

    def _xpath_str(self) -> str:
        if self.refresh_xpath or self._xpath is None:
            self._xpath = self.getroottree().getpath(self)
        return self._xpath

    xpath_str = property(_xpath_str, _setXPath)

    def get_xpath(self, refresh=True) -> str:
        self.refresh_xpath = refresh
        return self.xpath_str

    css = HtmlElement.cssselect

    def jquery(self, expr):
        from domparser.cssselect import JQuerySelector
        return JQuerySelector(expr)(self)


    def children_of_parent(self) -> List[_DOMElement]:
        return self.getparent().getchildren()

    def children_of_all_parent(self):
        for parent in self.iterancestors():
            yield (parent, parent.getchildren())

    def get_index(self, element: _DOMElement) -> int:
        return self.index(element)

    def my_index_by_tag(self) -> int:
        p = self.getparent()
        if p is None:
            return 0
        childs = p.getchildren()
        if childs is not None and len(childs)>1:
            i=1
            for n in childs:
                if self == n:
                    return i
                if self.tag == n.tag:
                    i += 1
            return i
        else:
            return 0

    @property
    def my_index(self) -> int:
        p = self.getparent()
        return p.index(self) if p is not None else 0

    @property
    def all_parent(self) -> List[_DOMElement]:
        return list(self.iterancestors())

    @property
    def parent(self) -> _DOMElement:
        return self.getparent()

    @property
    def children(self) -> List[_DOMElement]:
        return self.getchildren()

    @property
    def tree(self) -> et.ElementTree:
        return self.getroottree()

    @property
    def root(self) -> _DOMElement:
        return self.tree.getroot()

    def tostring(self, method="html") -> str:
        return et.tostring(self, encoding="unicode", method=method, with_tail=False)

    @property
    def outer_html(self) -> str:
        return self.tostring()

    @property
    def inner_html(self) -> str:
        return "".join([str(c) if type(c) == et._ElementUnicodeResult else c.tostring() for c in self.xpath("node()")]).strip()

    def all_text(
        self, sep=" ", handle_whitespace="STRIP", whitespaces=["\n", "\r"], **kwargs
    ) -> str:
        """Returns the text content of the element."""

        # NOTE:
        #  - element.itertext returns comment text
        #  - html.tostring() or etree.tostring() would not support the
        #    separator options
        #  - Suggested way `.//text()` which seems sufficient.
        text = sep.join(
            self.xpath(
                ".//text()[not(ancestor::head|ancestor::title|ancestor::noscript|ancestor::script|ancestor::style|ancestor::link)]"
            )
        )
        if handle_whitespace == "STRIP":
            text = text.strip()
        elif handle_whitespace == "NORMALIZED":
            text = normalize_whitespace(text)
        elif handle_whitespace == "REPLACE":
            text = re.sub(
                r"[%s]" % ("".join(whitespaces)), " ", text, flags=re.UNICODE
            ).strip()
        return text


class DOMComment(XmlDomMixin, DomMixin, HtmlComment):
    pass


class DOMElement(XmlDomMixin, DomMixin, HtmlElement):
    pass


class DOMPI(XmlDomMixin, DomMixin, HtmlProcessingInstruction):
    pass


class DOMEntity(XmlDomMixin, DomMixin, HtmlEntity):
    pass

class DOMFormElement(XmlDomMixin, DomMixin, FormElement):
    pass

class DOMTextareaElement(XmlDomMixin, DomMixin, TextareaElement):
    pass

class DOMSelectElement(XmlDomMixin, DomMixin, SelectElement):
    pass

class DOMInputElement(XmlDomMixin, DomMixin, InputElement):
    pass

class DOMLabelElement(XmlDomMixin, DomMixin, LabelElement):
    pass


class DOMElementClassLookup(et.CustomElementClassLookup):
    """A lookup scheme for HTML Element classes.

    To create a lookup instance with different Element classes, pass a tag
    name mapping of Element classes in the ``classes`` keyword argument and/or
    a tag name mapping of Mixin classes in the ``mixins`` keyword argument.
    The special key '*' denotes a Mixin class that should be mixed into all
    Element classes.
    """

    _default_element_classes = {'form': DOMFormElement,
                                'textarea': DOMTextareaElement,
                                'select': DOMSelectElement,
                                'input': DOMInputElement,
                                'label': DOMLabelElement}

    def __init__(self, classes=None, mixins=None):
        et.CustomElementClassLookup.__init__(self)
        if classes is None:
            classes = self._default_element_classes.copy()
        if mixins:
            mixers = {}
            for name, value in mixins:
                if name == "*":
                    for n in classes.keys():
                        mixers.setdefault(n, []).append(value)
                else:
                    mixers.setdefault(name, []).append(value)
            for name, mix_bases in mixers.items():
                cur = classes.get(name, DOMElement)
                bases = tuple(mix_bases + [cur])
                classes[name] = type(cur.__name__, bases, {})
        self._element_classes = classes

    def lookup(self, node_type, document, namespace, name):

        if node_type == "element":
            return self._element_classes.get(name.lower(), DOMElement)
        elif node_type == "comment":
            return DOMComment
        elif node_type == "PI":
            return DOMPI
        elif node_type == "entity":
            return DOMEntity
        else:
            print(node_type)
        return None


class SmartHTMLParser(et.HTMLParser):
    """An HTML parser that is configured to return lxml.html Element
    objects.
    """

    def __init__(self, **kwargs):
        super(SmartHTMLParser, self).__init__(**kwargs)

        parser_lookup = DOMElementClassLookup()
        self.set_element_class_lookup(parser_lookup)


class SmartXHTMLParser(et.XMLParser):
    """An XML parser that is configured to return lxml.html Element
    objects.

    Note that this parser is not really XHTML aware unless you let it
    load a DTD that declares the HTML entities.  To do this, make sure
    you have the XHTML DTDs installed in your catalogs, and create the
    parser like this::

        >>> parser = XHTMLParser(load_dtd=True)

    If you additionally want to validate the document, use this::

        >>> parser = XHTMLParser(dtd_validation=True)

    For catalog support, see http://www.xmlsoft.org/catalog.html.
    """

    def __init__(self, **kwargs):
        super(SmartXHTMLParser, self).__init__(**kwargs)
        parser_lookup = DOMElementClassLookup()
        self.set_element_class_lookup(parser_lookup)


class SmartHTMLParser5(_HTMLParser):
    """An html5lib HTML parser with lxml as tree."""

    def __init__(self, strict=False, namespaceHTMLElements=False, **kwargs):
        _HTMLParser.__init__(
            self,
            TB5,
            strict=strict,
            namespaceHTMLElements=namespaceHTMLElements,
            **kwargs,
        )
        self.tree.fromstring = partial(lh.fromstring, parser=SmartHTMLParser())



def html5_xhtml5_df2(html, base_url=None, parser=None, encoding=None):
    """Parse the html, returning a single element/document.

    This tries to minimally parse the chunk of text, without knowing if it
    is a fragment or a document.

    'base_url' will set the document's base_url attribute (and the tree's
    docinfo.URL)

    If `guess_charset` is true, or if the input is not Unicode but a
    byte string, the `chardet` library will perform charset guessing
    on the string.
    """
    if not isinstance(html, _strings):
        raise TypeError("string required")
    if parser is None:
        raise TypeError("parser required")

    parser.tree.fromstring = partial(
        lh.fromstring, parser=SmartHTMLParser(), base_url=base_url
    )
    doc = document_fromstring_html5(html, parser=parser)

    # document starts with doctype or <html>, full document!
    start = html[:50]
    if isinstance(start, bytes):
        # Allow text comparison in python3.
        # Decode as ascii, that also covers latin-1 and utf-8 for the
        # characters we need.
        start = start.decode("ascii", "replace")

    start = start.lstrip().lower()
    if start.startswith("<html") or start.startswith("<!doctype"):
        return doc

    head = _find_tag(doc, "head")

    # if the head is not empty we have a full document
    if len(head):
        return doc

    body = _find_tag(doc, "body")

    # The body has just one element, so it was probably a single
    # element passed in
    if (
        len(body) == 1
        and (not body.text or not body.text.strip())
        and (not body[-1].tail or not body[-1].tail.strip())
    ):
        return body[0]

    # Now we have a body which represents a bunch of tags which have the
    # content that was passed in.  We will create a fake container, which
    # is the body tag, except <body> implies too much structure.
    if _contains_block_level_tag(body):
        body.tag = "div"
    else:
        body.tag = "span"
    return body
