from html.parser import HTMLParser
from html.entities import name2codepoint
import re


class _HTMLToText(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self._buf = []
        self.hide_output = False

    def handle_starttag(self, tag, attrs):
        actions = {"p": "\n", "br": "\n", "script": "", "style": ""}
        if not self.hide_output:
            self._buf.append(actions.get(tag, ""))
        if tag in ("script", "style"):
            self.hide_output = True

    def handle_startendtag(self, tag, attrs):
        if tag == "br":
            self._buf.append("\n")

    def handle_endtag(self, tag):
        if tag == "p":
            self._buf.append("\n")
        elif tag in ("script", "style"):
            self.hide_output = False

    def handle_data(self, text):
        if text and not self.hide_output:
            self._buf.append(re.sub(r"\s+", " ", text))

    def handle_entityref(self, name):
        if name in name2codepoint and not self.hide_output:
            c = chr(name2codepoint[name])
            self._buf.append(c)

    def handle_charref(self, name):
        if not self.hide_output:
            n = int(name[1:], 16) if name.startswith("x") else int(name)
            self._buf.append(chr(n))

    def get_text(self):
        text = re.sub(r" +", " ", " ".join(self._buf))
        text = text.split("\n")
        text = [x.strip() for x in text]
        return "\n".join(text)


def html_to_text(html):
    parser = _HTMLToText()
    try:
        parser.feed(html)
        parser.close()
        data = parser.get_text().strip()
        data = re.sub(r",,", ",", data)
        data = re.sub(r"\s+,", ",", data)
        return data
    except Exception as e:
        raise RuntimeError(
            f"Error occurred: {e}"
        )
