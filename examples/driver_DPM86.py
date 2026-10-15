# examples/driver_DPM86.py
# =============================================================================
# BayesFracX driver file for sample DPM86.
# Run from the BayesFracX folder:
# python examples/driver_DPM86.py
# =============================================================================

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bfx import BAYESFRACX

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

bfx = BAYESFRACX(
    job_name=f"results_DPM86_{timestamp}",
    voxel_size=0.0165,       # mm/voxel = 16.5 micrometers
    seed=0
)

# Parameters
bfx.params["min_component_voxels"]["value"] = 5000
bfx.params["connectivity"]["value"] = 26
bfx.params["sampling_percent"]["value"] = 20
bfx.params["planarity_thresholds"]["value"] = [
    0.99,
    0.90
]
bfx.params["min_cluster_points"]["value"] = 50
bfx.params["alpha"]["value"] = 1.0
bfx.params["max_components"]["value"] = 50
bfx.params["max_rounds"]["value"] = 10
bfx.params["max_iter"]["value"] = 200
bfx.params["n_init"]["value"] = 3
bfx.params["min_full_planarity"]["value"] = 0.80
bfx.print_params()

# Input
bfx.load_volume("data/DPM86/DPM86_segmented.tif", dtype="uint8")
bfx.build_fracture_mask()
bfx.build_point_cloud()
bfx.subsample()
bfx.plot_points()

# Detection
bfx.detect_fractures()

# Reconstruction
bfx.reconstruct()

# Characterization
bfx.characterize()

# Output
bfx.summary()

# Export
bfx.save()
