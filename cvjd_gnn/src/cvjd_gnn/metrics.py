from ._torch import torch
from torch import nn
from torch.nn import functional as F

from .data import LABELS


def classification_metrics(truth, predictions) -> dict:
    truth, predictions = list(truth), list(predictions)
    if len(truth) != len(predictions) or not truth:
        raise ValueError("Metrics need equally sized, nonempty truth/prediction lists")
    confusion = [[0] * 3 for _ in range(3)]
    for actual, predicted in zip(truth, predictions):
        if int(actual) not in range(3) or int(predicted) not in range(3):
            raise ValueError("Class indices must be 0, 1, 2")
        confusion[int(actual)][int(predicted)] += 1
    report = {}
    for i, name in enumerate(LABELS):
        tp = confusion[i][i]
        support, predicted_count = sum(confusion[i]), sum(row[i] for row in confusion)
        precision, recall = tp / predicted_count if predicted_count else 0.0, tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        report[name] = {"precision": precision, "recall": recall, "f1-score": f1, "support": support}
    macro = {key: sum(report[name][key] for name in LABELS) / 3 for key in ("precision", "recall", "f1-score")}
    weighted = {key: sum(report[name][key] * report[name]["support"] for name in LABELS) / len(truth)
                for key in ("precision", "recall", "f1-score")}
    accuracy = sum(confusion[i][i] for i in range(3)) / len(truth)
    report["macro avg"] = {**macro, "support": len(truth)}
    report["weighted avg"] = {**weighted, "support": len(truth)}
    return {"accuracy": accuracy, "macro_f1": macro["f1-score"], "per_class": report,
            "confusion_matrix": confusion, "class_order": list(LABELS)}


def baselines(dataset, encoder, seed: int) -> dict:
    """Train-only majority and linear softmax on TF-IDF cosine; plus skill rule."""
    cv_ids, jd_ids = sorted(dataset.cvs), sorted(dataset.jobs)
    cv_vec = dict(zip(cv_ids, encoder.transform([dataset.cvs[k].text for k in cv_ids])))
    jd_vec = dict(zip(jd_ids, encoder.transform([f"{dataset.jobs[k].title} {dataset.jobs[k].text}" for k in jd_ids])))

    def similarities(pairs):
        return torch.stack([torch.dot(cv_vec[p.cv_id], jd_vec[p.jd_id]) for p in pairs]).reshape(-1, 1)

    train = dataset.labelled_pairs("train")
    labels = torch.tensor([p.label for p in train], dtype=torch.long)
    counts = torch.bincount(labels, minlength=3).float()
    majority = int(counts.argmax().item())
    weights = len(labels) / (3 * counts)
    torch.manual_seed(seed)
    classifier = nn.Linear(1, 3)
    optimizer = torch.optim.LBFGS(classifier.parameters(), lr=1, max_iter=60, line_search_fn="strong_wolfe")
    features = similarities(train)

    def closure():
        optimizer.zero_grad()
        loss = F.cross_entropy(classifier(features), labels, weight=weights) + 0.01 * classifier.weight.square().sum()
        loss.backward()
        return loss

    optimizer.step(closure)
    result = {}
    for split in ("validation", "test"):
        pairs = dataset.labelled_pairs(split)
        truth = [p.label for p in pairs]
        rule = []
        for pair in pairs:
            required = set(dataset.jobs[pair.jd_id].skills)
            ratio = len(required.intersection(dataset.cvs[pair.cv_id].skills)) / len(required) if required else 0
            rule.append(0 if ratio < 0.4 else 1 if ratio < 0.6 else 2)
        with torch.no_grad():
            predicted = classifier(similarities(pairs)).argmax(-1).tolist()
        result[split] = {
            "majority": classification_metrics(truth, [majority] * len(pairs)),
            "skill_overlap_rule": classification_metrics(truth, rule),
            "tfidf_cosine_logistic_regression": classification_metrics(truth, predicted),
        }
    return result
