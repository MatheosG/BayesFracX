# bfx/io.py
# =============================================================================
# Input: load volume, build fracture mask, build point cloud, subsample.
# =============================================================================
import re
from pathlib import Path

import cc3d
import numpy as np


def _natural_key(path):
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def load_volume(path, shape=None, dtype="uint8"):
    path = Path(path)
    dtype = np.dtype(dtype)
    suffix = path.suffix.lower()

    if suffix == ".raw":
        if shape is None:
            raise ValueError("raw volumes need shape=(Z, Y, X)")
        volume = np.fromfile(path, dtype=dtype).reshape(shape)

    elif suffix in {".tif", ".tiff"} or path.is_dir():
        import tifffile as tiff

        if path.is_dir():
            slice_paths = sorted(
                list(path.glob("*.tif")) + list(path.glob("*.tiff")),
                key=_natural_key,
            )
            first_slice = tiff.imread(slice_paths[0])
            volume = np.empty(
                (len(slice_paths), *first_slice.shape), dtype=first_slice.dtype
            )
            volume[0] = first_slice
            for file_index, file_path in enumerate(slice_paths[1:], start=1):
                volume[file_index] = tiff.imread(file_path)
        else:
            volume = tiff.imread(path)
            if volume.ndim > 3:
                volume = np.squeeze(volume)
        volume = volume.astype(dtype)

    else:
        raise ValueError(f"Unknown volume format: {path.suffix}")

    print(f"  Loaded {path}: shape={volume.shape}, dtype={volume.dtype}")
    return volume


def build_fracture_mask(
    volume,
    min_component_voxels=500,
    connectivity=26,
):
    fracture_mask = volume == 0
    print(f"  Raw fracture voxels: {fracture_mask.sum():,}")

    if min_component_voxels > 0:
        fracture_mask = cc3d.dust(
            fracture_mask.astype(np.uint8, copy=False),
            threshold=min_component_voxels,
            connectivity=connectivity,
            in_place=False,
        ).astype(bool, copy=False)

        print(
            f"  Small-component filter (<{min_component_voxels} vox): "
            f"{fracture_mask.sum():,} voxels retained"
        )

    return fracture_mask


def build_point_cloud(fracture_mask):
    z_indices, y_indices, x_indices = np.where(fracture_mask)
    full_points = np.column_stack([x_indices, y_indices, z_indices]).astype(
        np.float32
    )
    print(f"  Full points: {len(full_points):,}")
    return full_points


def subsample(full_points, sampling_percent, seed):
    random_generator = np.random.default_rng(seed)

    if sampling_percent >= 100:
        print("  sampling_percent >= 100: no subsampling")
        return full_points

    n_sampled = max(1, int(len(full_points) * sampling_percent / 100.0))

    sample_indices = random_generator.permutation(len(full_points))[:n_sampled]

    sampled_points = full_points[sample_indices]

    print(
        f"  Subsampled to {sampling_percent}%: {len(sampled_points):,} points"
    )
    return sampled_points