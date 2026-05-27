"""Minimal noun-class prefix hints for imported dictionary entries.

The table is intentionally incomplete. It supports transparent hints for
bootstrap imports only and must never be treated as a morphological analyzer.
Where a prefix is uncertain or requires local review, the candidate list is
left empty instead of guessing.
"""

from __future__ import annotations

import re


# Reference orientation:
# zul: Poulos & Msimang (1998), Doke (1927)
# xho: Du Plessis & Visser (1992)
# sot: Doke & Mofokeng (1957)
# tsn: Cole (1955)
# nso: Lombard (1985), Mojapelo (2007)
PREFIX_TABLE: dict[tuple[str, str], list[int]] = {
    ("zul", "umu"): [1, 3],  # Poulos & Msimang (1998): ambiguous class 1/3 surface prefix.
    ("zul", "um"): [1, 3],  # Poulos & Msimang (1998): reduced orthographic surface.
    ("zul", "u"): [1, 1],  # Doke (1927): class 1a/proper-name-like augment; kept ambiguous.
    ("zul", "aba"): [2],  # Poulos & Msimang (1998).
    ("zul", "o"): [2],  # Doke (1927): class 2a; needs context.
    ("zul", "imi"): [4],  # Poulos & Msimang (1998).
    ("zul", "i(li)"): [],  # TODO: needs reference-grammar verification for bootstrap string matching.
    ("zul", "ili"): [5],  # Poulos & Msimang (1998).
    ("zul", "ama"): [6],  # Poulos & Msimang (1998).
    ("zul", "isi"): [7],  # Poulos & Msimang (1998).
    ("zul", "izi"): [8, 10],  # Poulos & Msimang (1998): plural classes can overlap.
    ("zul", "in"): [9, 10],  # Poulos & Msimang (1998): nasal classes need stem context.
    ("zul", "im"): [9, 10],  # Poulos & Msimang (1998).
    ("zul", "i"): [5, 9],  # Poulos & Msimang (1998): common ambiguous augment.
    ("zul", "ubu"): [14],  # Poulos & Msimang (1998).
    ("zul", "uku"): [15],  # Poulos & Msimang (1998).
    ("xho", "um"): [1, 3],  # Du Plessis & Visser (1992).
    ("xho", "umu"): [1, 3],  # Du Plessis & Visser (1992).
    ("xho", "u"): [1],  # Du Plessis & Visser (1992): class 1a/proper names need review.
    ("xho", "aba"): [2],  # Du Plessis & Visser (1992).
    ("xho", "oo"): [2],  # Du Plessis & Visser (1992): class 2a-like proper-name plural.
    ("xho", "imi"): [4],  # Du Plessis & Visser (1992).
    ("xho", "ili"): [5],  # Du Plessis & Visser (1992).
    ("xho", "ama"): [6],  # Du Plessis & Visser (1992).
    ("xho", "isi"): [7],  # Du Plessis & Visser (1992).
    ("xho", "izi"): [8, 10],  # Du Plessis & Visser (1992).
    ("xho", "in"): [9, 10],  # Du Plessis & Visser (1992).
    ("xho", "im"): [9, 10],  # Du Plessis & Visser (1992).
    ("xho", "i"): [5, 9],  # Du Plessis & Visser (1992).
    ("xho", "ubu"): [14],  # Du Plessis & Visser (1992).
    ("xho", "uku"): [15],  # Du Plessis & Visser (1992).
    ("sot", "mo"): [1, 3],  # Doke & Mofokeng (1957): class 1/3 ambiguity.
    ("sot", "mma"): [1],  # Doke & Mofokeng (1957): kinship/proper forms; needs review.
    ("sot", "ba"): [2],  # Doke & Mofokeng (1957).
    ("sot", "bo"): [2],  # Doke & Mofokeng (1957): class 2a-like; needs context.
    ("sot", "me"): [4],  # Doke & Mofokeng (1957).
    ("sot", "le"): [5],  # Doke & Mofokeng (1957).
    ("sot", "ma"): [6],  # Doke & Mofokeng (1957).
    ("sot", "se"): [7],  # Doke & Mofokeng (1957).
    ("sot", "di"): [8, 10],  # Doke & Mofokeng (1957).
    ("sot", "n"): [9, 10],  # Doke & Mofokeng (1957): nasal class needs stem context.
    ("sot", "boh"): [14],  # TODO: needs reference-grammar verification.
    ("tsn", "mo"): [1, 3],  # Cole (1955).
    ("tsn", "mma"): [1],  # Cole (1955): kinship/proper forms; needs review.
    ("tsn", "ba"): [2],  # Cole (1955).
    ("tsn", "bo"): [2],  # Cole (1955): class 2a-like; needs context.
    ("tsn", "me"): [4],  # Cole (1955).
    ("tsn", "le"): [5],  # Cole (1955).
    ("tsn", "ma"): [6],  # Cole (1955).
    ("tsn", "se"): [7],  # Cole (1955).
    ("tsn", "di"): [8, 10],  # Cole (1955).
    ("tsn", "n"): [9, 10],  # Cole (1955).
    ("tsn", "boh"): [14],  # TODO: needs reference-grammar verification.
    ("nso", "mo"): [1, 3],  # Lombard (1985).
    ("nso", "ba"): [2],  # Lombard (1985).
    ("nso", "bo"): [2],  # Mojapelo (2007): needs context.
    ("nso", "me"): [4],  # Lombard (1985).
    ("nso", "le"): [5],  # Lombard (1985).
    ("nso", "ma"): [6],  # Lombard (1985).
    ("nso", "se"): [7],  # Lombard (1985).
    ("nso", "di"): [8, 10],  # Lombard (1985).
    ("nso", "n"): [9, 10],  # Lombard (1985).
    ("nso", "boh"): [14],  # TODO: needs reference-grammar verification.
}


def suggest_class(token: str, iso_lang: str) -> tuple[int | None, list[int]]:
    """Return a conservative noun-class hint for a token.

    A single candidate returns `(class_number, [])`. Multiple candidates return
    `(None, candidates)`. No confident prefix returns `(None, [])`.
    """

    cleaned = re.sub(r"^[\"'`.,;:!?()\\[\\]{}]+|[\"'`.,;:!?()\\[\\]{}]+$", "", token.casefold())
    cleaned = cleaned.replace("-", "")
    matches: list[tuple[int, list[int]]] = []
    for (lang, prefix), candidates in PREFIX_TABLE.items():
        if lang != iso_lang or not candidates:
            continue
        normalized_prefix = prefix.casefold().replace("-", "")
        if cleaned.startswith(normalized_prefix):
            matches.append((len(normalized_prefix), candidates))
    if not matches:
        return None, []
    matches.sort(key=lambda item: item[0], reverse=True)
    best = sorted(set(matches[0][1]))
    if len(best) == 1:
        return best[0], []
    return None, best
