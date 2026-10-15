# examples/driver_DPM443.py
# =============================================================================
# BayesFracX driver file for sample DPM443.
# Run from the BayesFracX folder:  python examples/driver_DPM443.py
# =============================================================================
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1])) 

from bfx import BAYESFRACX

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

bfx = BAYESFRACX(
    job_name=f"results_DPM443_{timestamp}", 
    voxel_size=0.012559,       # mm/voxel = 12.559 micrometers, 
    seed=0
)

bfx.params["min_component_voxels"]["value"] = 500  # drop pores < this (voxels)
bfx.params["connectivity"]["value"] = 26
bfx.params["sampling_percent"]["value"] = 5  # sampling %, speed knob
bfx.params["planarity_thresholds"]["value"] = [0.99, 0.95]
bfx.params["min_cluster_points"]["value"] = 80
bfx.params["alpha"]["value"] = 1
bfx.params["max_components"]["value"] = 50
bfx.params["max_rounds"]["value"] = 10
bfx.params["max_iter"]["value"] = 200
bfx.params["n_init"]["value"] = 3
bfx.params["min_full_planarity"]["value"] = 0.90
bfx.print_params()

bfx.load_volume("data/DPM443/DPM443.tif", dtype="uint8")
bfx.build_fracture_mask()
bfx.build_point_cloud()
bfx.subsample()


bfx.detect_fractures()

bfx.reconstruct()

bfx.characterize()

bfx.summary()
bfx.save() 
