"""PyTorch's optional NumPy bridge is deliberately unused by this project."""

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Failed to initialize NumPy: No module named 'numpy'.*", category=UserWarning)
    import torch

__all__ = ["torch"]
