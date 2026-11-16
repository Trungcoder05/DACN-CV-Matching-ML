"""Only train CVs send messages into the known-job graph.

New CVs receive skill messages but cannot alter the context. Predictions for one
query therefore do not depend on other validation/test CVs in the same batch.
No CV-JD suitability labels are used as graph edges or node features.
"""

from dataclasses import dataclass

from ._torch import torch

from .data import Dataset, Document, Pair
from .features import TextEncoder

CV_TO_SKILL = ("cv", "has", "skill")
SKILL_TO_CV = ("skill", "in_cv", "cv")
JD_TO_SKILL = ("jd", "requires", "skill")
SKILL_TO_JD = ("skill", "in_jd", "jd")
RELATIONS = (CV_TO_SKILL, SKILL_TO_CV, JD_TO_SKILL, SKILL_TO_JD)


def edge_tensor(pairs: list[tuple[int, int]]) -> torch.Tensor:
    return torch.tensor(pairs, dtype=torch.long).t().contiguous() if pairs else torch.empty((2, 0), dtype=torch.long)


@dataclass
class Graph:
    x_dict: dict[str, torch.Tensor]
    edge_index_dict: dict[tuple[str, str, str], torch.Tensor]

    def clone(self) -> "Graph":
        return Graph({k: v.clone() for k, v in self.x_dict.items()},
                     {k: v.clone() for k, v in self.edge_index_dict.items()})

    def to(self, device: str) -> "Graph":
        return Graph({k: v.to(device) for k, v in self.x_dict.items()},
                     {k: v.to(device) for k, v in self.edge_index_dict.items()})


@dataclass
class Context:
    graph: Graph
    cv_ids: list[str]
    job_ids: list[str]
    skill_names: list[str]


def build_context(dataset: Dataset, encoder: TextEncoder) -> Context:
    cvs = [dataset.cvs[key] for key in dataset.cv_ids("train")]
    jobs = [dataset.jobs[key] for key in sorted(dataset.jobs)]
    skill_names = sorted({s for document in [*cvs, *jobs] for s in document.skills})
    # A zero-degree placeholder keeps empty-skill datasets valid for text-only paths.
    skill_names = skill_names or ["__no_known_skill__"]
    encoder.fit([d.text for d in cvs] + [f"{d.title} {d.text}" for d in jobs] + skill_names)
    graph = Graph({"cv": encoder.transform([d.text for d in cvs]),
                   "jd": encoder.transform([f"{d.title} {d.text}" for d in jobs]),
                   "skill": encoder.transform(skill_names)}, {})
    skill_index = {skill: i for i, skill in enumerate(skill_names)}
    for documents, forward, reverse in ((cvs, CV_TO_SKILL, SKILL_TO_CV), (jobs, JD_TO_SKILL, SKILL_TO_JD)):
        edges = [(i, skill_index[s]) for i, document in enumerate(documents) for s in document.skills]
        graph.edge_index_dict[forward] = edge_tensor(edges)
        graph.edge_index_dict[reverse] = graph.edge_index_dict[forward].flip(0)
    return Context(graph, [d.id for d in cvs], [d.id for d in jobs], skill_names)


def add_queries(context: Context, queries: list[Document], encoder: TextEncoder) -> Context:
    graph = context.graph.clone().to("cpu")
    offset = graph.x_dict["cv"].shape[0]
    graph.x_dict["cv"] = torch.cat([graph.x_dict["cv"], encoder.transform([d.text for d in queries])])
    skill_index = {skill: i for i, skill in enumerate(context.skill_names)}
    edges = [(skill_index[s], offset + i) for i, document in enumerate(queries)
             for s in document.skills if s in skill_index]
    graph.edge_index_dict[SKILL_TO_CV] = torch.cat([graph.edge_index_dict[SKILL_TO_CV], edge_tensor(edges)], dim=1)
    # Deliberately no query -> skill edges: the base context stays unchanged.
    return Context(graph, context.cv_ids + [d.id for d in queries], context.job_ids, context.skill_names)


def pair_tensors(context: Context, pairs: list[Pair]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    cv_index = {key: i for i, key in enumerate(context.cv_ids)}
    jd_index = {key: i for i, key in enumerate(context.job_ids)}
    return (torch.tensor([cv_index[p.cv_id] for p in pairs], dtype=torch.long),
            torch.tensor([jd_index[p.jd_id] for p in pairs], dtype=torch.long),
            torch.tensor([p.label for p in pairs], dtype=torch.long))
