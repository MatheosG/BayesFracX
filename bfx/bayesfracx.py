# bfx/bayesfracx.py
# =============================================================================
# The BayesFracX driver class.
# =============================================================================
from pathlib import Path

import numpy as np

from . import characterize, detect, export, io, reconstruct, visualize


class BAYESFRACX:
    def __init__(self, job_name, voxel_size=1.0, seed=0):
        """create the object: bfx = BAYESFRACX(...)."""
        self.job_name = job_name
        self.output_dir = Path(job_name)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.voxel_size = voxel_size
        self.seed = seed

        random_generator = np.random.default_rng(seed)

        self.sampling_seed = int(random_generator.integers(2**31))
        self.detection_seed = int(random_generator.integers(2**31))
        self.plotting_seed = int(random_generator.integers(2**31))

        self.volume = None          # raw volume (Z, Y, X)
        self.fracture_mask = None   # boolean fracture mask
        self.full_points = None     # all fracture voxels, XYZ
        self.sampled_points = None  # subsampled points for detection
        self.fractures = []         # list of fracture dicts
        self.rejected_points = None # points not assigned to any fracture
        self.distance_field = None  # EDT for watershed and aperture

        self.params = {
            # preprocessing
            "min_component_voxels": {
                "value": 500,
                "description": (
                    "Drop fracture components smaller than this (voxels)."
                ),
            },
            "connectivity": {
                "value": 26,
                "description": "Voxel connectivity for connected components.",
            },
            "sampling_percent": {
                "value": 2,
                "description": (
                    "% of fracture voxels kept for detection."
                ),
            },
            # detection
            "planarity_thresholds": {
                "value": [0.90, 0.85],
                "description": (
                    "Planarity acceptance thresholds, relaxed per tier."
                ),
            },
            "min_cluster_points": {
                "value": 80,
                "description": (
                    "Reject clusters smaller than this (sampled points)."
                ),
            },
            "max_components": {
                "value": 10,
                "description": (
                    "BGMM components per fit (upper bound, DP prunes)."
                ),
            },
            "max_rounds": {
                "value": 10,
                "description": "Clustering rounds per tier.",
            },
            "alpha": {
                "value": 1.0,
                "description": "Dirichlet-process concentration parameter.",
            },
            "max_iter": {"value": 200, "description": "BGMM EM iterations."},
            "n_init": {
                "value": 3,
                "description": "BGMM restarts per fit (stability).",
            },
            # QC
            "min_full_planarity": {
                "value": 0.80,
                "description": (
                    "Flag fracture if full-voxel planarity drops below."
                ),
            },
        }
    def _need(self, attribute, step):
        value = getattr(self, attribute)

        if value is None or (attribute == "fractures" and not value):
            raise RuntimeError(
                f"Nothing in self.{attribute} -- run {step} first."
            )
        
    def _need_characterized(self):
        self._need("fractures", "detect_fractures()")

        if not all("aperture" in fracture for fracture in self.fractures):
            raise RuntimeError(
                "Fractures have not been characterized -- "
                "run reconstruct() and characterize() first."
            )

    def print_params(self):

        print(f"\nBayesFracX parameters (job: {self.job_name})")
        for parameter_name, parameter in self.params.items():
            print(
                f"  {parameter_name:20s} = {str(parameter['value']):16s} "
                f"# {parameter['description']}"
            )

    def load_volume(self, path, shape=None, dtype="uint8"):
        print("\n[load_volume]")
        self.volume = io.load_volume(path, shape, dtype)

    def build_fracture_mask(self):
        self._need("volume", "load_volume()")
        print("\n[build_fracture_mask]")
        self.fracture_mask = io.build_fracture_mask(
            self.volume,
            min_component_voxels=self.params["min_component_voxels"]["value"],
            connectivity=self.params["connectivity"]["value"],
        )
        self.volume = None  

    def build_point_cloud(self):
        self._need("fracture_mask", "build_fracture_mask()")
        print("\n[build_point_cloud]")
        self.full_points = io.build_point_cloud(self.fracture_mask)

    def subsample(self):
        self._need("full_points", "build_point_cloud()")
        print("\n[subsample]")
        self.sampled_points = io.subsample(
            self.full_points,
            self.params["sampling_percent"]["value"],
            self.sampling_seed,
        )

    def detect_fractures(self):
        self._need("sampled_points", "subsample()")
        print("\n[detect_fractures]")
        self.fractures, self.rejected_points = detect.detect_fractures(
            self.sampled_points,
            planarity_thresholds=self.params["planarity_thresholds"]["value"],
            min_cluster_points=self.params["min_cluster_points"]["value"],
            max_components=self.params["max_components"]["value"],
            alpha=self.params["alpha"]["value"],
            max_rounds=self.params["max_rounds"]["value"],
            max_iter=self.params["max_iter"]["value"],
            n_init=self.params["n_init"]["value"],
            seed=self.detection_seed,
        )

    def reconstruct(self):
        self._need("fractures", "detect_fractures()")
        self._need("fracture_mask", "build_fracture_mask()")
        print("\n[reconstruct]")
        self.distance_field = reconstruct.compute_edt(self.fracture_mask)
        reconstruct.reconstruct(
            self.fractures,
            self.rejected_points,
            self.fracture_mask,
            self.distance_field,
            min_full_planarity=self.params["min_full_planarity"]["value"],
        )

    def characterize(self):
        self._need("fractures", "detect_fractures() and reconstruct()")
        self._need("distance_field", "reconstruct()")
        print("\n[characterize]")
        characterize.characterize(
            self.fractures, self.distance_field, self.voxel_size
        )

    def summary(self):
        self._need_characterized()
        export.summary(self.fractures, self.rejected_points)

    def save(self):
        self._need_characterized()
        print("\n[save]")
        export.save_npz(
            self.fractures,
            self.rejected_points,
            self.sampled_points,
            self.voxel_size,
            self.output_dir / "fractures.npz",
        )
        export.save_summary_csv(
            self.fractures, self.voxel_size, self.output_dir / "summary.csv"
        )

    def load(self, path=None):
        path = path or (self.output_dir / "fractures.npz")
        print("\n[load]")
        (
            self.fractures,
            self.rejected_points,
            self.sampled_points,
            self.voxel_size,
        ) = export.load_npz(path)

    def to_stl(self):
        self._need_characterized()
        print("\n[to_stl]")
        export.to_stl(self.fractures, self.output_dir, self.voxel_size)

    # Plots
    def plot_points(self):
        visualize.plot_points(
            self.full_points,
            self.sampled_points,
            seed=self.plotting_seed,
        )

    def plot_fractures(self, use_full=None):
        self._need("fractures", "detect_fractures()")

        if use_full is None:
            use_full = self.fractures[0].get("full_points") is not None

        visualize.plot_fractures(
            self.fractures,
            self.rejected_points,
            seed=self.plotting_seed,
            use_full=use_full,
        )

    def plot_polygons(self):
        self._need_characterized()
        visualize.plot_polygons(self.fractures)