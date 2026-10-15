# examples/driver_synthetic_15fractures.py
# =============================================================================
# BayesFracX driver for the synthetic 15-fracture validation case.
# Run from the BayesFracX folder:
# python examples/driver_synthetic_15fractures.py
# =============================================================================
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bfx import BAYESFRACX

bfx = BAYESFRACX(
    job_name="results_synthetic_15fractures",
    voxel_size=1.0,
    seed=0
)

bfx.params["min_component_voxels"]["value"] = 500
bfx.params["connectivity"]["value"] = 26
bfx.params["sampling_percent"]["value"] = 10
bfx.params["planarity_thresholds"]["value"] = [0.99]
bfx.params["min_cluster_points"]["value"] = 30
bfx.params["alpha"]["value"] = 1
bfx.params["max_components"]["value"] = 15
bfx.params["max_rounds"]["value"] = 10
bfx.params["max_iter"]["value"] = 200
bfx.params["n_init"]["value"] = 3
bfx.params["min_full_planarity"]["value"] = 0.95
bfx.print_params()

bfx.load_volume(
    "data/synthetic_15fractures.tif"
)

bfx.build_fracture_mask()
bfx.build_point_cloud()
bfx.subsample()

bfx.plot_points()

# FRACTURE DETECTION
bfx.detect_fractures()
bfx.plot_fractures(
    use_full=False
)

bfx.reconstruct()
bfx.plot_fractures(
    use_full=True
)

bfx.characterize()
bfx.plot_polygons()

bfx.summary()
bfx.save()
bfx.to_stl()