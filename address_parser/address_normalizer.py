import usaddress
import pyap

LINE1_USADDRESS_LABELS = (
    "AddressNumber",
    "StreetName",
    "AddressNumberPrefix",
    "AddressNumberSuffix",
    "StreetNamePreDirectional",
    "StreetNamePostDirectional",
    "StreetNamePreModifier",
    "StreetNamePostType",
    "StreetNamePreType",
    "IntersectionSeparator",
    "SecondStreetNamePreDirectional",
    "SecondStreetNamePostDirectional",
    "SecondStreetNamePreModifier",
    "SecondStreetNamePostType",
    "SecondStreetNamePreType",
    "LandmarkName",
    "CornerOf",
    "IntersectionSeparator",
    "BuildingName",
)
LINE2_USADDRESS_LABELS = (
    "OccupancyType",
    "OccupancyIdentifier",
    "SubaddressIdentifier",
    "SubaddressType",
)

PO_BOX_USADDRESS_LABELS = (
    "USPSBoxType",
    "USPSBoxID",
    "USPSBoxGroupType",
    "USPSBoxGroupID",
)


def format_address(address):
    parsed_address, _ = usaddress.tag(address)
    if parsed_address:
        line1_labels = [
            label for label in parsed_address.keys() if label in LINE1_USADDRESS_LABELS
        ]
        line1 = " ".join([parsed_address[label].strip() for label in line1_labels])
        line1 = line1.strip() if line1.strip() else None

        line2_labels = [
            label for label in parsed_address.keys() if label in LINE2_USADDRESS_LABELS
        ]
        line2 = " ".join([parsed_address[label].strip() for label in line2_labels])

        po_box_labels = [
            label for label in parsed_address.keys() if label in PO_BOX_USADDRESS_LABELS
        ]
        po_box = " ".join([parsed_address[label].strip() for label in po_box_labels])
        if not line1 and po_box:
            line1 = po_box
        else:
            line2 = " ".join([line2, po_box])

        line2 = line2.strip() if line2.strip() else None

        return dict(
            address_line_1=line1,
            address_line_2=line2,
            city=parsed_address.get("PlaceName"),
            state=parsed_address.get("StateName"),
            postal_code=parsed_address.get("ZipCode"),
            confidence="HIGH",
        )
    return {}



def format_address_2(address: str):
    addresses = pyap.parse(address, country="US")
    if addresses: 
        parsed_address = address.as_dict()
        street_address = parsed_address.get("full_street")
        formatted_street_address = format_address(street_address)
        return dict(
            address_line_1 = formatted_street_address.get("address_line_1"),
            address_line_2 = formatted_street_address.get("address_line_2"),
            city = parsed_address.get("city"),
            state = parsed_address.get("region1"),
            postal_code = parsed_address.get("postal_code"),
            confidence = "HIGH",
        )
    else:
        return {}