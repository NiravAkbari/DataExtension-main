import spacy
from spacy.language import Language
from spacy.tokens import Span


def create_custom_ner_pipe(nlp, web_trf_nlp, address_parser_nlp):
    @Language.component("partial_address_ner_pipe_component")
    def partial_address_ner_pipe_component(doc):
        text = doc.text

        doc1 = web_trf_nlp(text)
        doc2 = address_parser_nlp(text)

        gpe_entities = [ent for ent in doc1.ents if ent.label_ in ["GPE", "ORG"]]
        address_entities = [
            ent
            for ent in doc2.ents
            if ent.label_ in {"full_street", "city", "state", "postal_code"}
        ]

        for label in {"GPE", "ORG", "full_street", "city", "state", "postal_code"}:
            doc.vocab.strings.add(label)

        combined_entities = []
        for ent in gpe_entities + address_entities:
            overlapping = [
                e for e in combined_entities if e.start < ent.end and e.end > ent.start
            ]
            if not overlapping:
                combined_entities.append(ent)
            else:
                if ent in address_entities:
                    for overlapping_ent in overlapping:
                        combined_entities.remove(overlapping_ent)
                    combined_entities.append(ent)

        doc.ents = [
            Span(doc, ent.start, ent.end, label=doc.vocab.strings[ent.label_])
            for ent in combined_entities
        ]

        return doc

    return partial_address_ner_pipe_component


class PartialAddressExtractor:
    def __init__(self, web_trf_nlp, address_parser_nlp):
        self.nlp_en_core_web_trf = web_trf_nlp
        self.nlp_address_ner_model_v2 = address_parser_nlp
        self.nlp_partial_address = spacy.blank("en")
        self.nlp_partial_address.add_pipe("sentencizer")
        partial_address_ner_pipe_component = create_custom_ner_pipe(
            self.nlp_partial_address,
            self.nlp_en_core_web_trf,
            self.nlp_address_ner_model_v2,
        )
        self.nlp_partial_address.add_pipe("partial_address_ner_pipe_component")

    def extract_addresses(self, doc):
        patterns = []
        i = 0

        while i < len(doc.ents) - 2:
            pattern = {}
            start_index = i
            pattern["confidence"] = "LOW"
            if doc.ents[i].label_ == "ORG":
                if (
                    doc.ents[i + 1].label_ in {"GPE", "city"}
                    and doc.ents[i + 1].start_char - doc.ents[i].end_char <= 4
                ):
                    pattern["city"] = doc.ents[i + 1].text
                    pattern["confidence"] = "HIGH"
                    pattern["match_start"] = doc.ents[i + 1].start_char
                    i += 1
                else:
                    i += 1
                    continue
            elif doc.ents[i].label_ in {"GPE", "city"}:
                pattern["city"] = doc.ents[i].text
                pattern["match_start"] = doc.ents[i].start_char
            else:
                i += 1
                continue

            if (
                doc.ents[i + 1].label_ == "state"
                and doc.ents[i + 2].label_ == "postal_code"
                and doc.ents[i + 1].start_char - doc.ents[i].end_char <= 4
                and doc.ents[i + 2].start_char - doc.ents[i + 1].end_char <= 4
            ):
                pattern["state"] = doc.ents[i + 1].text
                pattern["postal_code"] = doc.ents[i + 2].text
                pattern["match_end"] = doc.ents[i + 2].end_char
                pattern["raw_address_str"] = doc.text[
                    pattern["match_start"] : pattern["match_end"]
                ]
                patterns.append(pattern)
                i += 3
            else:
                i += 1

        return patterns
