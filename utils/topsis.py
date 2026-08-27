"""
utils/topsis.py — alias for core.topsis_solver.run_topsis_optimization.
Exists so `from utils.topsis import run_topsis_optimization` works as expected by main.py.
"""

from core.topsis_solver import run_topsis_optimization  # re-export

__all__ = ["run_topsis_optimization"]
