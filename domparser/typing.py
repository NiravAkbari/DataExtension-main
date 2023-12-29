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
)

# from typing import NewType, Union
from lxml import etree, html

# from typing import
import html5lib
from domparser.parser import SmartHTMLParser, SmartHTMLParser5, html5_xhtml5_df2


HtmlParser = NewType(
    "HtmlParser",
    Union[etree.XMLParser, etree.HTMLParser, html.HTMLParser, html5lib.HTMLParser],
)
