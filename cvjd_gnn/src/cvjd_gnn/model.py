"""Heterogeneous mean GraphSAGE implemented directly with PyTorch.

For relation r: m_v = mean(h_u for (u,v) in r),
z_v,r = W_neighbor,r m_v + W_root,r h_v. Average the relation outputs per
destination type, then apply ReLU/dropout. All graph message weights are learned.
"""

from ._torch import torch
from torch import nn
from torch.nn import functional as F

from .graph import RELATIONS


class MeanSAGE(nn.Module):
    def __init__(self, channels: int):
        super().__init__()
        self.neighbor = nn.Linear(channels, channels)
        self.root = nn.Linear(channels, channels, bias=False)

    def forward(self, source: torch.Tensor, destination: torch.Tensor, edges: torch.Tensor):
        neighbors = destination.new_zeros(destination.shape)
        degree = destination.new_zeros((len(destination), 1))
        if edges.numel():
            neighbors.index_add_(0, edges[1], source[edges[0]])
            degree.index_add_(0, edges[1], destination.new_ones((edges.shape[1], 1)))
        neighbors = neighbors / degree.clamp_min(1)
        return self.neighbor(neighbors) + self.root(destination)


class CVJDModel(nn.Module):
    def __init__(self, input_channels: int, hidden_channels: int = 64, layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.dropout = dropout
        self.projections = nn.ModuleDict({name: nn.Linear(input_channels, hidden_channels)
                                          for name in ("cv", "jd", "skill")})
        self.convs = nn.ModuleList([nn.ModuleDict({"__".join(rel): MeanSAGE(hidden_channels)
                                                   for rel in RELATIONS}) for _ in range(layers)])
        self.classifier = nn.Sequential(nn.Linear(hidden_channels * 4, hidden_channels), nn.ReLU(),
                                        nn.Dropout(dropout), nn.Linear(hidden_channels, 3))

    def encode(self, graph):
        values = {key: F.relu(self.projections[key](x)) for key, x in graph.x_dict.items()}
        for conv in self.convs:
            incoming = {key: [] for key in values}
            for relation in RELATIONS:
                source, _, destination = relation
                incoming[destination].append(conv["__".join(relation)](
                    values[source], values[destination], graph.edge_index_dict[relation]))
            values = {key: F.dropout(F.relu(torch.stack(messages).mean(0)), p=self.dropout, training=self.training)
                      for key, messages in incoming.items()}
        return values

    def forward(self, graph, cv_index: torch.Tensor, jd_index: torch.Tensor) -> torch.Tensor:
        embeddings = self.encode(graph)
        cv, jd = embeddings["cv"][cv_index], embeddings["jd"][jd_index]
        return self.classifier(torch.cat([cv, jd, (cv - jd).abs(), cv * jd], dim=-1))
