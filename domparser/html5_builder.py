import warnings
import re
import sys


try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
from six import PY3, binary_type

from lxml import html, etree

from html5lib import _ihatexml
from html5lib.treebuilders import base, etree as etree_builders
from html5lib.treebuilders.etree_lxml import (
    Document,
    DocumentType,
    DataLossWarning,
    TreeBuilder as TB,
    testSerializer,
    tostring,
)

html.Comment = html.HtmlComment

fullTree = True
tag_regexp = re.compile("{([^}]*)}(.*)")

comment_type = etree.Comment("asd").tag


class TreeBuilder(base.TreeBuilder):
    documentClass = Document
    doctypeClass = DocumentType
    elementClass = None
    commentClass = None
    fragmentClass = Document
    implementation = html

    def __init__(self, namespaceHTMLElements, fullTree=False):
        infosetFilter = self.infosetFilter = _ihatexml.InfosetFilter(
            preventDoubleDashComments=True
        )
        self.namespaceHTMLElements = namespaceHTMLElements

        builder = html_builder = etree_builders.getETreeModule(html, fullTree=False)
        # etree_builder = etree_builders.getETreeModule(etree, fullTree=False)
        self.fromstring = html.fromstring

        class Attributes(MutableMapping):
            def __init__(self, element):
                self._element = element

            def _coerceKey(self, key):
                if isinstance(key, tuple):
                    name = "{%s}%s" % (key[2], infosetFilter.coerceAttribute(key[1]))
                else:
                    name = infosetFilter.coerceAttribute(key)
                return name

            def __getitem__(self, key):
                value = self._element._element.attrib[self._coerceKey(key)]
                if not PY3 and isinstance(value, binary_type):
                    value = value.decode("ascii")
                return value

            def __setitem__(self, key, value):
                self._element._element.attrib[self._coerceKey(key)] = value

            def __delitem__(self, key):
                del self._element._element.attrib[self._coerceKey(key)]

            def __iter__(self):
                return iter(self._element._element.attrib)

            def __len__(self):
                return len(self._element._element.attrib)

            def clear(self):
                return self._element._element.attrib.clear()

        class Element(builder.Element):
            def __init__(self, name, namespace):
                name = infosetFilter.coerceElement(name)
                builder.Element.__init__(self, name, namespace=namespace)
                self._attributes = Attributes(self)

            def _setName(self, name):
                self._name = infosetFilter.coerceElement(name)
                self._element.tag = self._getETreeTag(self._name, self._namespace)

            def _getName(self):
                return infosetFilter.fromXmlName(self._name)

            name = property(_getName, _setName)

            def _getAttributes(self):
                return self._attributes

            def _setAttributes(self, value):
                attributes = self.attributes
                attributes.clear()
                attributes.update(value)

            attributes = property(_getAttributes, _setAttributes)

            def insertText(self, data, insertBefore=None):
                data = infosetFilter.coerceCharacters(data)
                builder.Element.insertText(self, data, insertBefore)

            def cloneNode(self):
                element = type(self)(self.name, self.namespace)
                if self._element.attrib:
                    element._element.attrib.update(self._element.attrib)
                return element

        class Comment(builder.Comment):
            def __init__(self, data):
                data = infosetFilter.coerceComment(data)
                builder.Comment.__init__(self, data)

            def _setData(self, data):
                data = infosetFilter.coerceComment(data)
                self._element.text = data

            def _getData(self):
                return self._element.text

            data = property(_getData, _setData)

        self.elementClass = Element
        self.commentClass = Comment
        # self.elementClass = html_builder.Element
        # self.commentClass = etree.Comment

        # self.fragmentClass = builder.DocumentFragment
        base.TreeBuilder.__init__(self, namespaceHTMLElements)

    def reset(self):
        base.TreeBuilder.reset(self)
        self.insertComment = self.insertCommentInitial
        self.initial_comments = []
        self.doctype = None

    def testSerializer(self, element):
        return testSerializer(element)

    def tostring(self, element):
        return tostring(element)

    def getDocument(self):
        if fullTree:
            return self.document._elementTree
        else:
            return self.document._elementTree.getroot()

    def getFragment(self):
        fragment = []
        element = self.openElements[0]._element
        if element.text:
            fragment.append(element.text)
        fragment.extend(list(element))
        if element.tail:
            fragment.append(element.tail)
        return fragment

    def insertDoctype(self, token):
        name = token["name"]
        publicId = token["publicId"]
        systemId = token["systemId"]

        if not name:
            warnings.warn("lxml cannot represent empty doctype", DataLossWarning)
            self.doctype = None
        else:
            coercedName = self.infosetFilter.coerceElement(name)
            if coercedName != name:
                warnings.warn("lxml cannot represent non-xml doctype", DataLossWarning)

            doctype = self.doctypeClass(coercedName, publicId, systemId)
            self.doctype = doctype

    def insertCommentInitial(self, data, parent=None):
        assert parent is None or parent is self.document
        assert self.document._elementTree is None
        self.initial_comments.append(data)

    def insertCommentMain(self, data, parent=None):
        if (
            parent == self.document
            and self.document._elementTree.getroot()[-1].tag == comment_type
        ):
            warnings.warn(
                "lxml cannot represent adjacent comments beyond the root elements",
                DataLossWarning,
            )
        super(TreeBuilder, self).insertComment(data, parent)

    def insertRoot(self, token):
        # Because of the way libxml2 works, it doesn't seem to be possible to
        # alter information like the doctype after the tree has been parsed.
        # Therefore we need to use the built-in parser to create our initial
        # tree, after which we can add elements like normal
        docStr = ""
        if self.doctype:
            assert self.doctype.name
            docStr += "<!DOCTYPE %s" % self.doctype.name
            if self.doctype.publicId is not None or self.doctype.systemId is not None:
                docStr += ' PUBLIC "%s" ' % (
                    self.infosetFilter.coercePubid(self.doctype.publicId or "")
                )
                if self.doctype.systemId:
                    sysid = self.doctype.systemId
                    if sysid.find("'") >= 0 and sysid.find('"') >= 0:
                        warnings.warn(
                            "DOCTYPE system cannot contain single and double quotes",
                            DataLossWarning,
                        )
                        sysid = sysid.replace("'", "U00027")
                    if sysid.find("'") >= 0:
                        docStr += '"%s"' % sysid
                    else:
                        docStr += "'%s'" % sysid
                else:
                    docStr += "''"
            docStr += ">"
            if self.doctype.name != token["name"]:
                warnings.warn(
                    "lxml cannot represent doctype with a different name to the root element",
                    DataLossWarning,
                )
        # docStr += "<THIS_SHOULD_NEVER_APPEAR_PUBLICLY/>"
        # root = etree.fromstring(docStr)
        docStr += "<html></html>"
        root = self.fromstring(docStr)

        # Append the initial comments:
        for comment_token in self.initial_comments:
            comment = self.commentClass(comment_token["data"])
            root.addprevious(comment._element)

        # Create the root document and add the ElementTree to it
        self.document = self.documentClass()
        self.document._elementTree = root.getroottree()

        # Give the root element the right name
        name = token["name"]
        namespace = token.get("namespace", self.defaultNamespace)
        if namespace is None:
            etree_tag = name
        else:
            etree_tag = "{%s}%s" % (namespace, name)
        root.tag = etree_tag

        # Add the root element to the internal child/open data structures
        root_element = self.elementClass(name, namespace)
        root_element._element = root
        self.document._childNodes.append(root_element)
        self.openElements.append(root_element)

        # Reset to the default insert comment function
        self.insertComment = self.insertCommentMain
