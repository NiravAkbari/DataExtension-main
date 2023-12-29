# Disable writing *.pyc files - they don't seem to speed anything
# up appreciably, and they sometimes cause issues when switching
# branches during development.
# __all__ = ["DOM", "DOMElement"]
import logging
logger = logging.getLogger()
logger.debug("Initialising domparser module")
import sys
sys.setrecursionlimit(5000)
sys.dont_write_bytecode = True
from domparser.dom import DOM
from domparser.parser import DOMElement
from domparser.clean5 import drop_tag, drop_tree, remove_element
from ._version import __version__
logger.debug("Initialisation completed")
