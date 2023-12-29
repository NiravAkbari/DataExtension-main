from lxml import etree
from lxml.cssselect import LxmlTranslator, LxmlHTMLTranslator
from pyquery.cssselectpatch import JQueryTranslator


class JQuerySelector(etree.XPath):
    """A JQuery selector.

    This class is used to implement the css pseudo classes
    (:first, :last, ...) that are not defined in the css standard,
    but are defined in the jquery API.

    Usage::

    Matches the first selected element::

            >>> from pyquery import PyQuery
            >>> d = PyQuery('<div><p class="first"></p><p></p></div>')
            >>> d('p:first')
            [<p.first>]

        ..
    Matches the last selected element::

            >>> from pyquery import PyQuery
            >>> d = PyQuery('<div><p></p><p class="last"></p></div>')
            >>> d('p:last')
            [<p.last>]

        ..


    """
    def __init__(self, jquery, namespaces=None):
        translator = JQueryTranslator()
        path = translator.css_to_xpath(jquery)
        etree.XPath.__init__(self, path, namespaces=namespaces)
        self.jquery = jquery

    def __repr__(self):
        return '<%s %s for %r>' % (
            self.__class__.__name__,
            hex(abs(id(self)))[2:],
            self.jquery)
