# plot_after.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bfx import BAYESFRACX

# Load saved checkpoint
bfx = BAYESFRACX(
    # job_name="results/results_synthetic_3fractures", voxel_size=1.0,
    # job_name="results/results_synthetic_15fractures", voxel_size=1.0,
    # job_name="results/results_DPM86", voxel_size=0.0165,  
    # job_name="results/results_DPM195", voxel_size=0.054,   
    # job_name="results/results_DPM205_45_1", voxel_size= 0.065, 
    # job_name="results/results_DPM285", voxel_size= 0.053,
    # job_name="results_DPM443", voxel_size=0.012559, 
    seed=0,
)

bfx.load()
bfx.summary()


# Sampled point cloud before clustering
bfx.plot_points()

#  Detected clusters before watershed
bfx.plot_fractures(use_full=False)

# Full fractures after watershed
bfx.plot_fractures(use_full=True)

# Reduced fracture surfaces colored by aperture
bfx.plot_polygons()