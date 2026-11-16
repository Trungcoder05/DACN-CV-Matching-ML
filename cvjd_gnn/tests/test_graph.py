from cvjd_gnn._torch import torch

from cvjd_gnn.data import Document, load_dataset
from cvjd_gnn.demo import make_demo
from cvjd_gnn.features import TextEncoder
from cvjd_gnn.graph import CV_TO_SKILL, add_queries, build_context
from cvjd_gnn.model import CVJDModel


def test_held_out_cv_cannot_change_context_or_another_query(tmp_path):
    make_demo(tmp_path / "demo", cvs=18)
    dataset = load_dataset(tmp_path / "demo")
    encoder = TextEncoder(64)
    context = build_context(dataset, encoder)
    query_a = Document("new_a", "Python Django student project", ("python", "django"))
    query_b = Document("new_b", "React frontend project", ("react", "html"))
    a = add_queries(context, [query_a], encoder)
    ab = add_queries(context, [query_a, query_b], encoder)
    assert torch.equal(context.graph.edge_index_dict[CV_TO_SKILL], ab.graph.edge_index_dict[CV_TO_SKILL])
    model = CVJDModel(encoder.dimension, hidden_channels=8, layers=2, dropout=0)
    model.eval()
    with torch.no_grad():
        base_h = model.encode(context.graph)
        a_h, ab_h = model.encode(a.graph), model.encode(ab.graph)
    for kind in ("jd", "skill"):
        torch.testing.assert_close(base_h[kind], ab_h[kind])
    torch.testing.assert_close(a_h["cv"][-1], ab_h["cv"][-2])
    assert not set(context.cv_ids).intersection(dataset.cv_ids("test"))
    assert all("match" not in relation[1] for relation in context.graph.edge_index_dict)


def test_tfidf_serialization_keeps_features_and_ignores_unseen_vocabulary(tmp_path):
    encoder = TextEncoder(64).fit(["Python and C++", "SQL Django project"])
    original = encoder.transform(["Python Django totallyunseentoken"])
    encoder.save(tmp_path / "encoder.json")
    restored = TextEncoder.load(tmp_path / "encoder.json")
    torch.testing.assert_close(original, restored.transform(["Python Django totallyunseentoken"]))
    assert "totallyunseentoken" not in restored.vocabulary
