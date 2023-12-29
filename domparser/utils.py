# -*- coding: utf-8 -*-
import sys
import re
import itertools
from typing import Any, List, Pattern, Union, cast, Match
from w3lib.html import replace_entities as w3lib_replace_entities

have_np = False
try:
    import numpy as np
    np.set_printoptions(threshold=sys.maxsize)
    have_np = True
except:
    have_np = False

SIMPLIFY_XPATH_RE = re.compile("\[\d+\]")


def find_continous_subsequence(iterable, predicate):
    """
    find the continuous subsequence with predicate function return true

    >>> find_continous_subsequence([2, 1, 2, 4], lambda x: x % 2 == 0)
    [[2], [2, 4]]

    >>> find_continous_subsequence([2, 1, 2, 4], lambda x: x % 2 != 0)
    [[1]]
    """
    seqs = []
    for key, values in itertools.groupby(iterable, key=predicate):
        if key == True:
            seqs.append(list(values))
    return seqs


def split_sequence(seq, predicate):
    """
    split the sequence at the position when predicate return true

    >>> list(split_sequence([0, 1, 2, 1, 2], lambda x: x == 1))
    [[0], [1, 2], [1, 2]]

    >>> list(split_sequence([0, 1, 2, 1, 2, 1], lambda x: x == 2))
    [[0, 1], [2, 1], [2, 1]]

    >>> list(split_sequence([('a', 1), ('b', 2), ('c', 1)], lambda x: x[1] == 1))
    [[('a', 1), ('b', 2)], [('c', 1)]]
    """
    seqs = []
    for s in seq:
        if predicate(s):
            if seqs:
                yield seqs
            seqs = [s]
        else:
            seqs.append(s)
    if seqs:
        yield seqs


def reverse_dict(d):
    return dict(reversed(item) for item in d.items())


def common_prefix(*sequences):
    """determine the common prefix of all sequences passed

    For example:
    >>> common_prefix('abcdef', 'abc', 'abac')
    ['a', 'b']
    """
    prefix = []
    for sample in zip(*sequences):
        first = sample[0]
        if all([x == first for x in sample[1:]]):
            prefix.append(first)
        else:
            break
    return prefix


def simplify_xpath(xpath):
    return SIMPLIFY_XPATH_RE.sub("", xpath)


def heal(xpath_dict):
    if not have_np:
        raise ValueError(
            "Numpy is not installed. Please install numpy to use this feature"
        )

    def handle_matrix(matrix, skeleton):
        mt = np.array(matrix)
        if len(mt.shape) == 1:
            return "No Valid Matrix [3]"
        mt = np.sort(mt, axis=0)
        shape = mt.shape
        row_size = shape[0]
        if row_size == 1:
            return "No Valid Matrix [4]"
        col_size = shape[1]
        if col_size == 1:
            return "No Valid Matrix [5]"
        recreate_arr = []
        for i in range(0, col_size):
            check_matrix = column(mt, i)
            make_set = set(check_matrix)
            if len(make_set) > 1:
                min_point = check_matrix[0]
                max_point = check_matrix[-1]
                distance = max_point - min_point + 1
                recreate_arr.append([min_point, max_point, distance])
            else:
                recreate_arr.append(list(make_set))
        distance = [i[2] for i in recreate_arr if len(i) > 1][0]
        filler = []
        for iii in recreate_arr:
            if len(iii) == 1:
                uu = [int(iii[0]) for i in range(0, distance)]
                filler.append(uu)
            else:
                min_point = iii[0]
                max_point = iii[1]
                yy = [int(i) for i in range(min_point, max_point + 1)]
                filler.append(yy)
        abc = np.array(filler)
        tt = np.transpose(abc)
        itr_arr = []
        try:
            for auto in tt:
                auto = tuple(auto)
                paths = skeleton % auto
                paths = paths.replace("[0]", "")
                itr_arr.append(paths)
            return itr_arr
        except Exception as e:
            return "No Valid Matrix [6]"

    def column(matrix, i):
        return [row[i] for row in matrix]

    if len(xpath_dict) == 0:
        return "Received Empty List [1]"
    for smpfy_xp, values in xpath_dict.items():
        unique_values = set(values)
        if len(unique_values) <= 1:
            xpath_dict[smpfy_xp] = list(unique_values)
            continue
        meta = dict()
        meta["smpfy_xp"] = smpfy_xp
        input_matrix = []
        skeleton = ""
        values = list(unique_values)
        for xpath in values:
            xpath = [i for i in xpath.split("/")]
            heal = [re.sub("\[\d+\]", "", i) for i in xpath]
            data = [re.findall("\[\d+\]", i) for i in xpath]
            dt = [str(i) if i else "0" for i in data]
            matrix = [int(re.sub("\[|\]|'", "", i)) for i in dt]
            skeleton = "[%s]/".join(heal) + "[%s]"
            input_matrix.append(matrix)
        try:
            pathx = handle_matrix(input_matrix, skeleton)
            # if 'No Valid Matrix' in pathx:
            #     meta = dict()
            #     meta['smpfy_xp'] = smpfy_xp
            #     meta['xpaths'] = []
            #     return meta
            #
            # else:
            if "No Valid Matrix" not in pathx:
                # meta = dict()
                # meta['smpfy_xp'] = smpfy_xp
                # meta['xpaths'] = pathx
                # return meta
                xpath_dict[smpfy_xp] = pathx
        except Exception as e:
            # meta = dict()
            # meta['smpfy_xp'] = smpfy_xp
            # meta['xpath'] = 'Exception'+str(e)
            # return meta
            pass
    return xpath_dict

