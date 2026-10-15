# bfx/export.py
# =============================================================================
# Output functions: console summary, NPZ checkpoint, summary CSV, and STL export.
# =============================================================================
import numpy as np
import pyvista as pv
from skimage.measure import marching_cubes


def summary(fractures, rejected_points):
    print(
        f"\nFracture network: {len(fractures)} fractures, "
        f"{len(rejected_points):,} "
        "rejected points"
    )
    for fracture_id, fracture in enumerate(fractures, start=1):
        flag_text = "  FLAGGED" if fracture["flagged"] else ""
        aperture = fracture["aperture"]

        print(
            f"  {fracture_id}. tier={fracture['tier']}, "
            f"P={fracture['sampled_planarity']:.2f} "
            f"(full={fracture['full_planarity']:.2f}), "
            f"voxels={len(fracture['full_points']):,}, "
            f"dip={fracture['dip']:.1f}, "
            f"dipdir={fracture['dip_direction']:.1f}, "
            f"aperture={aperture['mean']:.2f}{flag_text}"
        )


def save_npz(fractures, rejected_points, sampled_points, voxel_size, path):
    np.savez(
        path,
        fractures=np.array(fractures, dtype=object),
        rejected_points=rejected_points,
        sampled_points=sampled_points,
        voxel_size=voxel_size,
    )
    print(f"  Saved checkpoint -> {path}")

def load_npz(path):
    checkpoint = np.load(path, allow_pickle=True)

    fractures = list(checkpoint["fractures"])
    rejected_points = checkpoint["rejected_points"]
    sampled_points = checkpoint["sampled_points"]
    voxel_size = float(checkpoint["voxel_size"])

    print(f"  Loaded {len(fractures)} fractures <- {path}")

    return fractures, rejected_points, sampled_points, voxel_size

def save_summary_csv(fractures, voxel_size, path):
    rows = [
        "id,tier,round,n_sampled_points,n_voxels,"
        "sampled_planarity,full_planarity,flagged,"
        "dip_deg,dip_direction_deg,area,equivalent_radius,"
        "aperture_mean,aperture_std,center_x,center_y,center_z"
    ]

    for fracture_id, fracture in enumerate(fractures, start=1):

        aperture = fracture["aperture"]
        center_physical = fracture["center"] * voxel_size

        rows.append(
            f"{fracture_id},{fracture['tier']},{fracture['round']},"
            f"{len(fracture['sampled_points'])},{len(fracture['full_points'])},"
            f"{fracture['sampled_planarity']:.4f},"
            f"{fracture['full_planarity']:.4f},{int(fracture['flagged'])},"
            f"{fracture['dip']:.2f},{fracture['dip_direction']:.2f},"
            f"{fracture['area']:.2f},{fracture['equivalent_radius']:.2f},"
            f"{aperture['mean']:.4f},{aperture['std']:.4f},"
            f"{center_physical[0]:.2f},{center_physical[1]:.2f},"
            f"{center_physical[2]:.2f}"
        )

    path.write_text("\n".join(rows))
    print(f"  Wrote summary -> {path}")

def to_stl(fractures, output_dir, voxel_size=1.0):
    
    for fracture_id, fracture in enumerate(fractures, start=1):
        full_points = fracture["full_points"].astype(int)  # XYZ
        min_corner = full_points.min(axis=0) 
        max_corner = full_points.max(axis=0)
        nz, ny, nx = (
            (max_corner - min_corner)[2] + 3,
            (max_corner - min_corner)[1] + 3,
            (max_corner - min_corner)[0] + 3,
        )
        local_mask = np.zeros((nz, ny, nx), dtype=np.uint8)  # local ZYX mask
        local_mask[
            full_points[:, 2] - min_corner[2] + 1,
            full_points[:, 1] - min_corner[1] + 1,
            full_points[:, 0] - min_corner[0] + 1,
        ] = 1

        vertices_zyx, triangles, _, _ = marching_cubes(local_mask, level=0.5)
        vertices_xyz = (
            vertices_zyx[:, ::-1] + (min_corner - 1)
        ) * voxel_size  # ZYX -> XYZ, global
        mesh_faces = np.hstack(
            [np.full((len(triangles), 1), 3), triangles]
        ).ravel()
        fracture_mesh = pv.PolyData(vertices_xyz, mesh_faces)

        stl_path = output_dir / f"fracture_{fracture_id}.stl"
        fracture_mesh.save(str(stl_path))
        print(
            f"  Fracture {fracture_id}: "
            f"{len(triangles):,} triangles -> {stl_path}"
        )
    print(f"  Wrote {len(fractures)} STL surfaces ")
