from __future__ import absolute_import, print_function, annotations
from typing import (
    List,
    Dict,
    Union,
    Optional,
    IO
)


import copy
from difflib import SequenceMatcher

import pandas as pd
from bs4.dammit import UnicodeDammit, EncodingDetector
from html5lib.constants import namespaces
from lxml import etree
from lxml.etree import XMLParser, fromstring as xml_df, XPathError
from lxml.html import (
    XHTML_NAMESPACE,
    fromstring as html_xhtml_df,
    xhtml_to_html,
    tostring,
    document_fromstring,
    Classes
)
from lxml.html.clean import Cleaner
from lxml.cssselect import CSSSelector
from cssselect.parser import SelectorSyntaxError, SelectorError
from domparser.session import Session
from .clean5 import Cleaner as Cleaner5

from domparser.xpath_extension import *

from domparser.common import *
from domparser.exception import (
    XpathException,
    XpathReturnedNone,
    XpathReturnedMultiple,
    XpathMultipleParents,
    CSSSelectorException
)
from domparser.metadata import extract as metadata_extract
from domparser.parser import DOMElement, SmartHTMLParser, SmartHTMLParser5, html5_xhtml5_df2
from domparser.typing import HtmlParser
from urllib.parse import urljoin
import logging


logger = logging.getLogger(__name__)


