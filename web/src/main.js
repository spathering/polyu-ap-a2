import '@kitware/vtk.js/Rendering/Profiles/Geometry';
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
import vtkCellArray from '@kitware/vtk.js/Common/Core/CellArray';
import vtkCellPicker from '@kitware/vtk.js/Rendering/Core/CellPicker';
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';
import vtkGenericRenderWindow from '@kitware/vtk.js/Rendering/Misc/GenericRenderWindow';
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
import vtkPoints from '@kitware/vtk.js/Common/Core/Points';
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData';

import './style.css';

const app = document.querySelector('#app');
const container = document.querySelector('#viewer');
const slider = document.querySelector('#timeline');
const dateLabel = document.querySelector('#date-label');
const timelineDate = document.querySelector('#timeline-date');
const tooltip = document.querySelector('#tooltip');
const loading = document.querySelector('#loading');
const errorBox = document.querySelector('#error');

const state = {
  day: 0,
  selectedStation: null,
  autoplayTimer: null,
  resumeTimer: null,
  lastPickAt: 0,
};

function hexToRgb(hex) {
  const value = hex.replace('#', '');
  return [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16) / 255);
}

function colourBytes(values, range, palette) {
  const colours = palette.map((value) => hexToRgb(value).map((item) => item * 255));
  const output = new Uint8Array(values.length * 3);
  const span = range[1] - range[0];
  for (let index = 0; index < values.length; index += 1) {
    const normalised = Math.max(0, Math.min(1, (values[index] - range[0]) / span));
    const position = normalised * (colours.length - 1);
    const low = Math.min(Math.floor(position), colours.length - 2);
    const fraction = position - low;
    for (let channel = 0; channel < 3; channel += 1) {
      output[index * 3 + channel] = Math.round(
        colours[low][channel] * (1 - fraction) + colours[low + 1][channel] * fraction,
      );
    }
  }
  return output;
}

function vtkTriangles(faces) {
  const output = new Uint32Array((faces.length / 3) * 4);
  for (let source = 0, target = 0; source < faces.length; source += 3, target += 4) {
    output[target] = 3;
    output[target + 1] = faces[source];
    output[target + 2] = faces[source + 1];
    output[target + 3] = faces[source + 2];
  }
  return output;
}

function vtkVertices(count) {
  const output = new Uint32Array(count * 2);
  for (let index = 0; index < count; index += 1) {
    output[index * 2] = 1;
    output[index * 2 + 1] = index;
  }
  return output;
}

function createSurface(nodes, faces, y, values, range, palette, opacity) {
  const coordinates = new Float32Array((nodes.length / 2) * 3);
  for (let index = 0; index < nodes.length / 2; index += 1) {
    coordinates[index * 3] = nodes[index * 2];
    coordinates[index * 3 + 1] = y[index];
    coordinates[index * 3 + 2] = nodes[index * 2 + 1];
  }
  const points = vtkPoints.newInstance();
  points.setData(coordinates, 3);
  const polyData = vtkPolyData.newInstance();
  polyData.setPoints(points);
  polyData.setPolys(vtkCellArray.newInstance({ values: vtkTriangles(faces) }));

  const colours = vtkDataArray.newInstance({
    name: 'Colours',
    numberOfComponents: 3,
    values: colourBytes(values, range, palette),
  });
  polyData.getPointData().setScalars(colours);
  const mapper = vtkMapper.newInstance();
  mapper.setInputData(polyData);
  mapper.setColorModeToDirectScalars();
  mapper.setScalarModeToUsePointData();
  mapper.setScalarVisibility(true);
  const actor = vtkActor.newInstance();
  actor.setMapper(mapper);
  actor.getProperty().setOpacity(opacity);
  actor.getProperty().setAmbient(0.32);
  actor.getProperty().setDiffuse(0.72);
  actor.getProperty().setSpecular(0.1);
  return { polyData, points, coordinates, colours, actor };
}

