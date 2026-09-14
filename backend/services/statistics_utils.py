"""
Statistical Utilities for Petroleum Engineering & Rig Risk Analytics

Provides small-sample Wilson Score Confidence Intervals (Wilson 1927)
to replace spurious raw percentages from small counts of analog wells or historical incidents.
"""

import math
from typing import Dict, Any


def wilson_confidence_interval(successes: int, total: int, confidence: float = 0.95) -> Dict[str, Any]:
    """
    Computes the Wilson score interval for a binomial proportion —
    more reliable than a normal approximation or raw percentage for small sample sizes.
    
    Formula:
        center = p_hat + z^2 / (2n)
        margin = z * sqrt( (p_hat * (1 - p_hat) / n) + (z^2 / (4n^2)) )
        lower = (center - margin) / (1 + z^2 / n)
        upper = (center + margin) / (1 + z^2 / n)
    """
    if total <= 0:
        return {
            "point_estimate": 0.0,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "sample_size": 0,
            "confidence": confidence,
            "formatted": "0% (n=0)"
        }

    # Constrain successes between 0 and total
    k = max(0, min(successes, total))
    n = total

    # Standard normal quantiles
    if abs(confidence - 0.99) < 0.005:
        z = 2.576
    elif abs(confidence - 0.90) < 0.005:
        z = 1.645
    else:
        z = 1.95996  # 95% default standard normal quantile (1.96)

    p_hat = k / n
    denominator = 1.0 + (z**2 / n)
    center = p_hat + (z**2 / (2.0 * n))
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z**2 / (4.0 * n**2)))

    lower = max(0.0, (center - margin) / denominator)
    upper = min(1.0, (center + margin) / denominator)

    pct = round(p_hat * 100.0, 1)
    lower_pct = round(lower * 100.0, 1)
    upper_pct = round(upper * 100.0, 1)
    conf_pct = round(confidence * 100.0)

    formatted_str = f"{pct:.0f}% ({conf_pct}% CI: {lower_pct:.0f}%-{upper_pct:.0f}%, n={n})"

    return {
        "point_estimate": round(p_hat, 3),
        "lower_bound": round(lower, 3),
        "upper_bound": round(upper, 3),
        "ci_lower": round(lower, 3),
        "ci_upper": round(upper, 3),
        "sample_size": n,
        "successes": k,
        "confidence": confidence,
        "formatted": formatted_str
    }


def format_wilson_insight(successes: int, total: int, metric_name: str = "success rate", confidence: float = 0.95) -> str:
    """Formats honest small-sample statistics with explicit Wilson confidence intervals."""
    stats = wilson_confidence_interval(successes, total, confidence)
    return stats["formatted"]
