import math

import pytest

from cvjd_gnn._torch import torch
from cvjd_gnn.features import TextEncoder
from cvjd_gnn.metrics import classification_metrics
from cvjd_gnn.model import MeanSAGE


def test_mean_sage_averages_neighbors_and_retains_isolated_node_features():
    layer = MeanSAGE(2)
    with torch.no_grad():
        layer.neighbor.weight.copy_(torch.eye(2))
        layer.neighbor.bias.zero_()
        layer.root.weight.copy_(torch.eye(2))
    sources = torch.tensor([[2., 4.], [6., 8.], [10., 20.]], requires_grad=True)
    destinations = torch.tensor([[1., 1.], [2., 2.], [3., 3.]])
    edges = torch.tensor([[0, 1, 2], [0, 0, 1]])
    output = layer(sources, destinations, edges)
    # Destination 0 receives mean([2,4],[6,8]); destination 2 has no neighbors.
    torch.testing.assert_close(output, torch.tensor([[5., 7.], [12., 22.], [3., 3.]]))
    torch.testing.assert_close(output, layer(sources, destinations, edges[:, [2, 0, 1]]))
    output.sum().backward()
    torch.testing.assert_close(sources.grad, torch.tensor([[0.5, 0.5], [0.5, 0.5], [1., 1.]]))


def test_classification_metrics_against_hand_counted_confusion():
    result = classification_metrics([0, 0, 1, 2], [0, 1, 1, 0])
    assert result["confusion_matrix"] == [[1, 1, 0], [0, 1, 0], [1, 0, 0]]
    assert result["accuracy"] == 0.5
    assert result["macro_f1"] == pytest.approx(7 / 18)
    assert result["per_class"]["high"]["recall"] == 0


def test_tfidf_weighting_and_unseen_words():
    encoder = TextEncoder(32).fit(["alpha alpha beta", "beta gamma"])
    vectors = encoder.transform(["alpha alpha beta", "wordneverobserved"])
    alpha, beta = encoder.vocabulary["alpha"], encoder.vocabulary["beta"]
    assert float(vectors[0, alpha] / vectors[0, beta]) == pytest.approx((1 + math.log(2)) * (math.log(3 / 2) + 1))
    assert float(vectors[0].norm()) == pytest.approx(1)
    assert float(vectors[1].norm()) == 0
