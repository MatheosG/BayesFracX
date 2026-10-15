# bfx/detect.py
# =============================================================================
# Fracture detection: iterative DP-BGMM clustering + planarity acceptance.
# =============================================================================
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.mixture import BayesianGaussianMixture

warnings.filterwarnings("ignore", category=ConvergenceWarning)


def planarity_index(points):
    """
    Planarity from squared singular values of the centered point cloud:
        P = (lambda_2 - lambda_3) / lambda_2
    P ~ 1 -> planar cluster
    P ~ 0 -> volumetric or line-like cluster
    """
    if len(points) < 3:
        return 0.0

    singular_values = np.linalg.svd(points - points.mean(0), compute_uv=False)

    _, lambda_2, lambda_3 = singular_values**2

    if lambda_2 <= 0:
        return 0.0

    return (lambda_2 - lambda_3) / lambda_2


def detect_fractures(
    sampled_points,
    planarity_thresholds,
    min_cluster_points,
    max_components,
    alpha,
    max_rounds,
    max_iter,
    n_init,
    seed,
):
    random_generator = np.random.default_rng(seed)
    fractures = []
    active_mask = np.ones(len(sampled_points), dtype=bool)

    for tier_id, min_planarity in enumerate(planarity_thresholds, start=1):
        print(f"\n--- Tier {tier_id}: P >= {min_planarity} ---")

        for round_id in range(1, max_rounds + 1):
            active_points = sampled_points[active_mask]

            if len(active_points) < min_cluster_points:
                print(
                    f"  Stopping tier: {len(active_points)} points "
                    f"< {min_cluster_points}"
                )
                break

            print(
                f"  Round {round_id}: {len(active_points):,} points, "
                f"K={max_components}"
            )

            prior_variance = np.mean(np.var(active_points, axis=0))

            bgmm = BayesianGaussianMixture(
                n_components=max_components,
                covariance_type="full",
                weight_concentration_prior_type="dirichlet_process",
                weight_concentration_prior=alpha,
                covariance_prior=np.eye(3) * prior_variance,
                max_iter=max_iter,
                init_params="random",
                n_init=n_init,
                random_state=int(random_generator.integers(2**31)),
            ).fit(active_points)

            cluster_labels = bgmm.predict(active_points)

            active_indices = np.where(active_mask)[0]
            n_accepted = 0

            for cluster_id in np.unique(cluster_labels):
                cluster_mask = cluster_labels == cluster_id
                cluster_points = active_points[cluster_mask]

                planarity = planarity_index(cluster_points)

                accepted = (
                    planarity >= min_planarity
                    and len(cluster_points) >= min_cluster_points
                )

                status_tag = (
                    "+"
                    if accepted
                    else (
                        "s"
                        if len(cluster_points) < min_cluster_points
                        else "x"
                    )
                )

                print(
                    f"    Cluster {cluster_id}: "
                    f"{len(cluster_points):,} pts, "
                    f"P={planarity:.3f} [{status_tag}]"
                )

                if accepted:
                    fractures.append(
                        {
                            "tier": tier_id,
                            "round": round_id,
                            "sampled_planarity": planarity,
                            "sampled_points": cluster_points.copy(),
                        }
                    )

                    active_mask[active_indices[cluster_mask]] = False
                    n_accepted += 1

            print(f"    Accepted this round: {n_accepted}")

    rejected_points = sampled_points[active_mask]

    print(
        f"\nDetection done: {len(fractures)} fractures, "
        f"{len(rejected_points):,} rejected points"
    )

    return fractures, rejected_points