def flatten(x):
    """flatten(sequence) -> list
    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).
    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]
    >>> flatten(["foo", "bar"])
    ['foo', 'bar']
    >>> flatten(["foo", ["baz", 42], "bar"])
    ['foo', 'baz', 42, 'bar']
    """
    return list(iflatten(x))


def iflatten(x):
    """iflatten(sequence) -> Iterator
    Similar to ``.flatten()``, but returns iterator instead"""
    for el in x:
        if _is_listlike(el):
            yield from flatten(el)
        else:
            yield el


def _is_listlike(x: Any) -> bool:
    """
    >>> _is_listlike("foo")
    False
    >>> _is_listlike(5)
    False
    >>> _is_listlike(b"foo")
    False
    >>> _is_listlike([b"foo"])
    True
    >>> _is_listlike((b"foo",))
    True
    >>> _is_listlike({})
    True
    >>> _is_listlike(set())
    True
    >>> _is_listlike((x for x in range(3)))
    True
    >>> _is_listlike(range(5))
    True
    """
    return hasattr(x, "__iter__") and not isinstance(x, (str, bytes))


def extract_regex(
    regex: Union[str, Pattern[str]], text: str, replace_entities: bool = True
) -> List[str]:
    """Extract a list of strings from the given text/encoding using the following policies:
    * if the regex contains a named group called "extract" that will be returned
    * if the regex contains multiple numbered groups, all those will be returned (flattened)
    * if the regex doesn't contain any group the entire regex matching is returned
    """
    if isinstance(regex, str):
        regex = re.compile(regex, re.UNICODE)

    if "extract" in regex.groupindex:
        # named group
        try:
            extracted = cast(Match[str], regex.search(text)).group("extract")
        except AttributeError:
            strings = []
        else:
            strings = [extracted] if extracted is not None else []
    else:
        # full regex or numbered groups
        strings = regex.findall(text)

    strings = flatten(strings)
    if not replace_entities:
        return strings
    return [w3lib_replace_entities(s, keep=["lt", "amp"]) for s in strings]


def shorten(text: str, width: int, suffix: str = "...") -> str:
    """Truncate the given text to fit in the given width."""
    if len(text) <= width:
        return text
    if width > len(suffix):
        return text[: width - len(suffix)] + suffix
    if width >= 0:
        return suffix[len(suffix) - width :]
    raise ValueError("width must be equal or greater than 0")
