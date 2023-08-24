from dataclasses import dataclass
import json
from typing import Callable, List, Set
from itertools import product
from math import log2

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


@dataclass
class StepResult:
    new_possibilities: List[str]
    expected_information: float
    actual_information: float


def information(p: float):
    if p <= 0:
        return 0
    return -log2(p)


def expected_information(p: float):
    return p * information(p)


@dataclass
class Engine:
    possible_words: List[str]

    def get_word_filtersets(self, word: str) -> List[List[FilterFn]]:
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

    def entropy(self, guesses: List[str], word: str):
        filter_sets = self.get_word_filtersets(word)
        word_sets = [self.narrow_guesses(guesses, filters)
                     for filters in filter_sets]
        entropy = sum(expected_information(len(word_set) / len(guesses))
                      for word_set in word_sets)
        return entropy

    def narrow_guesses(self, possible_words: List[str], filters: List[FilterFn]):
        new_matches: List[str] = []
        for word in possible_words:
            bad = False
            for f in filters:
                if not f(word):
                    bad = True
                    break
            if not bad:
                new_matches.append(word)
        return new_matches

    def step(self, word: str, filter_set: List[FilterFn]) -> StepResult:
        new_possibilities = self.narrow_guesses(self.possible_words, filter_set)  # noqa
        p = len(new_possibilities) / len(self.possible_words)
        i = information(p)
        e = self.entropy(self.possible_words, word)
        self.possible_words = new_possibilities
        return StepResult(
            new_possibilities=new_possibilities,
            expected_information=e,
            actual_information=i)


def main():
    words: List[str] = json.load(open("guesses.json"))
    e = Engine(possible_words=words)
    result = e.step("snake", [DoesNotHaveCharFilter("s")])
    print(result)


main()
