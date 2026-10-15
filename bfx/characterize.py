# bfx/characterize.py
# =============================================================================
# Fracture characterization: geometry, orientation, center, aperture.
# =============================================================================
import numpy as np
from scipy.spatial import ConvexHull, Delaunay


def characterize(fractures, distance_field, voxel_size=1.0):
    """
    For each fracture with full voxels ('full_points'), compute:
      'center'             fracture center
      'normal'             fracture plane normal
      'dip'                fracture dip angle
      'dip_direction'      fracture dip direction
      'polygon'            convex-hull boundary in 3D
      'area'               projected fracture area
      'equivalent_radius'  radius of circle with same projected area
      'aperture'           spatial aperture field + summary statistics
    """

    for fracture_id, fracture in enumerate(fractures, start=1):
        full_points = fracture["full_points"]

        center = full_points.mean(axis=0)
        centered_points = full_points - center

        _, _, principal_axes = np.linalg.svd(
            centered_points, full_matrices=False
        )
        axis_1, axis_2, normal = principal_axes

        if normal[2] < 0:
            normal = -normal

        dip = np.degrees(np.arccos(np.clip(normal[2], -1.0, 1.0)))

        dip_direction = np.degrees(np.arctan2(normal[0], normal[1])) % 360.0

        fracture["center"] = center
        fracture["normal"] = normal
        fracture["dip"] = dip
        fracture["dip_direction"] = dip_direction

        projected_points = np.column_stack(
            [centered_points @ axis_1, centered_points @ axis_2]
        )

        hull = ConvexHull(projected_points)
        polygon_2d = projected_points[hull.vertices]

        fracture["polygon"] = (
            center + polygon_2d[:, 0:1] * axis_1 + polygon_2d[:, 1:2] * axis_2
        )

        x_indices = full_points[:, 0].astype(int)
        y_indices = full_points[:, 1].astype(int)
        z_indices = full_points[:, 2].astype(int)

        voxel_distances = distance_field[z_indices, y_indices, x_indices]

        occupied_cells, cell_indices = np.unique(
            np.round(projected_points).astype(int), axis=0, return_inverse=True
        )

        cell_max_distance = np.zeros(len(occupied_cells))
        np.maximum.at(cell_max_distance, cell_indices, voxel_distances)
        voxels_per_cell = np.bincount(
            cell_indices, minlength=len(occupied_cells)
        )

        occupied_apertures = 2.0 * cell_max_distance * voxel_size

        single_voxel_mask = (voxels_per_cell == 1) & np.isclose(
            cell_max_distance, 1.0
        )

        occupied_apertures[single_voxel_mask] = voxel_size

        area = len(occupied_cells) * voxel_size**2

        fracture["area"] = area
        fracture["equivalent_radius"] = np.sqrt(area / np.pi)

        u = np.arange(
            occupied_cells[:, 0].min(), occupied_cells[:, 0].max() + 1
        )
        v = np.arange(
            occupied_cells[:, 1].min(), occupied_cells[:, 1].max() + 1
        )

        u_grid, v_grid = np.meshgrid(u, v)
        grid_cells = np.column_stack([u_grid.ravel(), v_grid.ravel()])

        hull_triangulation = Delaunay(polygon_2d)
        inside_hull = hull_triangulation.find_simplex(grid_cells) >= 0

        polygon_cells = grid_cells[inside_hull]

        aperture_values = np.zeros(len(polygon_cells), dtype=float)

        aperture_lookup = {
            tuple(cell): aperture_value
            for cell, aperture_value in zip(occupied_cells, occupied_apertures)
        }

        for cell_index, cell in enumerate(polygon_cells):
            aperture_values[cell_index] = aperture_lookup.get(tuple(cell), 0.0)

        aperture_points = (
            center
            + polygon_cells[:, 0:1] * axis_1
            + polygon_cells[:, 1:2] * axis_2
        )

        positive_apertures = aperture_values[aperture_values > 0]

        fracture["aperture"] = {
            "coords_2d": polygon_cells,
            "coords_3d": aperture_points,
            "values": aperture_values,
            "mean": float(positive_apertures.mean()),
            "std": float(positive_apertures.std())
        }

        print(
            f"  Fracture {fracture_id}: "
            f"dip={dip:.1f} deg, "
            f"dipdir={dip_direction:.1f} deg, "
            f"area={fracture['area']:.1f}, "
            f"r_eq={fracture['equivalent_radius']:.2f}, "
            f"aperture={fracture['aperture']['mean']:.2f} "
            f"+/- {fracture['aperture']['std']:.2f}"
        )