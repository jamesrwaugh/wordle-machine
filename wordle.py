from collections import defaultdict
from dataclasses import dataclass
import json
from typing import Callable, Dict, Iterable, List, Self, Set, Tuple
from itertools import product
from math import log2
import string
import time


FilterFn = Callable[[str], bool]


@dataclass
class IncludeCharFilter:
    char: str

    def __call__(self, candidate: str):
        return self.char in candidate

    def __hash__(self) -> int:
        return hash((self.char, "includes"))

    def __eq__(self, __value: Self) -> bool:
        return self.char == __value.char


@dataclass
class HasCharInPosFilter:
    char: str
    pos: int

    def __call__(self, candidate: str):
        return candidate[self.pos] == self.char

    def __hash__(self) -> int:
        return hash((self.char, self.pos, "haspos"))

    def __eq__(self, __value: Self) -> bool:
        return self.char == __value.char and self.pos == __value.pos


@dataclass
class DoesNotHaveCharFilter:
    char: str

    def __call__(self, candidate: str):
        return self.char not in candidate

    def __hash__(self) -> int:
        return hash((self.char, "doesnot"))

    def __eq__(self, __value: Self) -> bool:
        return self.char == __value.char


@dataclass
class StepResult:
    new_possibilities: Set[str]
    expected_information: float
    actual_information: float


def information(p: float):
    if p <= 0:
        return 0
    return -log2(p)


def expected_information(p: float):
    return p * information(p)


class Engine:
    def __init__(self, possible_words: List[str]):
        self.init_guesses(possible_words)
        self.current_filters: List[Tuple[FilterFn]] = []

    def init_guesses(self, guesses: Iterable[str]):
        self.possible_words = set(guesses)
        self.includeset_dict = self.build_includeset_dict()

    def build_word_filtersets(self, word: str) -> Iterable[Tuple[FilterFn]]:
        filters_per_char: List[List[FilterFn]] = []
        seen_chars: Set[str] = set()
        for i, char in enumerate(word):
            position_filters = [DoesNotHaveCharFilter(char=char),
                                HasCharInPosFilter(char=char, pos=i)]
            if char not in seen_chars:
                position_filters.append(IncludeCharFilter(char=char))
            seen_chars.add(char)
            filters_per_char.append(position_filters)
        inner_product: Iterable[Tuple[FilterFn, ...]] = product(*filters_per_char)  # noqa
        return inner_product

    def build_word_includeset(self, word: str) -> Set[FilterFn]:
        alphabet = set(string.ascii_lowercase)
        filters_per_char: Set[FilterFn] = set()
        word_alphabet = set(word)
        seen_chars: Set[str] = set()
        for i, char in enumerate(word):
            filters_per_char.add(HasCharInPosFilter(char, i))
            if not char in seen_chars:
                filters_per_char.add(IncludeCharFilter(char))
                seen_chars.add(char)
        for missing_char in (alphabet - word_alphabet):
            filters_per_char.add(DoesNotHaveCharFilter(missing_char))
        return filters_per_char

    def filter_current_guesses(self, filter_sets: Iterable[Tuple[FilterFn]]):
        word_sets: List[Set[str]] = []
        for filter_set in filter_sets:
            partial_filtered_words = [self.includeset_dict[filter]
                                      for filter in filter_set]
            word_set = self.possible_words.intersection(*partial_filtered_words)  # noqa
            word_sets.append(word_set)
        return word_sets

    def entropy(self, word: str):
        filter_sets = self.build_word_filtersets(word)
        word_sets = self.filter_current_guesses(filter_sets)
        entropy = sum(expected_information(len(word_set) / len(self.possible_words))
                      for word_set in word_sets)
        return entropy

    def build_includeset_dict(self):
        all_filters: Dict[FilterFn, Set[str]] = defaultdict(set)
        for word in self.possible_words:
            include_sets = self.build_word_includeset(word)
            for f in include_sets:
                all_filters[f].add(word)
        return all_filters

    def narrow_guesses(self, filters: Tuple[FilterFn]):
        new_wordset = self.filter_current_guesses([filters])[0]
        return new_wordset

    def step(self, word: str, new_filter_set: Tuple[FilterFn, ...]) -> StepResult:
        new_guesses = self.narrow_guesses(new_filter_set)
        p = len(new_guesses) / len(self.possible_words)
        actual_info = information(p)
        expected_info = self.entropy(word)
        self.init_guesses(new_guesses)
        self.current_filters.append(new_filter_set)
        return StepResult(
            new_possibilities=new_guesses,
            expected_information=expected_info,
            actual_information=actual_info)


def main():
    words: List[str] = json.load(open("guesses.json"))
    e = Engine(possible_words=words)
    start = time.time()
    result = e.step(
        "snake", (
            DoesNotHaveCharFilter("s"),
            DoesNotHaveCharFilter("n"),
            HasCharInPosFilter("a", pos=2),
            HasCharInPosFilter("k", pos=3),
            HasCharInPosFilter("e", pos=4)
        ))
    end = time.time()
    print((end - start))
    print(result.actual_information, result.expected_information,
          len(result.new_possibilities))


main()
