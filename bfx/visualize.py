# bfx/visualize.py
# =============================================================================
# Visualization functions.
# =============================================================================
from matplotlib import colormaps

import numpy as np
import pyvista as pv
from scipy.spatial import Delaunay


def plot_points(full_points, sampled_points, seed, max_points=300_000):
    random_generator = np.random.default_rng(seed)

    panels = []
    if full_points is not None:
        panels.append(("Full cloud", full_points, "gray"))
    if sampled_points is not None:
        panels.append(("Sampled", sampled_points, "tomato"))
    if not panels:
        return

    plotter = pv.Plotter(
        shape=(1, len(panels)),
        window_size=(900 * len(panels), 800),
    )

    for panel_index, (title, points, color) in enumerate(panels):
        plotter.subplot(0, panel_index)
        plotter.set_background("white")

        n_points = len(points)
        display_points = points

        if n_points > max_points:
            sample_indices = random_generator.choice(
                n_points, max_points, replace=False
            )
            display_points = points[sample_indices]

        if len(display_points):
            plotter.add_points(
                display_points,
                style="points_gaussian",
                color=color,
                point_size=3,
                render_points_as_spheres=True,
                emissive=False,
            )

        plotter.add_title(
            f"{title}\n{n_points:,} points",
            font_size=20,
            color="black",
        )
        plotter.add_axes(color="black")

    plotter.link_views()
    plotter.show()


def plot_fractures(fractures, rejected_points, seed, use_full=True,
                   max_points=100_000):
    random_generator = np.random.default_rng(seed)
    cmap = colormaps["inferno"]

    plotter = pv.Plotter(window_size=(1200, 900))
    plotter.set_background("white")

    label_positions = []
    legend_entries = []

    point_key = "full_points" if use_full else "sampled_points"
    planarity_key = "full_planarity" if use_full else "sampled_planarity"

    for fracture_id, fracture in enumerate(fractures, start=1):
        points = fracture.get(point_key)

        if points is None or len(points) == 0:
            continue

        display_points = points

        if len(points) > max_points:
            sample_indices = random_generator.choice(
                len(points), max_points, replace=False
            )
            display_points = points[sample_indices]

        if len(fractures) > 1:
            value = (fracture_id - 1) / (len(fractures) - 1)
        else:
            value = 0.5

        color = cmap(value)[:3]

        plotter.add_points(
            display_points,
            color=color,
            point_size=3,
        )

        label_distances = np.linalg.norm(
            display_points - display_points.mean(axis=0),
            axis=1,
        )

        for previous_position in label_positions:
            label_distances = np.minimum(
                label_distances,
                np.linalg.norm(
                    display_points - previous_position,
                    axis=1,
                ),
            )

        label_position = display_points[np.argmax(label_distances)]
        label_positions.append(label_position)

        plotter.add_point_labels(
            np.asarray([label_position]),
            [f"F{fracture_id}"],
            font_size=14,
            text_color="black",
            shape_color="white",
        )

        planarity = fracture[planarity_key]
        legend_entries.append(
            [f"F{fracture_id}  P={planarity:.4f}", color]
        )

    if rejected_points is not None and len(rejected_points):
        display_points = rejected_points

        if len(rejected_points) > max_points:
            sample_indices = random_generator.choice(
                len(rejected_points), max_points, replace=False
            )
            display_points = rejected_points[sample_indices]

        plotter.add_points(
            display_points,
            color="gray",
            point_size=2,
            opacity=0.65,
        )

        plotter.add_text(
            "Gray: rejected points",
            position="lower_left",
            font_size=11,
            color="gray",
        )

    if 0 < len(legend_entries) <= 10:
        plotter.add_legend(
            legend_entries,
            loc="upper right",
            bcolor="white",
            size=(0.23, max(0.10, 0.035 * len(legend_entries))),
        )

    plotter.add_title(
        f"{len(legend_entries)} fractures",
        font_size=22,
        color="black",
    )
    plotter.add_axes(color="black")

    plotter.show()


def plot_polygons(fractures):
    all_aperture_values = np.concatenate([
        fracture["aperture"]["values"]
        for fracture in fractures
    ])

    aperture_limits = [
        all_aperture_values.min(),
        np.percentile(all_aperture_values, 98),
    ]

    if aperture_limits[1] <= aperture_limits[0]:
        aperture_limits[1] = max(
            all_aperture_values.max(),
            aperture_limits[0] + 1e-6,
        )

    plotter = pv.Plotter(window_size=(1200, 900))
    plotter.set_background("white")

    for surface_index, fracture in enumerate(fractures):
        aperture = fracture["aperture"]

        triangulation = Delaunay(aperture["coords_2d"])

        mesh_faces = np.column_stack([
            np.full(len(triangulation.simplices), 3),
            triangulation.simplices,
        ]).ravel()

        fracture_surface = pv.PolyData(
            aperture["coords_3d"],
            mesh_faces,
        )
        fracture_surface["aperture"] = aperture["values"]

        plotter.add_mesh(
            fracture_surface,
            scalars="aperture",
            cmap="viridis",
            clim=aperture_limits,
            above_color="tomato",
            lighting=False,
            show_edges=False,
            show_scalar_bar=surface_index == 0,
            scalar_bar_args={
                "title": "Aperture",
                "color": "black",
                "fmt": "%.3g",
            },
        )

        polygon = fracture["polygon"]
        plotter.add_lines(
            np.vstack([polygon, polygon[0]]),
            connected=True,
            color="black",
            width=1,
        )

    plotter.add_title(
        "Spatial fracture aperture",
        font_size=22,
        color="black",
    )
    plotter.add_axes(color="black")

    plotter.show()