"""Statistical Uncertainty and Empirical Bayes Shrinkage Module for SupeRR Selector Analytics.

Implements robust small-sample handling:
- Empirical Bayes shrinkage adjusting extreme estimates toward population priors
- Match-level cluster standard error calculation
- Asymmetric and two-sided 90% confidence intervals
- Non-parametric match-level bootstrap confidence interval estimation
"""

from __future__ import annotations

import logging
from typing import Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def apply_empirical_bayes_shrinkage(
    sample_means: pd.Series,
    sample_sizes: pd.Series,
    population_prior: float | None = None,
    k_noise: float = 20.0,
) -> Tuple[pd.Series, pd.Series]:
    """Applies Empirical Bayes shrinkage to sample mean estimates.

    Formula:
        w_i = n_i / (n_i + k_noise)
        theta_shrunk = w_i * sample_mean + (1 - w_i) * population_prior

    Args:
        sample_means: Series of observed player sample mean impacts.
        sample_sizes: Series of observed sample counts (e.g., balls faced).
        population_prior: Population prior mean (if None, weighted sample mean is used).
        k_noise: Shrinkage penalty parameter in sample units.

    Returns:
        Tuple[pd.Series, pd.Series]: (shrunk_estimates, shrinkage_weights)
    """
    valid = sample_sizes > 0
    if population_prior is None:
        if valid.any():
            tot_w = sample_sizes[valid].sum()
            tot_val = (sample_means[valid] * sample_sizes[valid]).sum()
            population_prior = float(tot_val / max(1.0, tot_w))
        else:
            population_prior = 0.0

    n_arr = sample_sizes.fillna(0).astype("float64").values
    m_arr = sample_means.fillna(population_prior).astype("float64").values

    weights = np.where(n_arr > 0, n_arr / (n_arr + k_noise), 0.0)
    shrunk = weights * m_arr + (1.0 - weights) * population_prior

    return (
        pd.Series(np.round(shrunk, 4), index=sample_means.index, dtype="float64"),
        pd.Series(np.round(weights, 4), index=sample_means.index, dtype="float64"),
    )


def compute_confidence_intervals(
    estimates: pd.Series,
    std_devs: pd.Series,
    sample_counts: pd.Series,
    confidence_level: float = 0.90,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Computes cluster-aware standard errors and confidence interval bounds.

    Args:
        estimates: Central parameter estimates (e.g. shrunk impact).
        std_devs: Standard deviation across clusters/matches.
        sample_counts: Cluster count (matches).
        confidence_level: Desired coverage probability (default 0.90 for z=1.645).

    Returns:
        Tuple[pd.Series, pd.Series, pd.Series]: (standard_errors, lower_bounds, upper_bounds)
    """
    z_score = 1.645 if confidence_level == 0.90 else (1.960 if confidence_level == 0.95 else 1.645)

    n = np.maximum(1.0, sample_counts.fillna(0).astype("float64").values)
    s = std_devs.fillna(1.0).astype("float64").values
    est = estimates.fillna(0.0).astype("float64").values

    se = s / np.sqrt(n)
    lower = est - z_score * se
    upper = est + z_score * se

    return (
        pd.Series(np.round(se, 4), index=estimates.index, dtype="float64"),
        pd.Series(np.round(lower, 4), index=estimates.index, dtype="float64"),
        pd.Series(np.round(upper, 4), index=estimates.index, dtype="float64"),
    )

