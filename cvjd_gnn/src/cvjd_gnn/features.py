"""TF-IDF: word uni/bigrams, smoothed IDF, sublinear TF and L2 norm.

Fit on training context only. Standard library + PyTorch; no NumPy or SciPy.
"""

import json
import math
import re
from collections import Counter
from pathlib import Path

from ._torch import torch
from .data import DataError, write_json


class TextEncoder:
    def __init__(self, max_features: int = 1024):
        self.max_features = max_features
        self.vocabulary: dict[str, int] = {}
        self.idf: list[float] = []

    @staticmethod
    def terms(text: str) -> list[str]:
        words = re.findall(r"[\w#+.]+", text.casefold())
        return words + [f"{a} {b}" for a, b in zip(words, words[1:])]

    def fit(self, texts: list[str]) -> "TextEncoder":
        term_frequency, document_frequency = Counter(), Counter()
        for text in texts:
            terms = self.terms(text)
            term_frequency.update(terms)
            document_frequency.update(set(terms))
        selected = sorted(term_frequency, key=lambda term: (-term_frequency[term], term))[:self.max_features]
        if not selected:
            raise DataError("Khong tao duoc tu vung TF-IDF tu van ban rong")
        self.vocabulary = {term: i for i, term in enumerate(sorted(selected))}
        self.idf = [math.log((1 + len(texts)) / (1 + document_frequency[term])) + 1 for term in self.vocabulary]
        return self

    def transform(self, texts: list[str]) -> torch.Tensor:
        if not self.vocabulary:
            raise DataError("Bo ma hoa chua duoc fit/load")
        features = torch.zeros((len(texts), self.dimension), dtype=torch.float32)
        row_indices, col_indices, values = [], [], []
        for row, text in enumerate(texts):
            weights = {self.vocabulary[term]: (1 + math.log(count)) * self.idf[self.vocabulary[term]]
                       for term, count in Counter(self.terms(text)).items() if term in self.vocabulary}
            norm = math.sqrt(sum(value * value for value in weights.values())) or 1
            for col, weight in weights.items():
                row_indices.append(row)
                col_indices.append(col)
                values.append(weight / norm)
        if values:
            features[row_indices, col_indices] = torch.tensor(values, dtype=torch.float32)
        return features

    @property
    def dimension(self) -> int:
        return len(self.vocabulary)

    def save(self, path: Path) -> None:
        write_json(path, {"max_features": self.max_features, "vocabulary": self.vocabulary, "idf": self.idf})

    @classmethod
    def load(cls, path: Path) -> "TextEncoder":
        payload = json.loads(path.read_text(encoding="utf-8"))
        encoder = cls(payload["max_features"])
        encoder.vocabulary = payload["vocabulary"]
        encoder.idf = payload["idf"]
        return encoder
