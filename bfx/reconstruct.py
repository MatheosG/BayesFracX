# bfx/reconstruct.py
# =============================================================================
# Watershed reconstruction: sampled fracture seeds to full-resolution voxels,
# =============================================================================
import edt
import numpy as np
from skimage.segmentation import watershed

from .detect import planarity_index


def compute_edt(fracture_mask):
    print("  Distance transform...")
    return edt.edt(fracture_mask)


def reconstruct(
    fractures,
    rejected_points,
    fracture_mask,
    distance_field,
    min_full_planarity,
):
    markers = np.zeros(fracture_mask.shape, dtype=np.int32)
    for fracture_id, fracture in enumerate(fractures, start=1):
        sampled_points = fracture["sampled_points"].astype(int)
        markers[
            sampled_points[:, 2], sampled_points[:, 1], sampled_points[:, 0]
        ] = fracture_id  # XYZ -> ZYX
    if len(rejected_points) > 0:
        rejected_label = len(fractures) + 1
        rejected_points = rejected_points.astype(int)
        markers[
            rejected_points[:, 2],
            rejected_points[:, 1],
            rejected_points[:, 0],
        ] = rejected_label

    print("  Watershed...")
    watershed_labels = watershed(
        -distance_field, markers=markers, mask=fracture_mask
    )

    print("  QC: planarity on full voxels...")
    n_flagged = 0
    for fracture_id, fracture in enumerate(fractures, start=1):
        z_indices, y_indices, x_indices = np.where(
            watershed_labels == fracture_id
        )
        fracture["full_points"] = np.column_stack(
            [x_indices, y_indices, z_indices]
        ).astype(np.float32)

        full_planarity = planarity_index(fracture["full_points"])
        fracture["full_planarity"] = full_planarity
        fracture["flagged"] = full_planarity < min_full_planarity
        n_flagged += fracture["flagged"]

        warning_text = "  <-- FLAGGED" if fracture["flagged"] else ""
        print(
            f"    Fracture {fracture_id}: "
            f"{len(fracture['sampled_points']):,} seeds -> "
            f"{len(fracture['full_points']):,} voxels, "
            f"P sampled={fracture['sampled_planarity']:.3f} "
            f"full={full_planarity:.3f}{warning_text}"
        )

    if n_flagged:
        print(
            f"  {n_flagged} fracture(s) flagged: inspect before trusting them."
        )