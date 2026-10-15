# BayesFracX

**BayesFracX: A Bayesian clustering-based algorithm for individual fracture extraction and DFN-ready characterization from 3D CT images**

BayesFracX (Bayesian Fracture eXtraction) is a training-free Python algorithm for separating and characterizing individual fracture elements from connected, pre-segmented three-dimensional CT volumes.

The method combines Dirichlet-process Bayesian Gaussian mixture model (DP-BGMM) candidate clustering with iterative geometric acceptance, full-resolution watershed reconstruction, quality control, and fracture characterization. Each reconstructed element is reduced to a planar representation described by its position, orientation, boundary, size, and spatial aperture field.

BayesFracX requires a pre-segmented three-dimensional binary fracture volume with fracture voxels encoded as `0` and non-fracture voxels as nonzero values. Segmentation of grayscale CT data is outside the scope of the method.

## Repository contents

| Path | Contents |
|---|---|
| `bfx/` | BayesFracX source modules. |
| `data/synthetic_3fractures.tif` | Three-fracture synthetic validation input. |
| `data/synthetic_15fractures.tif` | Fifteen-fracture synthetic validation input. |
| `docs/user_guide.md` | Inputs, workflow, parameters, outputs, interpretation, and reproduction instructions. |
| `examples/driver_synthetic_3fractures.py` | Three-fracture validation driver. |
| `examples/driver_synthetic_15fractures.py` | Fifteen-fracture validation driver. |
| `examples/driver_DPM86.py` | Coal cleat application. |
| `examples/driver_DPM195.py` | Tortuous granite fracture application. |
| `examples/driver_DPM205.py` | Laminated Mancos shale application. |
| `examples/driver_DPM285.py` | Hydraulically fractured tight sandstone application. |
| `examples/driver_DPM443.py` | Induced shale fracture network application. |
| `requirements.txt` | Python dependencies and tested package versions. |
| `pyproject.toml` | Python package metadata, build configuration, and installation dependencies. |
| `LICENSE` | MIT License. |

## Requirements

BayesFracX has been tested with Python 3.14.5 and the package versions listed in `requirements.txt`:

```text
connected-components-3d==4.0.0
edt==3.1.2
numpy==2.4.6
pyvista==0.48.4
scikit-image==0.26.0
scikit-learn==1.9.0
scipy==1.18.0
tifffile==2026.7.31
vtk==9.6.2
```

### Tested computing environment

| Component | Tested configuration |
|---|---|
| Operating system | Microsoft Windows 11 Home, 64-bit, version 10.0.26200 |
| CPU | AMD Ryzen 7 4800H with Radeon Graphics |
| Installed RAM | 15.4 GB |
| Python | `3.14.5` |

These entries describe the tested setup. They are not minimum hardware requirements. A GPU is not required for fracture extraction and characterization. Interactive plots require a working PyVista/VTK rendering environment.

