(async () => {
  "use strict";
  const datasetSelect = document.querySelector("#dataset");
  const viewSelect = document.querySelector("#visualization");
  const container = document.querySelector("#viewer");
  const frame = document.querySelector(".viewer-frame");
  const status = document.querySelector("#status");
  const labelCanvas = document.querySelector("#fracture-labels");
  const labelContext = labelCanvas.getContext("2d");
  const labels = { fractures: "Extracted fractures", aperture: "Aperture representation" };
  const catalogURL = new URL("./models/datasets.json", document.baseURI);

  function message(text, busy = false) {
    status.textContent = text;
    status.hidden = !text;
    frame.setAttribute("aria-busy", String(busy));
  }

  try {
    if (location.protocol === "file:") {
      throw new Error("Open this page through a local static preview or GitHub Pages.");
    }
    if (!window.vtk) {
      throw new Error("The 3D viewer could not load. Check your internet connection and reload.");
    }
    const vtk = window.vtk;
    const window3d = vtk.Rendering.Misc.vtkGenericRenderWindow.newInstance({
      background: [1, 1, 1], listenWindowResize: false,
    });
    window3d.setContainer(container);
    const renderer = window3d.getRenderer();
    const renderWindow = window3d.getRenderWindow();
    const observer = new ResizeObserver(() => window3d.resize());
    observer.observe(container);
    window3d.resize();
    container.addEventListener("contextmenu", (event) => event.preventDefault());
    container.querySelector("canvas").addEventListener("webglcontextlost", (event) => {
      event.preventDefault();
      message("The graphics context was lost. Reload the page to restore the viewer.");
    });

    let current = null;
    let request = 0;
    let controller;

    function addFractureLabels(dataset) {
      const annotations = dataset.labels || [];
      if (!annotations.length || !labelContext) return;
      const points = vtk.Common.DataModel.vtkPolyData.newInstance();
      points.getPoints().setData(new Float64Array(annotations.flatMap((item) => item.position)), 3);
      const mapper = vtk.Rendering.Core.vtkPixelSpaceCallbackMapper.newInstance();
      mapper.setInputData(points);
      mapper.setCallback((coordinates, camera, aspect, depth, size) => {
        const [width, height] = size;
        if (labelCanvas.width !== width) labelCanvas.width = width;
        if (labelCanvas.height !== height) labelCanvas.height = height;
        labelContext.clearRect(0, 0, width, height);
        const pixelRatio = width / Math.max(1, container.clientWidth);
        labelContext.font = `${13 * pixelRatio}px system-ui, sans-serif`;
        labelContext.textAlign = "center";
        labelContext.textBaseline = "middle";
        labelContext.lineJoin = "round";
        labelContext.lineWidth = 3 * pixelRatio;
        labelContext.strokeStyle = "white";
        labelContext.fillStyle = "#162b46";
        coordinates.forEach(([x, y, z], index) => {
          if (!Number.isFinite(x + y + z) || z < -1 || z > 1 ||
              x < 0 || x > width || y < 0 || y > height) return;
          labelContext.strokeText(annotations[index].text, x, height - y);
          labelContext.fillText(annotations[index].text, x, height - y);
        });
      });
      const actor = vtk.Rendering.Core.vtkActor.newInstance();
      actor.setMapper(mapper);
      actor.setPickable(false);
      current.annotations = { actor, mapper, points };
      renderer.addActor(actor);
    }

    function release() {
      labelContext?.clearRect(0, 0, labelCanvas.width, labelCanvas.height);
      if (!current) return;
      if (current.annotations) {
        renderer.removeActor(current.annotations.actor);
        current.annotations.actor.delete();
        current.annotations.mapper.delete();
        current.annotations.points.delete();
      }
      renderer.removeActor(current.actor);
      current.actor.delete();
      current.mapper.delete();
      current.lookup?.delete();
      current.data.delete();
      current.reader.delete();
      current = null;
    }

    async function loadView(dataset) {
      const token = ++request;
      controller?.abort();
      controller = new AbortController();
      release();
      renderWindow.render();
      const mode = viewSelect.value;
      message("Loading " + dataset.label + "…", true);
      let reader;
      try {
        const url = new URL(dataset.views[mode], catalogURL);
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error("Model request failed: " + response.status + " " + url);
        const buffer = await response.arrayBuffer();
        if (token !== request) return;
        reader = vtk.IO.XML.vtkXMLPolyDataReader.newInstance();
        reader.parseAsArrayBuffer(buffer);
        const data = reader.getOutputData(0);
        if (!data || !data.getNumberOfPoints()) throw new Error("Empty model: " + url);
        const scalars = data.getPointData().getArrayByName(mode === "aperture" ? "aperture" : "colors");
        if (!scalars) throw new Error("Missing display data: " + url);
        const mapper = vtk.Rendering.Core.vtkMapper.newInstance();
        const actor = vtk.Rendering.Core.vtkActor.newInstance();
        current = { reader, data, mapper, actor, lookup: null };
        reader = null;
        mapper.setInputData(data);
        mapper.setScalarModeToUsePointFieldData();
        mapper.setColorByArrayName(scalars.getName());
        actor.setMapper(mapper);

        if (mode === "aperture") {
          const range = data.getFieldData().getArrayByName("display_range")?.getData();
          const table = data.getFieldData().getArrayByName("display_lut");
          if (!range || range.length !== 2 || !table) throw new Error("Missing aperture color mapping.");
          const lookup = vtk.Common.Core.vtkLookupTable.newInstance();
          current.lookup = lookup;
          lookup.setTable(table);
          lookup.setMappingRange(range[0], range[1]);
          lookup.setAboveRangeColor(1, 99 / 255, 71 / 255, 1);
          lookup.setUseAboveRangeColor(true);
          mapper.setColorModeToMapScalars();
          mapper.setLookupTable(lookup);
          mapper.setScalarRange(range[0], range[1]);
          mapper.setInterpolateScalarsBeforeMapping(true);
          actor.getProperty().setLighting(false);
        } else {
          mapper.setColorModeToDirectScalars();
          actor.getProperty().setAmbient(0.45);
          actor.getProperty().setDiffuse(0.55);
          actor.getProperty().setSpecular(0);
        }
        const scale = data.getFieldData().getArrayByName("display_scale")?.getData()[0] ?? 1;
        if (!(Number.isFinite(scale) && scale > 0)) throw new Error("Invalid display scale.");
        actor.setScale(scale, scale, scale);
        renderer.addActor(actor);
        addFractureLabels(dataset);
        const camera = renderer.getActiveCamera();
        camera.setPosition(1, -1, 1);
        camera.setFocalPoint(0, 0, 0);
        camera.setViewUp(0, 0, 1);
        renderer.resetCamera();
        renderer.resetCameraClippingRange();
        renderWindow.render();
        message("");
      } catch (error) {
        reader?.delete();
        if (token !== request || error.name === "AbortError") return;
        release();
        renderWindow.render();
        console.error(error);
        message("Could not load " + dataset.label + " — " + labels[mode] + ". Choose another view or reload.");
      }
    }

    const response = await fetch(catalogURL, { cache: "no-cache" });
    if (!response.ok) throw new Error("The dataset list could not be loaded.");
    const datasets = await response.json();
    if (!Array.isArray(datasets)) throw new Error("The dataset list is invalid.");
    if (!datasets.length) { message("No publication models have been added yet."); return; }
    const ids = new Set();
    for (const dataset of datasets) {
      if (!dataset.id || !dataset.label || ids.has(dataset.id) || !dataset.views ||
          !Object.keys(labels).some((mode) => typeof dataset.views[mode] === "string")) {
        throw new Error("The dataset list contains an invalid entry.");
      }
      ids.add(dataset.id);
      datasetSelect.add(new Option(dataset.label, dataset.id));
    }
    function chooseDataset() {
      const dataset = datasets.find((item) => item.id === datasetSelect.value);
      const previousMode = viewSelect.value;
      viewSelect.replaceChildren();
      for (const [mode, label] of Object.entries(labels)) {
        if (typeof dataset.views[mode] === "string") viewSelect.add(new Option(label, mode));
      }
      if (dataset.views[previousMode]) viewSelect.value = previousMode;
      viewSelect.disabled = false;
      loadView(dataset);
    }
    datasetSelect.disabled = false;
    datasetSelect.addEventListener("change", chooseDataset);
    viewSelect.addEventListener("change", () => {
      loadView(datasets.find((item) => item.id === datasetSelect.value));
    });
    chooseDataset();
    // vtk.js renders on interaction; there is no animation loop or auto-rotation.
    window.addEventListener("pagehide", (event) => {
      if (event.persisted) return;
      request++;
      controller?.abort();
      observer.disconnect();
      release();
      window3d.delete();
    });
  } catch (error) {
    console.error(error);
    message(error.message || "The viewer could not start in this browser.");
  }
})();
