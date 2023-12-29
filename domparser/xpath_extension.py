from __future__ import absolute_import
from lxml.etree import register_namespace, FunctionNamespace, tostring, _Element
import re

try:
    from thefuzz import fuzz

    fuzzy_match_enabled = True
except ImportError:
    print('"thefuzz" Module not found!!')
    fuzzy_match_enabled = False


WHITESPACE_RE = re.compile(r"\s+", flags=re.U)
WORD_RE = re.compile(r"\w+", flags=re.I | re.U)


def has_fuzzy_match(context, str_list, str_to_chk, threshold=90):
    _str = ""
    try:
        if isinstance(str_list, str):
            _str = str_list
        elif isinstance(str_list, list):
            _str = str_list[0]
        else:
            _str = str_list[0]
    except IndexError:
        return False

    _xstr = ""
    _type = ""
    # if isinstance(_str, _Element):
    #     # _str = tostring(context.context_node, method='text', encoding='unicode')
    #     _str = ' '.join([x.strip() for x in context.context_node.xpath('.//text()')]).strip()
    #     #word_len = float(len(WORD_RE.findall(_str)))
    #     _type = 'node'
    # else:
    #     word_len = float(len(WORD_RE.findall(_str)))
    #     _type = 'text_node'
    if isinstance(_str, _Element):
        _str = " ".join(
            [x.strip() for x in context.context_node.xpath(".//text()")]
        ).strip()

    ratio = fuzz.ratio(_str, str_to_chk)
    partial_ratio = fuzz.partial_ratio(_str, str_to_chk)
    print("In extension funct.", _str, str_to_chk)
    if float(50) <= float(ratio):
        print("In extension funct.", _str, str_to_chk)
    print("Ratio: ", ratio, "Partial Ratio: ", partial_ratio, "====", threshold)
    if float(threshold) <= float(ratio):
        return True
    else:
        return False


def has_word_count(context, str_list, word_len_to_chk):
    """
    Perform endswith for XPath after removing trailing whitespaces
    from source
    """

    try:
        if isinstance(str_list, str):
            _str = str_list
        elif isinstance(str_list, list):
            _str = str_list[0]
        else:
            _str = str_list[0]
    except IndexError:
        return False

    _xstr = ""
    _type = ""
    if isinstance(_str, _Element):
        # _str = tostring(context.context_node, method='text', encoding='unicode')
        _str = " ".join(
            [x.strip() for x in context.context_node.xpath(".//text()")]
        ).strip()
        word_len = float(len(WORD_RE.findall(_str)))
        _type = "node"
    else:
        word_len = float(len(WORD_RE.findall(_str)))
        _type = "text_node"
    if word_len <= float(word_len_to_chk):
        return True
    else:
        return False


def endswith(context, str_list, str_to_chk):
    """
    Perform endswith for XPath after removing trailing whitespaces
    from source
    """
    try:
        _str = str_list[0]
    except IndexError:
        return False
    if isinstance(_str, _Element):
        _str = tostring(context.context_node, method="text", encoding="unicode")
    return _str.strip().endswith(str_to_chk)


def endswith_i(context, str_list, str_to_chk):
    """
    Perform endswith for XPath after removing trailing whitespaces
    from source
    """
    try:
        _str = str_list[0]
    except IndexError:
        return False
    if isinstance(_str, _Element):
        _str = tostring(context.context_node, method="text", encoding="unicode")
    return _str.lower().strip().endswith(str_to_chk.lower())


def startswith_i(context, str_list, str_to_chk):
    """
    Perform starswith for XPath, ignore case after removing trailing whitespaces
    from source
    """
    try:
        _str = str_list[0]
    except IndexError:
        return False
    if isinstance(_str, _Element):
        _str = tostring(context.context_node, method="text", encoding="unicode")
    return _str.lower().strip().startswith(str_to_chk.lower())


def startswith(context, str_list, str_to_chk):
    """
    Perform starswith for XPath, ignore case after removing trailing whitespaces
    from source
    """
    try:
        _str = str_list[0]
    except IndexError:
        return False
    if isinstance(_str, _Element):
        _str = tostring(context.context_node, method="text", encoding="unicode")
    return _str.strip().startswith(str_to_chk)


def has_all_classes(context, classes_to_check):
    """
    Assert if an element contains all of the specified classes in XPath.

    Parameters
    ----------

    classes_to_check : str
        Space delimited set of classes to check

    Returns
    -------
    bool
    """
    cls_str = context.context_node.get("class")
    if not cls_str:
        return False
    classes = set(WHITESPACE_RE.split(cls_str))
    classes_to_check = set(WHITESPACE_RE.split(classes_to_check))
    return classes_to_check.issubset(classes)


def has_any_classes(context, classes_to_check):
    """
    Assert if an element contains any of the specified classes in XPath.

    Parameters
    ----------

    classes_to_check : str
        Space delimited set of classes to check

    Returns
    -------
    bool
    """
    cls_str = context.context_node.get("class")
    if not cls_str:
        return False
    classes = set(WHITESPACE_RE.split(cls_str))
    classes_to_check = set(WHITESPACE_RE.split(classes_to_check))
    return not classes_to_check.isdisjoint(classes)


def has_class(context, cls_to_chk):
    """
    Check for a class accurately in XPath. Synonymous to .class selector

    NOTE: This is not a replacement for cssselect method. It is just to
    provide that ability to XPath expressions. CSSSelctor class has a better
    performance when compared to this extension function because or it's
    implementation.

    Function exists for backwards compatibility. Same as using
    `has_all_classes` with a
    single class specified.
    """
    return has_all_classes(context, cls_to_chk)


def cls_starts_with(context, cls_to_chk):
    """
    Check for a class starting with cls_to_chk
    """
    cls_str = context.context_node.get("class")
    if not cls_str:
        return False
    classes = WHITESPACE_RE.split(cls_str)
    return any([cl.startswith(cls_to_chk) for cl in classes])


def cls_ends_with(context, cls_to_chk):
    """
    Check for a class ending with cls_to_chk
    """
    cls_str = context.context_node.get("class")
    if not cls_str:
        return False
    classes = WHITESPACE_RE.split(cls_str)
    return any([cl.endswith(cls_to_chk) for cl in classes])


XSURI = '"http://www.w3.org/2001/XMLSchema"'
xs_ns = FunctionNamespace(XSURI)
xs_ns.prefix = "xsd"

REURI = "http://exslt.org/regular-expressions"
re_ns = FunctionNamespace(REURI)
re_ns.prefix = "re"

SVG_XHTML_NAMESPACE = "http://www.w3.org/2000/svg"
register_namespace("svg", SVG_XHTML_NAMESPACE)

NSURI = "ext://xpath-extensions"
ext_ns = FunctionNamespace(NSURI)
ext_ns.prefix = "ext"

ext_ns["has-class"] = has_class
ext_ns["has-all-classes"] = has_all_classes
ext_ns["has-any-classes"] = has_any_classes
ext_ns["ends-with"] = endswith
ext_ns["ends-with-i"] = endswith_i
ext_ns["starts-with-i"] = startswith_i
ext_ns["starts-with"] = startswith
ext_ns["class-starts-with"] = cls_starts_with
ext_ns["class-ends-with"] = cls_ends_with
ext_ns["has-word-count"] = has_word_count
ext_ns["has-fuzzy-match"] = has_fuzzy_match
# ext_ns['has-ner'] = has_word_count