function createSolidMesh(nodes, faces, y, colour, opacity) {
  const coordinates = new Float32Array((nodes.length / 2) * 3);
  for (let index = 0; index < nodes.length / 2; index += 1) {
    coordinates[index * 3] = nodes[index * 2];
    coordinates[index * 3 + 1] = y;
    coordinates[index * 3 + 2] = nodes[index * 2 + 1];
  }
  const points = vtkPoints.newInstance();
  points.setData(coordinates, 3);
  const polyData = vtkPolyData.newInstance();
  polyData.setPoints(points);
  polyData.setPolys(vtkCellArray.newInstance({ values: vtkTriangles(faces) }));
  const mapper = vtkMapper.newInstance();
  mapper.setInputData(polyData);
  const actor = vtkActor.newInstance();
  actor.setMapper(mapper);
  actor.getProperty().setColor(...hexToRgb(colour));
  actor.getProperty().setOpacity(opacity);
  actor.getProperty().setAmbient(1);
  actor.getProperty().setDiffuse(0);
  return { polyData, actor };
}

function createLines(lines, colour, opacity = 0.72, width = 1.2) {
  const coordinates = [];
  const cells = [];
  let cursor = 0;
  lines.forEach((line) => {
    cells.push(line.length);
    line.forEach(([x, z]) => {
      coordinates.push(x, 24, z);
      cells.push(cursor);
      cursor += 1;
    });
  });
  const points = vtkPoints.newInstance();
  points.setData(Float32Array.from(coordinates), 3);
  const polyData = vtkPolyData.newInstance();
  polyData.setPoints(points);
  polyData.setLines(vtkCellArray.newInstance({ values: Uint32Array.from(cells) }));
  const mapper = vtkMapper.newInstance();
  mapper.setInputData(polyData);
  const actor = vtkActor.newInstance();
  actor.setMapper(mapper);
  actor.getProperty().setColor(...hexToRgb(colour));
  actor.getProperty().setOpacity(opacity);
  actor.getProperty().setLineWidth(width);
  return { polyData, actor };
}

function createStationActors(stations) {
  const count = stations.length;
  const linkCoordinates = new Float32Array(count * 9);
  const lineCells = new Uint32Array(count * 4);
  const endpointCoordinates = new Float32Array(count * 6);
  for (let index = 0; index < count; index += 1) {
    const base = index * 3;
    lineCells[index * 4] = 3;
    lineCells[index * 4 + 1] = base;
    lineCells[index * 4 + 2] = base + 1;
    lineCells[index * 4 + 3] = base + 2;
  }

  const linkPoints = vtkPoints.newInstance();
  linkPoints.setData(linkCoordinates, 3);
  const linkData = vtkPolyData.newInstance();
  linkData.setPoints(linkPoints);
  linkData.setLines(vtkCellArray.newInstance({ values: lineCells }));
  const linkMapper = vtkMapper.newInstance();
  linkMapper.setInputData(linkData);
  const linkActor = vtkActor.newInstance();
  linkActor.setMapper(linkMapper);
  linkActor.getProperty().setColor(0.96, 0.99, 1.0);
  linkActor.getProperty().setOpacity(0.62);
  linkActor.getProperty().setLineWidth(1.3);

  const endpointPoints = vtkPoints.newInstance();
  endpointPoints.setData(endpointCoordinates, 3);
  const endpointData = vtkPolyData.newInstance();
  endpointData.setPoints(endpointPoints);
  endpointData.setVerts(vtkCellArray.newInstance({ values: vtkVertices(count * 2) }));
  const endpointMapper = vtkMapper.newInstance();
  endpointMapper.setInputData(endpointData);
  const endpointActor = vtkActor.newInstance();
  endpointActor.setMapper(endpointMapper);
  endpointActor.getProperty().setColor(0.96, 0.99, 1.0);
  endpointActor.getProperty().setPointSize(7);

  const highlightCoordinates = new Float32Array(9);
  const highlightPoints = vtkPoints.newInstance();
  highlightPoints.setData(highlightCoordinates, 3);
  const highlightData = vtkPolyData.newInstance();
  highlightData.setPoints(highlightPoints);
  highlightData.setLines(vtkCellArray.newInstance({ values: Uint32Array.from([3, 0, 1, 2]) }));
  const highlightMapper = vtkMapper.newInstance();
  highlightMapper.setInputData(highlightData);
  const highlightActor = vtkActor.newInstance();
  highlightActor.setMapper(highlightMapper);
  highlightActor.getProperty().setColor(...hexToRgb('#ffe36b'));
  highlightActor.getProperty().setLineWidth(4);
  highlightActor.setVisibility(false);

  const highlightEndpointCoordinates = new Float32Array(6);
  const highlightEndpointPoints = vtkPoints.newInstance();
  highlightEndpointPoints.setData(highlightEndpointCoordinates, 3);
  const highlightEndpointData = vtkPolyData.newInstance();
  highlightEndpointData.setPoints(highlightEndpointPoints);
  highlightEndpointData.setVerts(vtkCellArray.newInstance({ values: vtkVertices(2) }));
  const highlightEndpointMapper = vtkMapper.newInstance();
  highlightEndpointMapper.setInputData(highlightEndpointData);
  const highlightEndpointActor = vtkActor.newInstance();
  highlightEndpointActor.setMapper(highlightEndpointMapper);
  highlightEndpointActor.getProperty().setColor(...hexToRgb('#ffe36b'));
  highlightEndpointActor.getProperty().setPointSize(14);
  highlightEndpointActor.setVisibility(false);

  return {
    linkCoordinates,
    linkPoints,
    linkData,
    linkActor,
    endpointCoordinates,
    endpointPoints,
    endpointData,
    endpointActor,
    highlightCoordinates,
    highlightPoints,
    highlightData,
    highlightActor,
    highlightEndpointCoordinates,
    highlightEndpointPoints,
    highlightEndpointData,
    highlightEndpointActor,
  };
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Unable to load ${path}: ${response.status}`);
  return response.json();
}

async function loadBuffer(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Unable to load ${path}: ${response.status}`);
  return response.arrayBuffer();
}

