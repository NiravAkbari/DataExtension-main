class CSSSelectorException(Exception):
    """Base CSS Selector Exception class."""

    msg_format = "An error occurred with css selector: {} using translator: {}"
    def __init__(self, selector, translator, element):
        super(CSSSelectorException, self).__init__(self.msg_format.format(selector, translator))
        self.log_info = {}
        if hasattr(element, "base_url") and element.base_url:
            self.log_info["extra_info"] = {"xpath_url": element.base_url}
        elif hasattr(element, "base") and element.base:
            self.log_info["extra_info"] = {"xpath_url": element.base}


class XpathException(Exception):
    """Base XPath Exception class."""

    msg_format = "An error occurred with xpath: {}"

    def __init__(self, xpath, element):
        super(XpathException, self).__init__(self.msg_format.format(xpath))
        self.log_info = {}
        if hasattr(element, "base_url") and element.base_url:
            self.log_info["extra_info"] = {"xpath_url": element.base_url}
        elif hasattr(element, "base") and element.base:
            self.log_info["extra_info"] = {"xpath_url": element.base}


class XpathReturnedNone(XpathException):
    """
    Used when an xpath expression returned no results and we expected at
    least one.
    """

    msg_format = "No results were returned for the xpath provided: {}"


class XpathReturnedMultiple(XpathException):
    """
    Used when an xpath expression returned more than one result but the query
    expected only one result.
    """

    msg_format = "Multiple results were returned for the xpath provided: {}"


class XpathMultipleParents(XpathException):
    """
    Used when an xpath expression returned more than one result but the query
    expected only one result.
    """

    msg_format = (
        "Multiple parents for each child were returned for the " "xpath provided: {}"
    )