class DOM(object):
    valid_document_parser: Dict[str, HtmlParser] = {
        "xml": XMLParser,
        "html": SmartHTMLParser,
        "xhtml": SmartHTMLParser,
        "html5": SmartHTMLParser5,
        "xhtml5": SmartHTMLParser5,
    }
    DEFAULT_REQUEST_HEADERS = {
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
    }  # type: Dict[str, str]

    remove_nodes_re = (
        "^side$|combx|retweet|mediaarticlerelated|menucontainer|"
        "navbar|storytopbar-bucket|utility-bar|inline-share-tools"
        "|comment|PopularQuestions|contact|foot|footer|Footer|footnote"
        "|cnn_strycaptiontxt|cnn_html_slideshow|cnn_strylftcntnt"
        "|links|meta$|shoutbox|sponsor"
        "|tags|socialnetworking|socialNetworking|cnnStryHghLght"
        "|cnn_stryspcvbx|^inset$|pagetools|post-attributes"
        "|welcome_form|contentTools2|the_answers"
        "|communitypromo|runaroundLeft|subscribe|vcard|articleheadings"
        "|date|^print$|popup|author-dropdown|tools|socialtools|byline"
        "|konafilter|KonaFilter|breadcrumbs|^fn$|wp-caption-text"
        "|legende|ajoutVideo|timestamp|js_replies"
    )  # type: Dict[str, str]
    logo_re = "logo|site-tagline|site-title|header-logo|"  # type: str
    breadcrumbs_re = "breadcrumbs|breadcrumb|BreadcrumbsButtons|"  # type: str
    cookie_re = "cookie-bar|cookie-notice|cookie-warning|"  # type: str
    menu_re = (
        "js-sticky-nav|nav-primary|nav-mobile|menu-item"
        "|popup-menu|js-menu|justin-popup|navtoggle"
        "|top-nav|main-nav|desktop-nav|nav-menu|^menu$"
        "|dropdown|navigation|mobile-menu|menu-main-menu"
        "|nav_menu|navbar-header|navbar-toggle|navbar-right"
        "|navbar-|navbar|primary-menu|side-nav|nav-links"
        "|NavLinks|^main_nav$|"
    )  # type: str
    header_re = (
        "header-contents|site-header|header-secondary-outer"
        "|site-header|site-header sticky|header-buttons"
        "|one_header_button|^header$|HeaderZone|headerLinks"
        "|^head_row$|"
    )  # type: str
    footer_re = (
        "footer-navigation|nav-footer|footer-bottom"
        "|site-footer|footer-menu|footer-location"
        "|footer-last|footer-start|site_footer|footer-widgets"
        "|footer-widget|wp-footer|page-footer|footer_links_column"
        "|footer_links|^footer$|footer-contact|FooterZone"
        "|footerCont|footerCol|^footer_row$|^footer_nav$"
        "|^footer_disclaimer$|^copyright$|"
    )  # type: str
    other_re = (
        "^brand$|^clear$|copyright|team-disclaimer|disclaimer"
        "|newsletter|social|search|side-trigger|batBeacon|scrollUp"
        "|to-top|apexnb-|instagram|search-outer|modal|recaptcha"
        "|covid19-container|covid19|contact-links|edz-ov-mask|edz-ov-body"
        "|edreamz-overlays|ad-ftaddblockersection|addblockersectionNew"
        "|ajaxFilter|banner|^aside$|lazyimage-anchor|^sidebar$|filters-|filter-bar"
        "|video-modal|slider-team|^slider$|slick-slide|slide_image"
        "|slick-prev|slick-arrow|slick-next|slick-list|prev|next"
        "|sdk_version|sdk_|_sdk|appointment|stayconnected|^pager$"
        "|BannerZone|SideZone|SideNavPanel|^address$|locations"
        "|sidepanel|aspNetHidden|headerSearch|headerFB|_gcse_"
        "|gsc-control|gsc-search|gsc-modal|gsc-results"
        "|site-top-bar|site-top-border|^cart$|cart-|^signin$"
        "|^PrintProfile$|^print|^practiceAddressContainer$"
        "|^practiceTimesContainer$|^practiceHoursDesktop$"
        "|address|hours|times|^login$|^news$|^survey(s)?$|^calendar$"
        "|^addthis_toolbox|^addthis_button|toolbar|flickr|paralax"
    )  # type: str
    combination_re = (
        logo_re
        + breadcrumbs_re
        + cookie_re
        + menu_re
        + header_re
        + footer_re
        + other_re
    )  # type: str

    regexp_namespace = "http://exslt.org/regular-expressions" # type: str

    primary_re = (
        "//*[re:test(@id, '%s', 'i') or re:test(@class, '%s', 'i') or re:test(@name, '%s', 'i')]"
        % (combination_re, combination_re, combination_re)
    )
    nauthy_ids_re = "//*[re:test(@id, '%s', 'i')]" % combination_re
    nauthy_classes_re = "//*[re:test(@class, '%s', 'i')]" % combination_re
    nauthy_names_re = "//*[re:test(@name, '%s', 'i')]" % combination_re
    role = "^navigation$|^banner$|^complimentary$|^search$|^button$|^combobox$|^listbox$|^option$|^presentation$|^dialog$"
    role_xpath_re = "//*[re:test(@role, '%s', 'i')]" % role

    div_to_p_re = r"<(a|blockquote|dl|div|img|ol|p|pre|table|ul)" # type: str
    caption_re = "^caption$" # type: str
    google_re = " google " # type: str
    entries_re = "^[^entry-]more.*$" # type: str
    facebook_re = "[^-]facebook" # type: str
    facebook_braodcasting_re = "facebook-broadcasting" # type: str
    twitter_re = "[^-]twitter" # type: str
    contains_article = 'self::body|.//body|.//main|.//figure|.//figcaption|.//article|.//*[@id="article"]|.//*[@itemprop="articleBody"]|.//*[@role="main"]|.//ancestor::*[@role="main"]|.//ancestor::*[@id="team"]|.//*[@id="team"]|.//*[contains(@class, "search-results")]|.//*[contains(@id, "search-results")]' # type: str
    _xpath_of_cleaned_elements = set()

    ALL_XPATHS_TO_REMOVE = "" # type: str
    HEADER_FOOTER_XPATH_RE = (
        "//head|//script|//style|//body/nav|//body/header|//body/footer"
        "|//nav[following-sibling::footer or following-sibling::article]"
        "|//header[following-sibling::footer or following-sibling::article]"
        "|//footer[preceding-sibling::header or preceding-sibling::article]"
        "|//aside[following-sibling::article or preceding-sibling::article]"
        "|//input[preceding-sibling::label]"
        "|//label[following-sibling::input]"
    ) # type: str

    EXTRA_UL_LI_XPATH_RE = (
        '//a[contains(@onclick,"scrollTop") or re:test(text(), "view more", "i")]'
        '|//ul[re:test(@class, "pagination", "i") or re:test(@id, "pagination", "i")]'
        '|//ul[re:test(@class, "filter", "i") or re:test(@id, "filter", "i")]'
        '|//div[re:test(@class, "pagination", "i") or re:test(@id, "pagination", "i")]'
        '|//ul[re:test(@class, "menu", "i") or re:test(@class, "nav", "i") or re:test(@class, "footer", "i")]'
        '|//nav[re:test(@class, "menu", "i") or re:test(@class, "nav", "i") or re:test(@class, "footer", "i")]'
        '|//li[re:test(@class, "menu", "i") or re:test(@class, "nav", "i") or re:test(@class, "footer", "i")]'
        '|//*//ul[re:test(string(), "about us", "i") or re:test(string(), "Career", "i") '
        'or re:test(string(), "contact us", "i") or re:test(string(), "contact", "i") '
        'or re:test(string(), "faq", "i") or re:test(string(), "blog", "i") '
        'or re:test(string(), "bill", "i") or re:test(string(), "pay", "i") '
        'or re:test(string(), "leadership", "i") or re:test(string(), "meet ", "i") '
        'or re:test(string(), "our team", "i") or re:test(string(), "team", "i")]'
        '|//*[re:test(text(), "design(ed)?\W+by", "i") or re:test(text(), "power(ed)?\W+by", "i")'
        ' or re:test(text(), "develop(ed)?\W+by", "i") or re:test(text(), "creat(ed)?\W+by", "i")'
        ' or re:test(text(), "host(ed)?\W+by", "i")]'
    ) # type: str

    # http://ceyuan.com/en/index.html
    SECTION_XPATH_RE = '//section[re:test(@id, "studio", "i") or re:test(@id, "works", "i") or re:test(@id, "contacts", "i") or re:test(@id, "feed", "i")]' # type: str

    # Not working //svg
    # //*[name()="svg"]
    SVG_XPATH_RE = '//*[local-name()="svg"]' # type: str

    # Comment due to weird cases
    # https://www.alpinvest.com/team

    # BUTTON_XPATH_RE = ('//button')
    ARIA_HIDDEN_XPATH_RE = '//*[@aria-hidden="true"]' # type: str

    SKIP_LINKS_XPATH_RE = '//a[re:test(string(), "Skip", "i") and re:test(string(), "Nav|Main|Content", "i")]' # type: str

    FORM_HIDDEN = '//form[contains(@style,"display:none;")]' # type: str

    ELEM_WITH_JSON_DATA = "//*[contains(text(),%s)]" % ("'" + '{"' + "'") # type: str

    ALL_XPATHS_TO_REMOVE = (
        HEADER_FOOTER_XPATH_RE
        + "|"
        + EXTRA_UL_LI_XPATH_RE
        + "|"
        + SECTION_XPATH_RE
        + "|"
        + SVG_XPATH_RE
        + "|"
        + ARIA_HIDDEN_XPATH_RE
        + "|"
        + SKIP_LINKS_XPATH_RE
        + "|"
        + FORM_HIDDEN
        + "|"
        + ELEM_WITH_JSON_DATA
        + "|"
        + primary_re
        + "|"
        + role_xpath_re
    ) # type: str

    # https://schema.org/Person
    # https://30a.beachpropertiesfla.com/agents/
    contains_person = (
        './/ancestor::*[@itemprop="employee"]|.//*[@itemprop="employee"]|'
        './/ancestor::*[@itemprop="name"]|.//*[@itemprop="name"]|'
        './/ancestor::*[@itemprop="jobTitle"]|.//*[@itemprop="jobTitle"]|'
        './/ancestor::*[@itemprop="telephone"]|.//*[@itemprop="telephone"]|'
        './/ancestor::*[@itemprop="address"]|.//*[@itemprop="address"]|'
        './/ancestor::*[@itemprop="email"]|.//*[@itemprop="email"]|'
        './/ancestor::*[@itemprop="url"]|.//*[@itemprop="url"]'
    ) # type: str

    def __init__(
        self,
        document_content: Optional[str] = None,
        parser: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs,
    ):

        self._document_type:str = "html"
        self._document_content: Union[str, None] = None
        self._document_content_bk: Union[str, None]  = None
        self._parser: Union[str, None] = parser
        self._tree_root: Union[DOMElement, None] = None
        self._clean_tree_root: Union[DOMElement, None]  = None
        self.clean_dom_as_default: bool = kwargs.get("clean_dom_as_default", False)
        self.base_url = base_url
        self._session: Union[Session, None] = kwargs.get("session", None)
        self.encoding: Union[str, None]  = kwargs.get("encoding", None)
        self.nsmap = copy.deepcopy(namespaces)
        self.nsmap.update({"x": XHTML_NAMESPACE})

        self._tree_root_cached: Union[List, List[DOMElement]] = []
        self._clean_tree_root_cached: Union[List, List[DOMElement]] = []

        self.content = document_content

    @classmethod
    def from_html_fragment(cls, fragment: str):
        return cls(document_content=fragment)

    @classmethod
    def from_url(cls, url: str):
        _session = Session()
        _resp = _session.get(
            url, headers=DOM.DEFAULT_REQUEST_HEADERS, verify=False, timeout=(30, 120)
        )
        _resp.raise_for_status()
        _dom_obj = cls(
            document_content=_resp.content, base_url=url, session=_session, encoding=_resp.encoding
        )
        return _dom_obj

    @classmethod
    def from_local(cls, file_obj: IO):
        if not (hasattr(file_obj, "read") and hasattr(file_obj, "write")):
            raise TypeError(
                "argument should be a valid File-like object and use encoding='utf-8'"
            )
        file_obj.seek(0)
        html_content = file_obj.read()
        return cls(document_content=html_content)

    @classmethod
    def get_unicode_html(cls, html:str, encoding:Union[str, None]=None):
        original_encoding = None
        declared_html_encoding = None
        if not html:
            return html, None, None

        if isinstance(html, str):
            declared_html_encoding = EncodingDetector(
                html, ["utf-8"], is_html=True
            ).find_declared_encoding(markup=html, is_html=True)
            return html, "utf-8", declared_html_encoding
        override_encodings = []
        if encoding:
            override_encodings.append(encoding)
        converted = UnicodeDammit(
            html, override_encodings=override_encodings, is_html=True
        )
        if not converted.unicode_markup:
            raise Exception(
                "Failed to detect encoding of article HTML, tried: %s"
                % ", ".join(converted.tried_encodings)
            )
        unicode_html = converted.unicode_markup
        declared_html_encoding = converted.declared_html_encoding
        original_encoding = converted.original_encoding
        if declared_html_encoding is None:
            declared_html_encoding = converted.detector.find_declared_encoding(
                markup=unicode_html, is_html=True
            )
        return (unicode_html, original_encoding, declared_html_encoding)

    def unset_clean_dom_as_default(self):
        self.clean_dom_as_default = False

    def set_clean_dom_as_default(self):
        self.clean_dom_as_default = True

    @property
    def tree(self):
        if self.clean_dom_as_default:
            element = self._clean_tree_root
            print(type(element), element.tag, id(element))
            return self._clean_tree_root

        else:
            element = self._tree_root
            print(type(element), element.tag, id(element))
            return self._tree_root

    @property
    def content(self):
        return self._document_content

    @content.setter
    def content(self, html_content: str):
        if html_content is None or (
            html_content is not None and not isinstance(html_content, (str, bytes))
        ):
            raise TypeError("content argument should be of type %s" % str)

        html_content = (
            html_content.strip() or "<html/>"
        )  # empty body raises error in lxml

        html_content, original_encoding, declared_html_encoding = DOM.get_unicode_html(
            html_content
        )
        # replaces &nbsp; entities with spaces
        html_content = html_content.replace("&nbsp;", " ")

        html_content = remove_control_characters(html_content)

        self._document_content_bk = self._document_content

        self._document_content = html_content
        if self._document_content is not None:
            _document_type = self.guess_document_type()
            assert (
                _document_type in self.valid_document_parser.keys()
                or _document_type == "html_fragment"
            ), "Invalid document type: {}".format(_document_type)
            self._document_type = _document_type
            self._method = (
                "xml" if ("xml" in self._document_type) else "html"
            )  # or "xhtml" in self._document_type
            self.build_root()

    def build_root(self):

        self._document_content = self._document_content.replace(
            "gcse:searchbox-only", "div"
        )
        if self._document_type in self.valid_document_parser.keys():
            for k, v in self.valid_document_parser.items():

                if self._document_type == k:
                    if k == "xhtml":
                        self._document_content = self._document_content.replace(
                            "</head>", "</head><body>"
                        )
                        self._document_content = (
                            self._document_content.replace(" async ", ' async="async" ')
                            .replace(" defer ", ' defer="defer" ')
                            .replace("tabindex=0", 'tabindex="0"')
                            .replace("<script>", '<script type="text/javascript" >')
                        )
                    if k == "xml":
                        parser = XMLParser(
                            load_dtd=True,
                            recover=True,
                            strip_cdata=False,
                            resolve_entities=False,
                        )
                    elif k == "html" or k == "xhtml":
                        parser = SmartHTMLParser(
                            recover=True, encoding="utf8", remove_blank_text=True, huge_tree=True
                        )
                    elif "5" in k:
                        parser = v(namespaceHTMLElements=False)
                    if k == "xml":
                        self._tree_root = xml_df(self._document_content, parser=parser)
                    elif k in ["html5", "xhtml5"]:
                        REPLACE_RE = re.compile(
                            r"<(link|meta)([^>]+?)(\/)?>", flags=re.I
                        )
                        self._document_content = REPLACE_RE.sub(
                            "<\\1 \\2 />", self._document_content
                        )
                        if k == "xhtml5":
                            REPLACE_RE = re.compile(
                                r"<(input)([^>]+?)(\/)?>", flags=re.I
                            )
                            self._document_content = REPLACE_RE.sub(
                                "<\\1 \\2 />", self._document_content
                            )


                        self._tree_root = _tree_root = html5_xhtml5_df2(
                            self._document_content,
                            parser=parser,
                            base_url=self.base_url,
                        )

                        xhtml_to_html(self._tree_root)

                        self._clean_tree_root = None
                    elif k in ["html", "xhtml"]:
                        REPLACE_RE = re.compile(
                            r"<(link|meta)([^>]+?)(\/)?>", flags=re.I
                        )
                        self._document_content = REPLACE_RE.sub(
                            "<\\1 \\2 />", self._document_content
                        )
                        if k == "xhtml":
                            REPLACE_RE = re.compile(
                                r"<(input)([^>]+?)(\/)?>", flags=re.I
                            )
                            self._document_content = REPLACE_RE.sub(
                                "<\\1 \\2 />", self._document_content
                            )
                        self._tree_root = html_xhtml_df(
                            self._document_content,
                            parser=parser,
                            base_url=self.base_url,
                        )
                        xhtml_to_html(self._tree_root)
                        self._clean_tree_root = None
                    break
        elif self._document_type == "html_fragment":
            parser = SmartHTMLParser(recover=True, encoding="utf8", remove_blank_text=True, huge_tree=True)
            self._tree_root = document_fromstring(
                self._document_content, parser=parser, base_url=self.base_url
            )
            self._clean_tree_root = None
        self._tree_root_cached = list(self._tree_root.getroottree().getroot().iter())
        self.clean_dom()
        self.set_clean_dom_as_default()

    def guess_document_type(self):

        if self._document_content is None or not self._document_content:
            raise ValueError(
                "Load document content first then try to guess document type"
            )
        clen = len(self._document_content)
        # MINI_LEN = 500
        MINI_LEN = max(2048, int(len(self._document_content) * 0.05))
        mini_content = self._document_content[: MINI_LEN if clen > MINI_LEN else clen]
        mini_content = mini_content.strip()
        # lxml does not play well with <? ?> encoding tags
        # <?xml version="1.0" encoding="utf-8"?>
        # <a><b/></a>
        if mini_content.startswith("<?"):
            mini_content = re.sub(r"^\<\?.*?\?\>", "", mini_content, flags=re.DOTALL)
            # ------ added by abhishek on 28/10/2021 ----------------
            # ------ for xml tag in html ----------------
            self._document_content = re.sub(
                r"^\<\?.*?\?\>", "", self._document_content, flags=re.DOTALL
            )
        elif mini_content.startswith("<!--"):
            mini_content = re.sub(
                r"^<!--[^<]*-->", "", mini_content, flags=re.DOTALL | re.M
            )
            # ------ added by abhishek on 28/10/2021 ----------------
            self._document_content = re.sub(
                r"^<!--[^<]*-->", "", self._document_content, flags=re.DOTALL | re.M
            )
            # mini_content = re.sub(r'^<!--((?!-->))*-->', '', mini_content.strip(), flags=re.DOTALL)
            # mini_content = re.sub(r'<!--(?!\s*(?:\[if [^\]]+]|))(?:(?!-->).)*-->', '', mini_content.strip(), flags=re.DOTALL)
        # print(mini_content)
        doctype = "html"
        if html5_regex(mini_content):
            doctype = "html5"
        elif html5_regex_2(mini_content):
            doctype = "html5"
        elif xhtml5_regex(mini_content):
            doctype = "xhtml5"
        elif xhtml_doctype_regex(mini_content):
            doctype = "xhtml"
        elif xml_html4_regex(mini_content):
            doctype = "xhtml"
        elif html4_regex(mini_content):
            doctype = "html"
        elif html_regex(mini_content):
            doctype = "html"
        elif xml_regex(mini_content):
            doctype = "xml"
            raise ValueError("XML content not supported")
        # elif xml_regex(mini_content):
        #     doctype = 'xml'
        elif html_fragment_regex(self._document_content):
            doctype = "html_fragment"
        else:
            doctype = "unknown"
            # raise ValueError("Invalid HTML content found")
        # print("Doctype: ", doctype)
        return doctype

    def restructure_html(self, html):
        pass

    @property
    def inner_html(self):
        assert self.tree is not None, "Dom tree is not set yet."
        return tostring(self.tree, encoding="unicode", method=self._method)

    def metadata(self):
        return metadata_extract(self.tree, self._document_content, base_url=self.base_url)

    def get_element(self, element: Union[DOMElement, None]):
        return self.tree if element is None else element

    def css(self, expr: str , element: Union[DOMElement, None]=None, **kwargs):
        """Wrapper for element.css(...)"""

        nmap = kwargs.get("namespaces", self.nsmap)
        namespaces = nmap
        translator = "xml" if self._document_type == "xml" else self._document_type.strip('5')
        selector = CSSSelector(expr, namespaces=namespaces, translator=translator)
        try:
            if element is not None:
                return selector(element)
            else:
                return selector(self.tree)
        except (XPathError, SelectorSyntaxError, SelectorError):
            raise CSSSelectorException(selector=expr, element=element)



    def xpath(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> Union[List[DOMElement], None]:
        """Wrapper for element.xpath(...)"""
        if xpath is None:
            raise ValueError("Xpath is mandatory")
        logger.debug("xpath: %s", xpath)
        nmap = kwargs.get("namespaces", self.nsmap)
        kwargs["namespaces"] = nmap
        try:
            if element is not None:
                return element.xpath(xpath, **kwargs)
            else:
                return self.tree.xpath(xpath, **kwargs)
        except XPathError:
            raise XpathException(xpath=xpath, element=element)

    def first(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> DOMElement:
        """
        Returns the first result of an xpath query or raises an
        XpathReturnedNone exception.
        """
        result = self.xpath(xpath, element, **kwargs)
        if not result:
            raise XpathReturnedNone(xpath, element)
        return result[0]

    def one(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> DOMElement:
        """
        Returns the only result of an xpath query, or raises an
        XpathReturnedNone or XpathReturnedMultiple exception.
        """
        result = self.xpath(xpath, element, **kwargs)
        if not result:
            raise XpathReturnedNone(xpath, element)
        if len(result) > 1:
            raise XpathReturnedMultiple(xpath, element)
        return result[0]

    def last(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> DOMElement:
        """
        Returns the last result of an xpath query or raises an
        XpathReturnedNone exception.
        """
        result = self.xpath(xpath, element, **kwargs)
        if not result:
            raise XpathReturnedNone(xpath, element)
        return result[-1]

    def first_or_none(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> Union[DOMElement, None]:
        """Returns the first result of an xpath query, or None."""
        try:
            return self.first(xpath, element, **kwargs)
        except XpathReturnedNone:
            return None

    def one_or_none(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> Union[DOMElement, None]:
        """
        Returns the only result of an xpath query or None. Raises
        XpathReturnedMultiple if multiple results are returned.
        """
        try:
            return self.one(xpath, element, **kwargs)
        except XpathReturnedNone:
            return None

    def last_or_none(self, xpath: str , element: Union[DOMElement, None]=None, **kwargs) -> Union[DOMElement, None]:
        """Returns the last result of an xpath query, or None."""
        try:
            return self.last(xpath, element, **kwargs)
        except XpathReturnedNone:
            return None

    def get_text_for_xpaths(self, xpaths: Union[List[str], str, None] = None, result_pos: str="first") -> Union[List[str], str]:
        if xpaths is None:
            raise ValueError("List of xpath is mandatory")

        if isinstance(xpaths, str):
            elems = self.xpath(xpath=xpaths)
            try:
                elem = elems[0]
                _text = self.text_formatted(elem)
                return _text
            except Exception as e:
                return ""
        elif isinstance(xpaths, list):
            all_text = []
            for xpath in xpaths:
                elems = self.xpath(xpath=xpath)
                try:
                    elem = elems[0]
                    _text = self.text_formatted(elem)
                    all_text.append(_text)
                except Exception as e:
                    all_text.append("")
            return all_text

    def text_as_table(
        self,
        element: Union[DOMElement, None] = None,
        sep:str = "",
        handle_whitespace:str = "STRIP",
        whitespaces: Union[List[str], None] = None,
        ignore_tags:Union[List[str], None] = None,
        word_count: Union[int, None] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Returns the text content of the element."""

        if whitespaces is None:
            whitespaces = ["\n", "\r", "\t"]

        element = self.get_element(element)

        allchunks = element_to_table(
            element
        )

        df = pd.DataFrame(allchunks)
        df.to_csv("htmltable.csv", index=False, encoding="utf-8-sig")
        return df

    def text_as_sentence(
        self,
        element: Union[DOMElement, None]=None,
        sep:str = "",
        handle_whitespace:str = "STRIP",
        whitespaces: Union[List[str], None] = None,
        ignore_tags:Union[List[str], None] = None,
        word_count: Union[int, None] = None,
        **kwargs,
    ):
        """Returns the text content of the element."""

        if whitespaces is None:
            whitespaces = ["\n", "\r", "\t"]

        element = self.get_element(element)

        chunks = element_to_text(
            element
        )

        if word_count:
            chunks = [ch for ch in chunks if float(len(WORD_RE(ch))) <= word_count]

        chunks = [
            ch + ". "
            if len(WORD_RE(ch.strip())) > 2 and not PUNCTUATION_END_RE(ch)
            else ch
            for ch in chunks
        ]

        text = "".join(chunks)

        if handle_whitespace == "STRIP":
            text = text.strip()
        elif handle_whitespace == "NORMALIZED":
            text = normalize_whitespace(text)
        elif handle_whitespace == "REPLACE":
            text = re.sub(
                r"[%s]" % ("".join(whitespaces)), " ", text, flags=re.UNICODE
            ).strip()

        return text

    def text_formatted(
        self,
        element: Union[DOMElement, None]=None,
        sep:str = "",
        handle_whitespace:str = "STRIP",
        whitespaces: Union[List[str], None] = None,
        ignore_tags:Union[List[str], None] = None,
        word_count: Union[int, None] = None,
        **kwargs,
    ):
        """Returns the text content of the element."""

        if whitespaces is None:
            whitespaces = ["\n", "\r", "\t"]

        element = self.get_element(element)

        chunks = element_to_text(
            element
        )

        if word_count:
            chunks = [ch for ch in chunks if float(len(WORD_RE(ch))) <= word_count]

        text = "".join(chunks)

        if handle_whitespace == "STRIP":
            text = text.strip()
        elif handle_whitespace == "NORMALIZED":
            text = normalize_whitespace(text)
        elif handle_whitespace == "REPLACE":
            text = re.sub(
                r"[%s]" % ("".join(whitespaces)), " ", text, flags=re.UNICODE
            ).strip()

        return text

    def all_text(
        self,
        element: Union[DOMElement, None]=None,
        sep:str = "",
        handle_whitespace:str = "STRIP",
        whitespaces: Union[List[str], None] = None,
        ignore_tags:Union[List[str], None] = None,
        word_count: Union[int, None] = None,
        **kwargs,
    ):
        """Returns the text content of the element."""

        # NOTE:
        #  - element.itertext returns comment text
        #  - html.tostring() or etree.tostring() would not support the
        #    separator options
        #  - Suggested way `.//text()` which seems sufficient.
        if whitespaces is None:
            whitespaces = ["\n", "\r", "\t"]
        if ignore_tags is None:
            ignore_tags = ["head", "title", "noscript", "script", "style"]
        element = self.get_element(element)
        not_xpath = ""

        if ignore_tags:
            # [not(ancestor::head|ancestor::title|ancestor::noscript|ancestor::script|ancestor::style)]
            ignore_statement = ""
            for ignore_tag in ignore_tags:
                ignore_statement += "ancestor::%s|" % (ignore_tag)
            if ignore_statement:
                not_xpath = "[not(" + ignore_statement.strip("|") + ")]"
        if word_count is not None:
            not_xpath = not_xpath + "[ext:has-word-count(.,%s)]" % word_count

        # for br in element.xpath("*//br"):
        #     br.tail = "\n" + br.tail if br.tail else "\n"
        # ------ using element_to_text ------
        # text = sep.join(element.xpath(".//text()%s" % (not_xpath)))
        # print(type(element), element.tag, id(element))
        chunks = element_to_text(
            element
        )

        if word_count:
            chunks = [ch for ch in chunks if float(len(WORD_RE(ch))) <= word_count]

        text = "".join(chunks)
        if handle_whitespace == "STRIP":
            text = text.strip()
        elif handle_whitespace == "NORMALIZED":
            text = normalize_whitespace(text)
        elif handle_whitespace == "REPLACE":
            text = re.sub(
                r"[%s]" % ("".join(whitespaces)), " ", text, flags=re.UNICODE
            ).strip()

        return text

    def text(
            self,
            element: Union[DOMElement, None]=None,
            sep:str = "",
            handle_whitespace:str = "STRIP",
            whitespaces: Union[List[str], None] = None,
            ignore_tags:Union[List[str], None] = None,
            word_count: Union[int, None] = None,
            **kwargs,
        ):
        if whitespaces is None:
            whitespaces = ["\n", "\r", "\t"]
        if ignore_tags is None:
            ignore_tags = ["head", "title", "noscript", "script", "style"]
        element = self.tree if element is None else element
        # not_xpath = ""

        # if ignore_tags:
        #     # [not(ancestor::head|ancestor::title|ancestor::noscript|ancestor::script|ancestor::style)]
        #     ignore_statement = ""
        #     for ignore_tag in ignore_tags:
        #         ignore_statement += "ancestor::%s|" % (ignore_tag)
        #     if ignore_statement:
        #         not_xpath = "[not(" + ignore_statement.strip("|") + ")]"
        # if word_count is not None:
        #     not_xpath = not_xpath + "[ext:has-word-count(.,%s)]" % word_count

        # # for br in element.xpath("*//br"):
        # #     br.tail = "\n" + br.tail if br.tail else "\n"
        # # ------ using element_to_text ------
        # # text = sep.join(element.xpath(".//text()%s" % (not_xpath)))
        # chunks = element_to_text(
        #     element._element if isinstance(element, DOMElement) else element
        # )

        # if word_count:
        #     chunks = [ch for ch in chunks if float(len(WORD_RE(ch))) <= word_count]

        # text = "".join(chunks)
        text = (element.text or '')
        if handle_whitespace == "STRIP":
            text = text.strip()
        elif handle_whitespace == "NORMALIZED":
            text = normalize_whitespace(text)
        elif handle_whitespace == "REPLACE":
            text = re.sub(
                r"[%s]" % ("".join(whitespaces)), " ", text, flags=re.UNICODE
            ).strip()

        return text

    def nstag(self, element: Union[DOMElement, None]):
        element = self.tree if element is None else element
        return element.tag

    def tag(self, element: Union[DOMElement, None]):
        element = self.tree if element is None else element
        tag = element.tag.split('}')[-1] # strip ns
        return tag

    def split(self, xpath: str, element: Union[DOMElement, None]=None, root_callback=None, **kwargs):
        """Splits a html document into multiple html fragments."""
        consider_common_parent = True

        def _default_root_callback():
            return html_xhtml_df("<html><body></body></html>"), "//body"

        if not root_callback:
            root_callback = _default_root_callback
        elements = []
        root = None
        if isinstance(xpath, str):
            _elem = self.tree if element is None else element
            _elems = _elem.xpath(xpath)
            _xpaths = []
            if consider_common_parent:
                _xpaths = [el.get_xpath() for el in _elems]
                _xpath_str1 = _xpaths[0]
                _filtered_xpaths = []
                for _xpath in _xpaths[1:]:
                    _xpath_str2 = _xpath
                    seqMatcher = SequenceMatcher(None, _xpath_str1, _xpath_str2)
                    matching_blocks = seqMatcher.get_matching_blocks()
                    if len(matching_blocks) == 3:
                        m1 = matching_blocks[0]
                        m2 = matching_blocks[1]
                        _common_xpath_part1 = _xpath_str1[m1.a : m1.a + m1.size].strip(
                            "["
                        )
                        _common_xpath_part2 = _xpath_str1[m2.a : m2.a + m2.size].strip(
                            "]"
                        )

                        _uncommon_xpath1 = _xpath_str1.replace(
                            _common_xpath_part2, ""
                        ).replace(_common_xpath_part1, "")
                        _uncommon_xpath2 = _xpath_str2.replace(
                            _common_xpath_part2, ""
                        ).replace(_common_xpath_part1, "")
                        _xp1 = _common_xpath_part1 + _uncommon_xpath1
                        _xp2 = _common_xpath_part1 + _uncommon_xpath2
                        if _xp1 not in _filtered_xpaths:
                            _filtered_xpaths.append(_xp1)
                        if _xp2 not in _filtered_xpaths:
                            _filtered_xpaths.append(_xp2)
                    _xpath_str1 = _xpath_str2

                _elems = _elem.xpath("|".join(_filtered_xpaths))
            for el in _elems:
                if root is None:
                    root = el.getparent()
                elif root != el.getparent():
                    raise XpathMultipleParents(xpath, el)
                elements.append(el)
        current_doc = None
        if root is None:
            return
        for el in root:
            if el in elements:
                if current_doc is not None:
                    yield self._wrap(current_doc)
                current_doc, root_xpath = root_callback()
                body = current_doc.xpath(root_xpath)[0]
            if current_doc is not None:
                body.append(
                    copy.deepcopy(el if isinstance(el, etree._Element) else el.element)
                )
        if current_doc is not None:
            yield self._wrap(current_doc)

    def tostring(self, element:Union[DOMElement, None]=None):
        if element is None:
            return tostring(self.tree, encoding="unicode", method=self._method)
        else:
            return tostring(element, encoding="unicode", method=self._method)

    def reset_clean_dom(self):
        self._clean_tree_root = None
        self.clean_dom()

    def clean_dom(self, remove_tags:Union[List[str], None]=["em", "strong", "b", "i", "span", "a", "code", "kbd"],
                        kill_tags:Union[List[str], None]=["script", "style"]):
        if self._clean_tree_root is None:
            if self._document_type not in ["html5", "xhtml5"]:
                Clean = Cleaner(
                    style=True,
                    inline_style=True,
                    forms=False,
                    page_structure=False,
                    remove_tags=remove_tags,
                    allow_tags=None,
                    kill_tags=kill_tags,
                    remove_unknown_tags=None,
                    safe_attrs_only=False,
                )

                self._clean_tree_root = copy.deepcopy(
                    self._tree_root.getroottree().getroot()
                )
                self._tree_root_cached = list(self._clean_tree_root.iter())
                xhtml_to_html(self._clean_tree_root)
                Clean(self._clean_tree_root)
            else:
                self._clean_tree_root = copy.deepcopy(
                    self._tree_root.getroottree().getroot()
                )
                self._tree_root_cached = list(self._clean_tree_root.iter())
                Clean = Cleaner5(
                    style=True,
                    inline_style=True,
                    forms=False,
                    page_structure=False,
                    remove_tags=remove_tags,
                    allow_tags=None,
                    kill_tags=kill_tags,
                    remove_unknown_tags=None,
                    safe_attrs_only=False,
                )
                Clean(self._clean_tree_root)
            self._xpath_of_cleaned_elements = set()

    def clean_html_text(self, remove_tags:Union[List[str], None]=None):
        self.clean_dom(remove_tags)
        return self.text(self._clean_tree_root)

    def remove_extra_content(self, strict:bool=False):
        _elems = self.xpath(self.ALL_XPATHS_TO_REMOVE)
        _elems.reverse()
        for _el in _elems:
            _xp = _el.get_xpath()
            if _el.tag == "form":
                attr_style = _el.attrib.get("style")
                if not attr_style:
                    continue
                elif attr_style and "display:none;" not in attr_style:
                    continue

            if not _el.xpath(self.contains_article) and not _el.xpath(
                self.contains_person
            ):

                attr = _el.attrib.get("class")
                if attr and attr == "clear":
                    if _el.xpath(".//h1|.//h2|.//h3|.//h4|.//h5|.//h6"):
                        continue
                attr_id = _el.attrib.get("id")
                if attr_id and "results" in attr_id or attr and "results" in attr:
                    continue
                self._xpath_of_cleaned_elements.add(_xp)
                _el.remove()
            else:
                pass

    def get_xpath_by_text(
        self,
        text:str,
        case_insensitive:bool=True,
        ignore_tags:Union[List[str],None]=None,
        use_original_dom:bool=False,
        word_count:Union[int,None]=None,

    ):
        _reset_dom = self.clean_dom_as_default
        if use_original_dom:
            self.unset_clean_dom_as_default()
        if ignore_tags is None:
            ignore_tags = ["head", "title", "noscript", "script", "style"]
        assert text is not None, "Please enter search text"
        not_xpath = ""
        if ignore_tags:
            ignore_statement = ""
            for ignore_tag in ignore_tags:
                ignore_statement += "ancestor::%s|" % (ignore_tag)
            if ignore_statement:
                not_xpath = "[not(" + ignore_statement.strip("|") + ")]"
        if word_count is not None:
            not_xpath = not_xpath + "[ext:has-word-count(.,%s)]" % word_count

        _xpath_ci = (
            "translate(string(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            if case_insensitive
            else "string()"
        )
        text_ci = text.lower() if case_insensitive else text
        _xpath = "//*[normalize-space(%s)=normalize-space('%s')]%s" % (
            _xpath_ci,
            text_ci,
            not_xpath,
        )
        _elems = self.xpath(_xpath)
        _xps = []

        for _el in _elems:
            _xps.append(_el.get_xpath())
        self.clean_dom_as_default = _reset_dom
        return _xps

    def get_xpath_by_multiple_partial_text(
        self,
        text:List[str]=[],
        operator:str="and",
        case_insensitive:bool=True,
        ignore_tags:Union[List[str],None]=None,
        use_original_dom:bool=False,
        word_count:Union[int,None]=None,
    ):
        _reset_dom = self.clean_dom_as_default
        if use_original_dom:
            self.unset_clean_dom_as_default()

        if ignore_tags is None:
            ignore_tags = [
                "head",
                "title",
                "noscript",
                "script",
                "style",
                "select",
                "option",
                "checkbox",
                "radio",
            ]
        assert (
            text is not None and isinstance(text, (list)) and len(text) > 0
        ), "Please enter search text"
        regex_xpath = ""
        not_xpath = ""
        if ignore_tags:
            ignore_statement = ""
            for ignore_tag in ignore_tags:
                ignore_statement += "ancestor-or-self::%s|" % (ignore_tag)
            if ignore_statement:
                not_xpath = "[not(" + ignore_statement.strip("|") + ")]"

        full_str = ""
        _xpath_list = []
        for txt in text:
            _xtr = normalize_whitespace(txt).split()
            if len(_xtr) > 1:
                _xtr = "\s*".join([re.escape(_x) for _x in _xtr])
                if APOS_RE.search(_xtr):
                    _xtr = _xtr.replace("'", "', \"'\", '")
                    _xtr = "concat('" + _xtr.strip() + "')"
                    regex_xpath = (
                        " or re:test(normalize-space(string()),%s, 'i')" % _xtr
                    )
                else:
                    regex_xpath = (
                        " or re:test(normalize-space(string()),'%s', 'i')" % _xtr
                    )
            if word_count is not None:
                not_xpath = (
                    not_xpath
                    + "[ext:has-word-count(normalize-space(string()),%s)]" % word_count
                )

            _xpath_ci = (
                "translate(string(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
                if case_insensitive
                else "string()"
            )
            txt_ci = txt.lower() if case_insensitive else txt

            if APOS_RE.search(txt_ci):
                txt_ci = txt_ci.replace("'", "', \"'\", '")
                txt_ci = "concat('" + txt_ci.strip() + "')"
                _xpath = "(contains(normalize-space(%s),normalize-space(%s))%s)" % (
                    _xpath_ci,
                    txt_ci,
                    regex_xpath,
                )
                _xpath_list.append(_xpath)
            else:
                _xpath = "(contains(normalize-space(%s),normalize-space('%s'))%s)" % (
                    _xpath_ci,
                    txt_ci,
                    regex_xpath,
                )
                _xpath_list.append(_xpath)

        _full_xpath = "//*[%s]%s" % (f" {operator} ".join(_xpath_list), not_xpath)
        _elems = self.xpath(_full_xpath)
        _fxps = self.get_longest_xpath(_elems)
        self.clean_dom_as_default = _reset_dom
        return _fxps

    def get_longest_xpath(self, elems: List[DOMElement]):
        _xps = []
        _fxps = []
        for _el in elems:
            _xps.append(_el.get_xpath())
        for _xp in _xps:
            if not is_text_substring_in_list(txt=_xp, txt_list=_xps):
                _fxps.append(_xp)
        return _fxps

    def get_xpath_by_multiple_partial_text_optional(
        self,
        text:List[str]=[],
        operator:str="and",
        case_insensitive:bool=True,
        ignore_tags:Union[List[str],None]=None,
        use_original_dom:bool=False,
        word_count:Union[int,None]=None,
    ):
        _reset_dom = self.clean_dom_as_default
        if use_original_dom:
            self.unset_clean_dom_as_default()

        if ignore_tags is None:
            ignore_tags = [
                "head",
                "title",
                "noscript",
                "script",
                "style",
                "select",
                "option",
                "checkbox",
                "radio",
            ]

        assert (
            text is not None and isinstance(text, list) and len(text) > 0
        ), "Please enter search text"

        regex_xpath = ""
        not_xpath = ""
        inner_operator = "or"
        if ignore_tags:
            ignore_statement = ""
            for ignore_tag in ignore_tags:
                ignore_statement += "ancestor-or-self::%s|" % (ignore_tag)
            if ignore_statement:
                not_xpath = "[not(" + ignore_statement.strip("|") + ")]"

        if word_count is not None:
            not_xpath = (
                not_xpath
                + "[ext:has-word-count(normalize-space(string()),%s)]" % word_count
            )

        _xpath_ci = (
            "translate(string(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            if case_insensitive
            else "string()"
        )
        full_str = ""
        _xpath_list = []
        for txt in text:

            if isinstance(txt, str):
                _xtr = normalize_whitespace(txt).split()
                if len(_xtr) > 1:
                    _xtr = "\s*".join([re.escape(_x) for _x in _xtr])
                    if APOS_RE.search(_xtr):
                        _xtr = _xtr.replace("'", "', \"'\", '")
                        _xtr = "concat('" + _xtr.strip() + "')"
                        regex_xpath = (
                            " or re:test(normalize-space(string()),%s, 'i')" % _xtr
                        )
                    else:
                        regex_xpath = (
                            " or re:test(normalize-space(string()),'%s', 'i')" % _xtr
                        )

                txt_ci = txt.lower() if case_insensitive else txt

                if APOS_RE.search(txt_ci):
                    txt_ci = txt_ci.replace("'", "', \"'\", '")
                    txt_ci = "concat('" + txt_ci.strip() + "')"
                    _xpath = "(contains(normalize-space(%s),normalize-space(%s))%s)" % (
                        _xpath_ci,
                        txt_ci,
                        regex_xpath,
                    )
                    _xpath_list.append(_xpath)
                else:
                    _xpath = (
                        "(contains(normalize-space(%s),normalize-space('%s'))%s)"
                        % (_xpath_ci, txt_ci, regex_xpath)
                    )
                    _xpath_list.append(_xpath)
            elif isinstance(txt, (list, set)):
                _xpath_list_inner = []
                for tt in txt:
                    _xtr = normalize_whitespace(tt).split()
                    if len(_xtr) > 1:
                        _xtr = "\s*".join([re.escape(_x) for _x in _xtr])
                        if APOS_RE.search(_xtr):
                            _xtr = _xtr.replace("'", "', \"'\", '")
                            _xtr = "concat('" + _xtr.strip() + "')"
                            regex_xpath = (
                                " or re:test(normalize-space(string()),%s, 'i')" % _xtr
                            )
                        else:
                            regex_xpath = (
                                " or re:test(normalize-space(string()),'%s', 'i')"
                                % _xtr
                            )

                    txt_ci = tt.lower() if case_insensitive else tt

                    if APOS_RE.search(txt_ci):
                        txt_ci = txt_ci.replace("'", "', \"'\", '")
                        txt_ci = "concat('" + txt_ci.strip() + "')"
                        _xpath = (
                            "(contains(normalize-space(%s),normalize-space(%s))%s)"
                            % (_xpath_ci, txt_ci, regex_xpath)
                        )
                        _xpath_list_inner.append(_xpath)
                    else:
                        _xpath = (
                            "(contains(normalize-space(%s),normalize-space('%s'))%s)"
                            % (_xpath_ci, txt_ci, regex_xpath)
                        )
                        _xpath_list_inner.append(_xpath)
                if len(_xpath_list_inner) > 0:
                    _full_inner_xpath = "(%s)" % (
                        f" {inner_operator} ".join(_xpath_list_inner)
                    )
                    _xpath_list.append(_full_inner_xpath.strip())
        _full_xpath = "//*[%s]%s" % (f" {operator} ".join(_xpath_list), not_xpath)

        _elems = self.xpath(_full_xpath)
        _fxps = self.get_longest_xpath(_elems)
        self.clean_dom_as_default = _reset_dom
        return _fxps

    def get_xpath_by_partial_text(
        self,
        text:str=None,
        case_insensitive:bool=True,
        ignore_tags:Union[List[str],None]=None,
        use_original_dom:bool=False,
        word_count:Union[int,None]=None,
    ):
        _reset_dom = self.clean_dom_as_default
        if use_original_dom:
            self.unset_clean_dom_as_default()

        if ignore_tags is None:
            ignore_tags = ["head", "title", "noscript", "script", "style"]
        assert text is not None, "Please enter search text"
        regex_xpath = ""
        not_xpath = ""
        if ignore_tags:
            # [not(ancestor::head|ancestor::title|ancestor::noscript|ancestor::script|ancestor::style)]
            ignore_statement = ""
            for ignore_tag in ignore_tags:
                ignore_statement += "ancestor-or-self::%s|" % (ignore_tag)
            if ignore_statement:
                not_xpath = "[not(" + ignore_statement.strip("|") + ")]"
        _xtr = normalize_whitespace(text).split()
        if len(_xtr) > 1:
            _xtr = "\s*".join([re.escape(_x) for _x in _xtr])
            if APOS_RE.search(_xtr):
                _xtr = _xtr.replace("'", "', \"'\", '")
                _xtr = "concat('" + _xtr.strip() + "')"
                regex_xpath = " or re:test(normalize-space(string()),%s, 'i')" % _xtr
            else:
                regex_xpath = " or re:test(normalize-space(string()),'%s', 'i')" % _xtr
        if word_count is not None:
            not_xpath = (
                not_xpath
                + "[ext:has-word-count(normalize-space(string()),%s)]" % word_count
            )

        _xpath_ci = (
            "translate(string(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            if case_insensitive
            else "string()"
        )
        text_ci = text.lower() if case_insensitive else text

        if APOS_RE.search(text_ci):
            text_ci = text_ci.replace("'", "', \"'\", '")
            text_ci = "concat('" + text_ci.strip() + "')"
            _xpath = "//*[contains(normalize-space(%s),normalize-space(%s))%s]%s" % (
                _xpath_ci,
                text_ci,
                regex_xpath,
                not_xpath,
            )
        else:
            _xpath = "//*[contains(normalize-space(%s),normalize-space('%s'))%s]%s" % (
                _xpath_ci,
                text_ci,
                regex_xpath,
                not_xpath,
            )
        _elems = self.xpath(_xpath)
        _fxps = self.get_longest_xpath(_elems)
        self.clean_dom_as_default = _reset_dom
        return _fxps

    def urljoin(self, url: str) -> str:
        """Convert url to absolute, taking in account
        url and baseurl of the response"""
        return urljoin(self.base_url, url)

    def __repr__(self):
        return "<%s %s at %x>" % (
            self.__class__.__name__,
            self._tree_root.tag,
            id(self._tree_root),
        )

    def get_index(self, parent: DOMElement, element: DOMElement) -> int:
        return parent.index(element)

    def get_classes(self, element: DOMElement) -> Classes:
        return element.classes

    def get_classes_as_str(self, element: DOMElement) -> Classes:
        _att = element.attrib
        return _att['class'] if 'class' in _att else ""

    def get_all_element_in_xpath(self, xpath_str: str) -> List:
        node: List = self.xpath(xpath_str)
        all_info = []
        if node is not None and len(node)>0:
            node: DOMElement = node[0]
            all_info.append({'tag':node.tag, 'index': node.my_index_by_tag(), 'node': node})
            for n in node.iterancestors():
                n: DOMElement
                all_info.append({'tag':n.tag, 'index': n.my_index_by_tag(), 'node': n})
        return all_info

    def ParseXpath(self, tree: DOM = None, xpath_string: str = None) -> List[Dict]:
        try:
            if xpath_string is None:
                logger.error(f"XpathOperations :: ParseXpath :: xpath, None is passed as parameter")
                return []
            if tree is None:
                logger.error(f"XpathOperations :: ParseXpath :: tree, None is passed as parameter")
                return []
            logger.debug(
                f"XpathOperations :: ParseXpath :: tree :: {tree}, xpath_string :: {xpath_string}")
            xpath_chunk = xpath_string.split("/")[1:]
            xpath_list = []
            xpath_till_now = ""
            for i in xpath_chunk:
                xpath_till_now += f"/{i}"
                xpath_list.append(xpath_till_now)
            xpath_list = xpath_list[2:]
            parsed_xpath_chunk_list = []
            for xpath_value in xpath_list:
                node = tree.xpath(xpath_value)[0]
                parsed_xpath_chunk_list.append({"xpath_tag": xpath_value.split("/")[-1], "node": node})
            logger.debug(
                f"XpathOperations :: ParseXpath :: parsed_xpath_chunk_list length :: {len(parsed_xpath_chunk_list)}")
            return parsed_xpath_chunk_list
        except Exception as e:
            logger.error(f"XpathOperations :: ParseXpath :: error occurred :: {e}")
            return []