function formatDate(iso) {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(`${iso}T00:00:00Z`)).toUpperCase();
}

function clampCamera(camera, pitchRange) {
  const position = camera.getPosition();
  const focal = camera.getFocalPoint();
  const offset = position.map((value, index) => value - focal[index]);
  const horizontal = Math.hypot(offset[0], offset[2]);
  const distance = Math.hypot(offset[0], offset[1], offset[2]);
  if (!distance || !horizontal) return;
  const pitch = Math.atan2(offset[1], horizontal) * 180 / Math.PI;
  const clamped = Math.max(pitchRange[0], Math.min(pitchRange[1], pitch));
  if (Math.abs(clamped - pitch) < 0.05) return;
  const angle = clamped * Math.PI / 180;
  const horizontalScale = distance * Math.cos(angle) / horizontal;
  camera.setPosition(
    focal[0] + offset[0] * horizontalScale,
    focal[1] + distance * Math.sin(angle),
    focal[2] + offset[2] * horizontalScale,
  );
  camera.setViewUp(0, 1, 0);
}

async function start() {
  const manifest = await loadJson('./data/manifest.json');
  const [topologyBuffer, temperatureYBuffer, temperatureValueBuffer, rainfallYBuffer,
    rainfallValueBuffer, stations, districtLines] = await Promise.all([
    loadBuffer(`./data/${manifest.topology.path}`),
    loadBuffer(`./data/${manifest.temperature.yFile}`),
    loadBuffer(`./data/${manifest.temperature.valueFile}`),
    loadBuffer(`./data/${manifest.rainfall.yFile}`),
    loadBuffer(`./data/${manifest.rainfall.valueFile}`),
    loadJson(`./data/${manifest.stationsFile}`),
    loadJson(`./data/${manifest.base.districtFile}`),
  ]);

  const nodeCount = manifest.nodeCount;
  const topology = manifest.topology;
  const nodes = new Float32Array(
    topologyBuffer,
    topology.nodes.offset,
    topology.nodes.shape[0] * topology.nodes.shape[1],
  );
  const faces = new Uint32Array(
    topologyBuffer,
    topology.faces.offset,
    topology.faces.shape[0] * topology.faces.shape[1],
  );
  const temperatureY = new Float32Array(temperatureYBuffer);
  const temperatureValues = new Float32Array(temperatureValueBuffer);
  const rainfallY = new Float32Array(rainfallYBuffer);
  const rainfallValues = new Float32Array(rainfallValueBuffer);

  const generic = vtkGenericRenderWindow.newInstance({ background: [0.027, 0.082, 0.106] });
  generic.setContainer(container);
  generic.resize();
  const renderer = generic.getRenderer();
  const renderWindow = generic.getRenderWindow();

  const temp = createSurface(
    nodes, faces, temperatureY.subarray(0, nodeCount),
    temperatureValues.subarray(0, nodeCount), manifest.temperature.range,
    manifest.temperature.colours, manifest.surfaceOpacity.temperature,
  );
  const rain = createSurface(
    nodes, faces, rainfallY.subarray(0, nodeCount),
    rainfallValues.subarray(0, nodeCount), manifest.rainfall.range,
    manifest.rainfall.colours, manifest.surfaceOpacity.rainfall,
  );
  const land = createSolidMesh(nodes, faces, 0, manifest.base.landColour, manifest.base.landOpacity);
  const seaNodes = Float32Array.from(manifest.seaCorners.flat());
  const seaFaces = Uint32Array.from([0, 1, 2, 0, 2, 3]);
  const sea = createSolidMesh(seaNodes, seaFaces, 0, manifest.base.seaColour, manifest.base.seaOpacity);
  const districts = createLines(districtLines, '#5e7479');
  const stationActors = createStationActors(stations);

  renderer.addActor(sea.actor);
  renderer.addActor(rain.actor);
  renderer.addActor(land.actor);
  renderer.addActor(districts.actor);
  renderer.addActor(temp.actor);
  renderer.addActor(stationActors.linkActor);
  renderer.addActor(stationActors.endpointActor);
  renderer.addActor(stationActors.highlightActor);
  renderer.addActor(stationActors.highlightEndpointActor);

  function updateStations(day) {
    stations.forEach((station, index) => {
      const base = index * 9;
      const upperY = temperatureY[day * nodeCount + station.node];
      const lowerY = rainfallY[day * nodeCount + station.node];
      stationActors.linkCoordinates.set(
        [station.x, upperY, station.z, station.x, 0, station.z, station.x, lowerY, station.z],
        base,
      );
      stationActors.endpointCoordinates.set(
        [station.x, upperY, station.z, station.x, lowerY, station.z],
        index * 6,
      );
    });
    stationActors.linkPoints.setData(stationActors.linkCoordinates, 3);
    stationActors.linkPoints.modified();
    stationActors.linkData.modified();
    stationActors.endpointPoints.setData(stationActors.endpointCoordinates, 3);
    stationActors.endpointPoints.modified();
    stationActors.endpointData.modified();
  }

  function updateHighlight() {
    if (state.selectedStation === null) {
      stationActors.highlightActor.setVisibility(false);
      stationActors.highlightEndpointActor.setVisibility(false);
      return;
    }
    const source = state.selectedStation * 9;
    stationActors.highlightCoordinates.set(
      stationActors.linkCoordinates.subarray(source, source + 9),
    );
    stationActors.highlightEndpointCoordinates.set([
      ...stationActors.highlightCoordinates.subarray(0, 3),
      ...stationActors.highlightCoordinates.subarray(6, 9),
    ]);
    stationActors.highlightPoints.setData(stationActors.highlightCoordinates, 3);
    stationActors.highlightPoints.modified();
    stationActors.highlightData.modified();
    stationActors.highlightEndpointPoints.setData(stationActors.highlightEndpointCoordinates, 3);
    stationActors.highlightEndpointPoints.modified();
    stationActors.highlightEndpointData.modified();
    stationActors.highlightActor.setVisibility(true);
    stationActors.highlightEndpointActor.setVisibility(true);
  }

  function updateSurface(surface, yValues, sourceValues, range, palette, day) {
    const offset = day * nodeCount;
    const y = yValues.subarray(offset, offset + nodeCount);
    const values = sourceValues.subarray(offset, offset + nodeCount);
    for (let index = 0; index < nodeCount; index += 1) {
      surface.coordinates[index * 3 + 1] = y[index];
    }
    surface.points.setData(surface.coordinates, 3);
    surface.points.modified();
    surface.colours.setData(colourBytes(values, range, palette), 3);
    surface.colours.modified();
    surface.polyData.modified();
  }

  function tooltipHtml(index) {
    const station = stations[index];
    const rain = station.trace[state.day]
      ? 'Trace (&lt;0.05 mm)'
      : `${station.rainfall[state.day].toFixed(1)} mm`;
    return `<strong>${station.name} (${station.code})</strong><br>${formatDate(manifest.dates[state.day])}`
      + `<br>Mean temperature&nbsp; ${station.temperature[state.day].toFixed(1)} °C`
      + `<br>Total rainfall&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${rain}`;
  }

  function applyDay(day) {
    state.day = (Number(day) + manifest.dates.length) % manifest.dates.length;
    updateSurface(temp, temperatureY, temperatureValues, manifest.temperature.range,
      manifest.temperature.colours, state.day);
    updateSurface(rain, rainfallY, rainfallValues, manifest.rainfall.range,
      manifest.rainfall.colours, state.day);
    updateStations(state.day);
    updateHighlight();
    slider.value = String(state.day);
    const label = formatDate(manifest.dates[state.day]);
    dateLabel.textContent = label;
    timelineDate.textContent = label;
    if (state.selectedStation !== null) tooltip.innerHTML = tooltipHtml(state.selectedStation);
    renderer.resetCameraClippingRange();
    renderWindow.render();
  }

  function stopAutoplay() {
    if (state.autoplayTimer) clearInterval(state.autoplayTimer);
    state.autoplayTimer = null;
    if (state.resumeTimer) clearTimeout(state.resumeTimer);
    state.resumeTimer = null;
  }

  function startAutoplay() {
    stopAutoplay();
    state.autoplayTimer = setInterval(
      () => applyDay((state.day + 1) % manifest.dates.length),
      manifest.timeline.intervalMs,
    );
  }

  slider.max = String(manifest.dates.length - 1);
  slider.addEventListener('input', (event) => {
    stopAutoplay();
    applyDay(Number(event.target.value));
  });
  slider.addEventListener('change', () => {
    state.resumeTimer = setTimeout(startAutoplay, manifest.timeline.resumeDelayMs);
  });

  const camera = renderer.getActiveCamera();
  const distance = manifest.horizontalSpan * manifest.camera.distanceFactor;
  const pitch = manifest.camera.initialPitch * Math.PI / 180;
  const horizontal = distance * Math.cos(pitch);
  const diagonal = horizontal / Math.sqrt(2);
  camera.setFocalPoint(0, 0, 0);
  camera.setPosition(-diagonal, distance * Math.sin(pitch), -diagonal);
  camera.setViewUp(0, 1, 0);
  renderer.resetCameraClippingRange();

  const picker = vtkCellPicker.newInstance();
  picker.setPickFromList(true);
  picker.initializePickList();
  picker.addPickList(land.actor);
  picker.addPickList(sea.actor);

  function clearSelection() {
    state.selectedStation = null;
    tooltip.hidden = true;
    updateHighlight();
    renderWindow.render();
  }

  function pickStation(event) {
    const now = performance.now();
    if (now - state.lastPickAt < 32) return;
    state.lastPickAt = now;
    const canvas = container.querySelector('canvas');
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * canvas.width / rect.width;
    const y = (rect.bottom - event.clientY) * canvas.height / rect.height;
    picker.pick([x, y, 0], renderer);
    const actors = picker.getActors();
    if (!actors.length) {
      clearSelection();
      return;
    }
    const position = picker.getPickPosition();
    let nearest = 0;
    let distanceSquared = Number.POSITIVE_INFINITY;
    stations.forEach((station, index) => {
      const value = (station.x - position[0]) ** 2 + (station.z - position[2]) ** 2;
      if (value < distanceSquared) {
        nearest = index;
        distanceSquared = value;
      }
    });
    state.selectedStation = nearest;
    updateHighlight();
    tooltip.innerHTML = tooltipHtml(nearest);
    tooltip.hidden = false;
    const left = Math.min(event.clientX + 16, window.innerWidth - 310);
    const top = Math.min(event.clientY + 16, window.innerHeight - 130);
    tooltip.style.left = `${Math.max(8, left)}px`;
    tooltip.style.top = `${Math.max(8, top)}px`;
    renderWindow.render();
  }

  container.addEventListener('pointermove', pickStation);
  container.addEventListener('pointerleave', clearSelection);
  container.addEventListener('pointerup', () => {
    clampCamera(camera, manifest.camera.pitchRange);
    renderer.resetCameraClippingRange();
    renderWindow.render();
  });
  container.addEventListener('wheel', () => {
    requestAnimationFrame(() => {
      clampCamera(camera, manifest.camera.pitchRange);
      renderer.resetCameraClippingRange();
      renderWindow.render();
    });
  }, { passive: true });

  window.addEventListener('resize', () => {
    generic.resize();
    renderWindow.render();
  });

  applyDay(0);
  startAutoplay();
  loading.hidden = true;
  app.setAttribute('aria-busy', 'false');
}

start().catch((error) => {
  console.error(error);
  loading.hidden = true;
  errorBox.hidden = false;
  errorBox.textContent = `Unable to start the visualisation.\n${error.message}`;
  app.setAttribute('aria-busy', 'false');
});
