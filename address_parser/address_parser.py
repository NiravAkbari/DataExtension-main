import os
import re
import spacy
import pyap
import scourgify

# from scourgify import normalize_address_record
from .address_normalizer import format_address as normalize_address_record
from .partial_address_parser import PartialAddressExtractor
from .utils import html_to_text


class USAddressParser:
    def __init__(self):
        model = "address_ner_model_v2"
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        self.address_parser_nlp = spacy.load(os.path.join(current_file_path, model))
        self.web_trf_nlp = spacy.load(
            "en_core_web_trf", disable=["tagger", "attribute_ruler", "lemmatizer"]
        )

        # Add EntityRuler to the pipeline
        self.entity_ruler = self.address_parser_nlp.add_pipe(
            "entity_ruler", before="ner"
        )

        # Define pattern for PO BOX
        po_box_pattern = [
            {"LOWER": {"IN": ["p.o.", "po", "p.o", "p. o.", "p. o"]}},
            {"IS_PUNCT": True, "OP": "?"},
            {"IS_SPACE": True, "OP": "*"},
            {"IS_ASCII": True, "OP": "*"},
            {"ORTH": {"REGEX": "(?i)box"}},
            {"IS_DIGIT": True},
        ]

        # Add the pattern to the EntityRuler
        self.entity_ruler.add_patterns(
            [{"label": "full_street", "pattern": po_box_pattern}]
        )

        self.pa_extractor = PartialAddressExtractor(
            self.web_trf_nlp, self.address_parser_nlp
        )

    @staticmethod
    def mask_telephone_numbers(text):
        """
        Replaces all telephone numbers in the given text with 'x' characters.

        Args:
        - text: str, the text in which to mask telephone numbers.

        Returns:
        - str, the text with masked telephone numbers.
        """
        pattern = r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})"
        return re.sub(pattern, USAddressParser.replace_matched_group, text)

    @staticmethod
    def count_numeric_chars(s):
        """
        Returns the number of numeric characters in the given string.

        Args:
        - s: str, the string to count numeric characters in.

        Returns:
        - int, the number of numeric characters in the string.
        """
        return sum(c.isnumeric() for c in s)

    @staticmethod
    def replace_matched_group(match, mask=True):
        """
        Replaces the matched group in the given match object with 'x' characters if the group contains
        10 or more numeric characters.

        Args:
        - match: re.Match, the match object whose group to replace.
        - mask: bool, whether to replace the group with 'x' characters.

        Returns:
        - str, the replaced group.
        """
        group = match.group()
        if USAddressParser.count_numeric_chars(group) >= 10:
            group = (
                "".join(["x" if c.isnumeric() else c for c in group]) if mask else group
            )
            return f"|{group}|"
        else:
            return group

    @staticmethod
    def normalize_text(text):
        """
        Normalizes the given text by removing unnecessary whitespace and replacing line breaks with commas.

        Args:
        - text: str, the text to normalize.

        Returns:
        - str, the normalized text.
        """
        text = re.sub(r"\n", ",", text)
        # text = re.sub(r"\.", "", text)

        text = re.sub(r"\s*\|\s*", ", ", text)
        text = re.sub(r",,", ",", text)
        text = re.sub(r" ,", ",", text)
        text = re.sub(r",\s+", ", ", text)
        text = re.sub(r"\s+,", ",", text)
        text = re.sub(r",(?!\s)", ", ", text)
        return text

    def nlp_extract_addresses(self, doc):
        """
        Extracts US addresses from the document using spaCy and PyAP.

        Returns:
        - list of dicts, each dict representing an extracted address with keys for address components.
        """

        addresses = []
        full_street_position = None

        for ent in doc.ents:
            if ent.label_ == "full_street":
                if full_street_position is not None:
                    postal_code_between = False
                    for e in doc.ents:
                        if (
                            e.label_ == "postal_code"
                            and e.start_char > full_street_position
                            and e.start_char < ent.start_char
                        ):
                            postal_code_between = True
                            break

                    if not postal_code_between:
                        full_street_position = ent.start_char
                        continue

                full_street_position = ent.start_char

            elif ent.label_ == "postal_code" and full_street_position is not None:
                end_position = ent.end_char
                address = dict()
                full_address = doc.text[full_street_position:end_position].strip()
                address["full_address"] = full_address

                for e in doc.ents:
                    if (
                        e.start_char >= full_street_position
                        and e.end_char <= end_position
                    ):
                        address[e.label_] = e.text
                address["match_start"] = full_street_position
                address["match_end"] = end_position
                address["raw_address_str"] = doc.text[full_street_position:end_position]
                addresses.append(address)

        return addresses

    def extract_addresses(self, text):
        pyap_addresses = []
        for address in pyap.parse(text, country="US"):
            print(text)
            address = address.as_dict()
            address["raw_address_str"] = address["full_address"]
            pyap_addresses.append(address)
        return pyap_addresses

    def render_displacy(self):
        """
        Renders the spaCy entity visualizer for the document.

        Returns:
        - str, the HTML for the entity visualizer.
        """
        return spacy.displacy.render(self.doc, style="ent")

    @staticmethod
    def remove_duplicate_addresses(addresses):
        """
        Removes duplicate addresses from the given list based on overlapping character positions.

        Args:
        - address_list: list of dicts, the list of addresses to remove duplicates from.

        Returns:
        - list of dicts, the list of unique addresses.
        """
        unique_addresses = []

        for address in addresses:
            overlap = False

            for unique_address in unique_addresses:
                if (
                    (
                        address["match_start"] >= unique_address["match_start"]
                        and address["match_start"] <= unique_address["match_end"]
                    )
                    or (
                        address["match_end"] >= unique_address["match_start"]
                        and address["match_end"] <= unique_address["match_end"]
                    )
                    or (
                        unique_address["match_start"] >= address["match_start"]
                        and unique_address["match_start"] <= address["match_end"]
                    )
                    or (
                        unique_address["match_end"] >= address["match_start"]
                        and unique_address["match_end"] <= address["match_end"]
                    )
                ):
                    overlap = True
                    break

            if not overlap:
                unique_addresses.append(address)

        return unique_addresses

    @staticmethod
    def normalize_addresses(addresses):
        """
        Normalizes the given list of addresses using scourgify.

        Args:
        - addresses: list of dicts, the list of addresses to normalize.

        Returns:
        - list of strs, the list of normalized addresses.
        """
        normalized_addresses = []
        for address in addresses:
            try:
                normalized_address = normalize_address_record(address["full_address"])
                normalized_address["raw_address_str"] = address["raw_address_str"]
                normalized_address["match_start"] = address["match_start"]
                normalized_address["match_end"] = address["match_end"]
                normalized_addresses.append(normalized_address)
            except Exception as e:
                normalized_addresses.append({})
        return normalized_addresses

    def replace_numbers_with_x(text):
        return "".join(["x" if char.isdigit() else char for char in text])

    def preprocess(self, text):
        doc = self.web_trf_nlp(text)
        modified_text = ""
        previous_end = 0

        for ent in doc.ents:
            if ent.label_ == "MONEY":
                modified_text += text[
                    previous_end : ent.start_char
                ] + USAddressParser.replace_numbers_with_x(ent.text)
                previous_end = ent.end_char

        modified_text += text[previous_end:]

        text = USAddressParser.mask_telephone_numbers(modified_text)
        return text

    def feed(self, html):
        """
        Extracts US addresses from the given HTML document using spaCy, PyAP, and scourgify.

        Args:
        - html: str, the HTML document to extract addresses from.
        """
        self.detected_addresses, self.normalized_addresses = [], []
        self.html = html
        self.html_to_text = html_to_text(html)
        self.masked_text = self.preprocess(self.html_to_text)
        self.normalized_text = USAddressParser.normalize_text(self.masked_text)

        self.doc = self.address_parser_nlp(self.masked_text)
        self.nlp_addresses = self.nlp_extract_addresses(self.doc)

        self.normalized_doc = self.address_parser_nlp(self.normalized_text)
        self.nlp_normalized_addresses = self.nlp_extract_addresses(self.normalized_doc)

        self.low_confidence_doc = self.pa_extractor.nlp_partial_address(
            self.html_to_text
        )

        self.pyap_addresses = self.extract_addresses(self.normalized_text)

        self.low_confidence_addresses = self.pa_extractor.extract_addresses(
            self.low_confidence_doc
        )

        self.detected_addresses = (
            self.pyap_addresses + self.nlp_addresses + self.nlp_normalized_addresses
        )

        self.normalized_addresses = USAddressParser.normalize_addresses(
            self.detected_addresses
        )

        combined_addresses = self.normalized_addresses + self.low_confidence_addresses

        self.normalized_addresses = USAddressParser.remove_duplicate_addresses(
            normalized_address
            for normalized_address in combined_addresses
            if normalized_address != {}
        )


if __name__ == "__main__":
    html = """<p>123 Main St, Anytown CA 12345</p>"""

    parser = USAddressParser()
    parser.feed(html)

    print(parser.pyap_addresses)
    print(parser.normalized_addresses)