Clustering cost depends on the number of sampled fracture points. Full-resolution distance-transform and watershed operations retain arrays at the input-volume dimensions, so reducing the sampling percentage does not proportionally reduce their memory requirements. See [Computational considerations](docs/user_guide.md#6-computational-considerations).

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/MatheosG/BayesFracX
cd BayesFracX
```

Install BayesFracX and its required Python dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

The `pyproject.toml` file defines BayesFracX as an installable Python package and specifies its required dependencies. The exact package versions used to produce the manuscript results are recorded in `requirements.txt`.

Run the examples from the repository root so that input paths resolve correctly.

## Quick start

Run the three-fracture synthetic validation case:

```bash
python examples/driver_synthetic_3fractures.py
```

The fifteen-fracture case can be run with:

```bash
python examples/driver_synthetic_15fractures.py
```

Both TIFF volumes are included in `data/`. The synthetic drivers display interactive plots. Close each plot window to continue. For unattended runs, comment out the `bfx.plot_*()` calls.

The following workflow uses the three-fracture reference settings. Run it from the repository root:

```python
from bfx import BAYESFRACX

bfx = BAYESFRACX(
    job_name="results_example",
    voxel_size=1.0,
    seed=0,
)

# Three-fracture reference settings. Other parameters retain their defaults.
bfx.params["sampling_percent"]["value"] = 100
bfx.params["planarity_thresholds"]["value"] = [0.99]
bfx.params["max_components"]["value"] = 3

bfx.load_volume("data/synthetic_3fractures.tif")
bfx.build_fracture_mask()
bfx.build_point_cloud()
bfx.subsample()
bfx.detect_fractures()
bfx.reconstruct()
bfx.characterize()
bfx.summary()
bfx.save()
```

This writes `fractures.npz` and `summary.csv` to `results_example/`. The checkpoint stores fracture records and point clouds. The CSV reports properties of the reconstructed fractures, including their full-resolution planarity quality-control state. Optional `bfx.to_stl()` exports their voxel-derived surfaces.

`voxel_size` sets the physical length per voxel. Aperture and equivalent radius use that length unit, and area uses its square. Stored point coordinates remain in voxel coordinates. CSV centers and STL coordinates are scaled by `voxel_size`. With `voxel_size=1.0`, synthetic lengths are reported in voxel-size units. See [Output units](docs/user_guide.md#47-output-units) for the complete mapping.

## Reproducing the article results

### Synthetic validation

Run the two synthetic drivers above without changing their parameters. The reference outcomes reported in the manuscript are:

| Case | Sampling | Planarity thresholds | `max_components` | `min_cluster_points` | Extracted fractures | Rejected sampled points |
|---|---:|---|---:|---:|---:|---:|
| Three fractures | `100%` | `[0.99]` | `3` | `80` | `3` | `0` |
| Fifteen fractures | `10%` | `[0.99]` | `15` | `30` | `15` | `0` |

Both drivers use `seed=0`. Their output directories are `results_synthetic_3fractures/` and `results_synthetic_15fractures/`. Repeating a driver with the same output directory overwrites its saved files.

### Experimental CT applications

The segmented inputs and corresponding reference outputs are provided
through the BayesFracX dataset on the Digital Porous Media Portal (DPMP):

**BayesFracX data:** https://doi.org/10.17612/7z7r-v755

Download the segmented inputs and place them at the following paths, relative to the repository root. RAW inputs use `dtype="uint8"`. Their shapes are specified in NumPy `(Z, Y, X)` order.

| Case | Input path used by the driver | Volume shape `(Z, Y, X)` | `voxel_size` (mm) |
|---|---|---|---:|
| DPM-86 | `data/DPM86/DPM86_segmented.tif` | `(80, 1497, 1505)` | `0.0165` |
| DPM-195 | `data/DPM195/DPM195_segmented.tif` | `(1300, 275, 843)` | `0.054` |
| DPM-205 | `data/DPM205_45_1_post_BayesFracX.tif` | `(750, 590, 620)` | `0.065` |
| DPM-285 | `data/DPM285/DPM285_BayesFracX.tif` | `(584, 890, 425)` | `0.053` |
| DPM-443 | `data/DPM443/DPM443.tif` | `(500, 550, 550)` | `0.012559` |

TIFF dimensions are read from the file. The table records the selected volumes used in the manuscript, which may be subsets of the original datasets. If a downloaded file has a different name or location, update the path in the driver's `load_volume()` call while retaining its shape, dtype, and voxel size.

Run:

```bash
python examples/driver_DPM86.py
python examples/driver_DPM195.py
python examples/driver_DPM205.py
python examples/driver_DPM285.py
python examples/driver_DPM443.py
```

Each driver defines its case-specific settings and output directory. Compare the resulting `summary.csv` and reconstructed elements with the archived reference outputs. The DPM-86 driver also opens an interactive point-cloud plot.

The original datasets are:

| Case | Original dataset | DOI |
|---|---|---|
| DPM-86 | Moura Coal | `10.17612/P7V888` |
| DPM-195 | Fracture in granite | `10.17612/P7QX1X` |
| DPM-205 | Fracture Patterns in Laminated Mancos Shale | `10.17612/P7F38T` |
| DPM-285 | A full-size fracture of tight sandstone induced by water, N2 and CO2 | `10.17612/4W5E-DQ86` |
| DPM-443 | Induced fracture network and a hydraulic fracture in a shale sample | `10.17612/XQ44-CJ63` |

### Sensitivity, stochastic stability, and subsampling

The [User Guide](docs/user_guide.md#7-reproducible-examples) lists the exact parameter variations and seed values used in the manuscript, instructions for modifying the fifteen-fracture driver, and guidance for recording detection time.

Use the same inputs, code version, dependency versions, and seed when comparing reference runs. Record the computing environment when comparing runtimes.

## Code and data availability

**Source code:** https://github.com/MatheosG/BayesFracX

**Archived software (v1.0.0):** https://doi.org/10.5281/zenodo.23405829

**Experimental data and results:** https://doi.org/10.17612/7z7r-v755

## Citation

If you use BayesFracX, please cite the accompanying article:

Giakoumi, M., Chang, B. C., and Prodanović, M. (2026).
*BayesFracX: A Bayesian clustering-based algorithm for individual fracture extraction and DFN-ready characterization from 3D CT images*.
[JOURNAL]. [Article DOI]

```bibtex
@article{GiakoumiEtAl2026BayesFracX,
  author  = {Giakoumi, Matheos and Chang, Bernard C. and Prodanovi{\'c}, Ma{\v{s}}a},
  title   = {BayesFracX: A Bayesian clustering-based algorithm for individual fracture extraction and DFN-ready characterization from 3D CT images},
  journal = {TO_BE_ADDED},
  year    = {2026},
  doi     = {TO_BE_ADDED},
  url     = {TO_BE_ADDED}
}
```

## Software citation

The BayesFracX v1.0.0 release is permanently archived in Zenodo.

Giakoumi, M., Chang, B. C., and Prodanović, M. (2026).
*BayesFracX* (Version 1.0.0) [Computer software].
Zenodo. https://doi.org/10.5281/zenodo.23405829

```bibtex
@misc{GiakoumiEtAl2026BayesFracXSoftware,
  author       = {Giakoumi, Matheos and Chang, Bernard C. and Prodanovi{\'c}, Ma{\v{s}}a},
  title        = {BayesFracX},
  year         = {2026},
  version      = {1.0.0},
  howpublished = {Zenodo},
  note         = {Computer software},
  doi          = {10.5281/zenodo.23405829}
}
```

## Data citation

The segmented experimental fracture volumes and corresponding BayesFracX
outputs used in the article are archived in the Digital Porous Media Portal.

Please cite the dataset as:

Giakoumi, M., Chang, B. C., and Prodanović, M. (2026).
*BayesFracX: Processed 3D CT fracture volumes and extraction results*.
Digital Porous Media Portal. https://doi.org/10.17612/7z7r-v755

```bibtex
@misc{GiakoumiEtAl2026BayesFracXData,
  author       = {Giakoumi, Matheos and Chang, Bernard C. and Prodanovi{\'c}, Ma{\v{s}}a},
  title        = {BayesFracX: Processed 3D CT fracture volumes and extraction results},
  year         = {2026},
  howpublished = {Digital Porous Media Portal},
  note         = {[dataset]},
  doi          = {10.17612/7z7r-v755}
}
```

## License

BayesFracX is distributed under the MIT License. See [`LICENSE`](LICENSE).

## Authors

**Matheos Giakoumi**  
**Bernard C. Chang**  
**Maša Prodanović**

Hildebrand Department of Petroleum and Geosystems Engineering  
The University of Texas at Austin
