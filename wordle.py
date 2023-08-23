from dataclasses import dataclass
import json
from typing import Callable, List, Set
from itertools import product

FilterFn = Callable[[str], bool]


@dataclass
class IncludeCharFilter:
    char: str

    def __call__(self, candidate: str):
        return self.char in candidate


@dataclass
class HasCharInPosFilter:
    char: str
    pos: int

    def __call__(self, candidate: str):
        return candidate[self.pos] == self.char


@dataclass
class DoesNotHaveCharFilter:
    char: str

    def __call__(self, candidate: str):
        return self.char not in candidate


def narrow_guesses(possible_words: List[str], filters: List[FilterFn]):
    new_matches = [
        word for word in possible_words
        if not (False in [filter(word) for filter in filters])
    ]
    return new_matches


def get_word_filtersets(word: str) -> List[List[FilterFn]]:
    filters_per_char: List[List[FilterFn]] = []
    seen_chars: Set[str] = set()
    for i, char in enumerate(word):
        position_filters = [DoesNotHaveCharFilter(char=char),
                            HasCharInPosFilter(char=char, pos=i)]
        if char not in seen_chars:
            position_filters.append(IncludeCharFilter(char=char))
        seen_chars.add(char)
        filters_per_char.append(position_filters)
    return list(product(*filters_per_char))


def guess(word: str, remaining_words: List[str]):
    filters = get_word_filtersets(word)


def main():
    OPENING = "crane"
    lines: List[str] = json.load(open("guesses.json"))
    filter_sets = get_word_filtersets(OPENING)
    c = [narrow_guesses(lines, filters) for filters in filter_sets]
    print(c)


main()
