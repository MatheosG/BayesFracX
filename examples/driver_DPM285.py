# examples/driver_DPM285.py
# =============================================================================
# BayesFracX driver file for sample DPM285.
# Run from the BayesFracX folder:  python examples/driver_DPM285.py
# =============================================================================
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # find bfx/

from bfx import BAYESFRACX

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

bfx = BAYESFRACX(
    job_name=f"results_DPM285_{timestamp}",
    voxel_size= 0.053,       # mm/voxel = 53 micrometers
    seed=0
)

bfx.params["min_component_voxels"]["value"] = 500       
bfx.params["connectivity"]["value"] = 26
bfx.params["sampling_percent"]["value"] = 20       
# bfx.params["planarity_thresholds"]["value"] = [0.99, 0.90]
bfx.params["planarity_thresholds"]["value"] = [0.90, 0.80]
bfx.params["min_cluster_points"]["value"] = 80
bfx.params["alpha"]["value"] = 1        
bfx.params["max_components"]["value"] = 40
bfx.params["max_rounds"]["value"] = 10
bfx.params["max_iter"]["value"] = 200
bfx.params["n_init"]["value"] = 3
bfx.params["min_full_planarity"]["value"] = 0.80
bfx.print_params()

bfx.load_volume("data/DPM285/DPM285_BayesFracX.tif", dtype="uint8")
bfx.build_fracture_mask()
bfx.build_point_cloud()
bfx.subsample()
       
bfx.detect_fractures()
       
bfx.reconstruct()
       
bfx.characterize()
           
bfx.summary()
bfx.save()                       