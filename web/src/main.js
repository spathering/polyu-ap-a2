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
const timelineSummary = document.querySelector('#timeline-summary');
const tooltip = document.querySelector('#tooltip');
const autoplayToggle = document.querySelector('#autoplay');
const playbackSpeed = document.querySelector('#playback-speed');
const playbackSpeedValue = document.querySelector('#playback-speed-value');
const loading = document.querySelector('#loading');
const errorBox = document.querySelector('#error');

const state = {
  position: 0,
  playPosition: 0,
  selectedStation: null,
  scrubbing: false,
  lastAnimationAt: null,
  lastPickAt: 0,
};

function hexToRgb(hex) {
  const value = hex.replace('#', '');
  return [0, 2, 4].map((index) => parseInt(value.slice(index, index + 2), 16) / 255);
}

function colourBytes(values, range, palette, baseline, fadeWidth, maxOpacity) {
  const colours = palette.map((value) => hexToRgb(value).map((item) => item * 255));
  const output = new Uint8Array(values.length * 4);
  const span = range[1] - range[0];
  for (let index = 0; index < values.length; index += 1) {
    const normalised = Math.max(0, Math.min(1, (values[index] - range[0]) / span));
    const position = normalised * (colours.length - 1);
    const low = Math.min(Math.floor(position), colours.length - 2);
    const fraction = position - low;
    for (let channel = 0; channel < 3; channel += 1) {
      output[index * 4 + channel] = Math.round(
        colours[low][channel] * (1 - fraction) + colours[low + 1][channel] * fraction,
      );
    }
    const distance = Math.max(0, Math.min(1, Math.abs(values[index] - baseline) / fadeWidth));
    const smooth = distance * distance * (3 - 2 * distance);
    output[index * 4 + 3] = Math.round(255 * maxOpacity * smooth);
  }
  return output;
}

function applyDepthFog(mapper, fog) {
  const colour = hexToRgb(fog.colour);
  mapper.setViewSpecificProperties({
    OpenGL: {
      ShaderReplacements: [{
        shaderType: 'Fragment',
        originalValue: '//VTK::RenderPassFragmentShader::Impl',
        replacementValue: `
          float weatherFog = smoothstep(${fog.start}, ${fog.end}, gl_FragCoord.z);
          weatherFog = clamp(weatherFog * ${fog.strength}, 0.0, 1.0);
          gl_FragData[0].rgb = mix(gl_FragData[0].rgb, vec3(${colour.join(',')}), weatherFog);
          //VTK::RenderPassFragmentShader::Impl
        `,
        replaceFirst: false,
        replaceAll: false,
      }],
    },
  });
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

function createSurface(nodes, faces, y, values, settings, opacity) {
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
    numberOfComponents: 4,
    values: colourBytes(
      values, settings.range, settings.colours,
      settings.baseline, settings.fadeWidth, opacity,
    ),
  });
  polyData.getPointData().setScalars(colours);
  const mapper = vtkMapper.newInstance();
  mapper.setInputData(polyData);
  mapper.setColorModeToDirectScalars();
  mapper.setScalarModeToUsePointData();
  mapper.setScalarVisibility(true);
  const actor = vtkActor.newInstance();
  actor.setMapper(mapper);
  actor.getProperty().setOpacity(1);
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

function createGrid(corners, settings) {
  const xs = corners.map(([x]) => x);
  const zs = corners.map(([, z]) => z);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minZ = Math.min(...zs);
  const maxZ = Math.max(...zs);
  const centreX = (minX + maxX) / 2;
  const centreZ = (minZ + maxZ) / 2;
  const halfX = Math.max((maxX - minX) / 2, 1);
  const halfZ = Math.max((maxZ - minZ) / 2, 1);
  const values = Array.from(
    { length: settings.divisions + 1 },
    (_, index) => index / settings.divisions,
  );

  function layer(major) {
    const coordinates = [];
    const cells = [];
    const colours = [];
    let cursor = 0;
    const rgb = major ? [128, 164, 172] : [88, 122, 130];
    const opacity = major ? settings.majorOpacity : settings.minorOpacity;

    function addLine(samples) {
      cells.push(samples.length);
      samples.forEach(([x, z]) => {
        coordinates.push(x, 0, z);
        cells.push(cursor);
        cursor += 1;
        const radius = Math.min(1, Math.hypot((x - centreX) / halfX, (z - centreZ) / halfZ));
        const position = Math.max(0, Math.min(
          1, (radius - settings.fadeStart) / (1 - settings.fadeStart),
        ));
        const fade = 1 - position * position * (3 - 2 * position);
        colours.push(...rgb, Math.round(255 * opacity * fade));
      });
    }

    values.forEach((fraction, index) => {
      if ((index % settings.majorEvery === 0) === major) {
        const x = minX + fraction * (maxX - minX);
        addLine(values.map((value) => [x, minZ + value * (maxZ - minZ)]));
      }
    });
    values.forEach((fraction, index) => {
      if ((index % settings.majorEvery === 0) === major) {
        const z = minZ + fraction * (maxZ - minZ);
        addLine(values.map((value) => [minX + value * (maxX - minX), z]));
      }
    });

    const points = vtkPoints.newInstance();
    points.setData(Float32Array.from(coordinates), 3);
    const polyData = vtkPolyData.newInstance();
    polyData.setPoints(points);
    polyData.setLines(vtkCellArray.newInstance({ values: Uint32Array.from(cells) }));
    polyData.getPointData().setScalars(vtkDataArray.newInstance({
      name: 'Grid colours',
      numberOfComponents: 4,
      values: Uint8Array.from(colours),
    }));
    const mapper = vtkMapper.newInstance();
    mapper.setInputData(polyData);
    mapper.setColorModeToDirectScalars();
    mapper.setScalarModeToUsePointData();
    mapper.setScalarVisibility(true);
    const actor = vtkActor.newInstance();
    actor.setMapper(mapper);
    actor.getProperty().setOpacity(1);
    actor.getProperty().setAmbient(1);
    actor.getProperty().setDiffuse(0);
    actor.getProperty().setLineWidth(major ? 1.8 : 1.0);
    return { polyData, actor };
  }

  return { minor: layer(false), major: layer(true) };
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
    temperatureValues.subarray(0, nodeCount), manifest.temperature,
    manifest.surfaceOpacity.temperature,
  );
  const rain = createSurface(
    nodes, faces, rainfallY.subarray(0, nodeCount),
    rainfallValues.subarray(0, nodeCount), manifest.rainfall,
    manifest.surfaceOpacity.rainfall,
  );
  const land = createSolidMesh(nodes, faces, 0, manifest.base.landColour, manifest.base.landOpacity);
  const seaNodes = Float32Array.from(manifest.seaCorners.flat());
  const seaFaces = Uint32Array.from([0, 1, 2, 0, 2, 3]);
  const pickPlane = createSolidMesh(seaNodes, seaFaces, 0, manifest.base.seaColour, 0);
  const grid = createGrid(manifest.seaCorners, manifest.grid);
  const districts = createLines(districtLines, '#5e7479');
  const stationActors = createStationActors(stations);

  [
    temp.actor, rain.actor, land.actor, grid.minor.actor, grid.major.actor, districts.actor,
    stationActors.linkActor, stationActors.endpointActor,
    stationActors.highlightActor, stationActors.highlightEndpointActor,
  ].forEach((actor) => applyDepthFog(actor.getMapper(), manifest.depthFog));

  renderer.addActor(pickPlane.actor);
  renderer.addActor(rain.actor);
  renderer.addActor(land.actor);
  renderer.addActor(grid.minor.actor);
  renderer.addActor(grid.major.actor);
  renderer.addActor(districts.actor);
  renderer.addActor(temp.actor);
  renderer.addActor(stationActors.linkActor);
  renderer.addActor(stationActors.endpointActor);
  renderer.addActor(stationActors.highlightActor);
  renderer.addActor(stationActors.highlightEndpointActor);

  function frameBlend(position) {
    const lower = Math.floor(position);
    const upper = Math.min(lower + 1, manifest.dates.length - 1);
    return { lower, upper, fraction: position - lower };
  }

  function blendedValue(values, node, blend) {
    const first = values[blend.lower * nodeCount + node];
    const second = values[blend.upper * nodeCount + node];
    return first * (1 - blend.fraction) + second * blend.fraction;
  }

  function formatDate(position) {
    const moment = new Date(`${manifest.dates[0]}T00:00:00Z`);
    moment.setTime(moment.getTime() + position * 86400000);
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      timeZone: 'UTC',
    }).format(moment).toUpperCase();
  }

  function stationSummary(position) {
    const blend = frameBlend(position);
    let rainfallTotal = 0;
    let temperatureTotal = 0;
    stations.forEach((station) => {
      rainfallTotal += station.rainfall[blend.lower] * (1 - blend.fraction)
        + station.rainfall[blend.upper] * blend.fraction;
      temperatureTotal += station.temperature[blend.lower] * (1 - blend.fraction)
        + station.temperature[blend.upper] * blend.fraction;
    });
    return {
      rainfallTotal,
      meanTemperature: temperatureTotal / stations.length,
    };
  }

  function formatTimelineSummary(position) {
    const summary = stationSummary(position);
    return `${formatDate(position)} · HK TOTAL RAINFALL ${summary.rainfallTotal.toFixed(1)} MM`
      + ` · HK MEAN TEMP ${summary.meanTemperature.toFixed(1)} °C`;
  }

  function updateStations(position) {
    const blend = frameBlend(position);
    stations.forEach((station, index) => {
      const base = index * 9;
      const upperY = blendedValue(rainfallY, station.node, blend);
      const lowerY = blendedValue(temperatureY, station.node, blend);
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

  function updateSurface(surface, yValues, sourceValues, settings, opacity, position) {
    const blend = frameBlend(position);
    const values = new Float32Array(nodeCount);
    for (let index = 0; index < nodeCount; index += 1) {
      surface.coordinates[index * 3 + 1] = blendedValue(yValues, index, blend);
      values[index] = blendedValue(sourceValues, index, blend);
    }
    surface.points.setData(surface.coordinates, 3);
    surface.points.modified();
    surface.colours.setData(colourBytes(
      values, settings.range, settings.colours,
      settings.baseline, settings.fadeWidth, opacity,
    ), 4);
    surface.colours.modified();
    surface.polyData.modified();
  }

  function tooltipHtml(index) {
    const station = stations[index];
    const blend = frameBlend(state.position);
    const temperature = station.temperature[blend.lower] * (1 - blend.fraction)
      + station.temperature[blend.upper] * blend.fraction;
    const rainfall = station.rainfall[blend.lower] * (1 - blend.fraction)
      + station.rainfall[blend.upper] * blend.fraction;
    const isExactTrace = blend.fraction < 1e-6 && station.trace[blend.lower];
    const rain = isExactTrace
      ? 'Trace (&lt;0.05 mm)'
      : `${rainfall.toFixed(1)} mm`;
    return `<strong>${station.name} (${station.code})</strong><br>${formatDate(state.position)}`
      + `<br>Mean temperature&nbsp; ${temperature.toFixed(1)} °C`
      + `<br>Total rainfall&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ${rain}`;
  }

  function applyPosition(position) {
    state.position = Math.max(0, Math.min(manifest.dates.length - 1, Number(position)));
    updateSurface(temp, temperatureY, temperatureValues, manifest.temperature,
      manifest.surfaceOpacity.temperature, state.position);
    updateSurface(rain, rainfallY, rainfallValues, manifest.rainfall,
      manifest.surfaceOpacity.rainfall, state.position);
    updateStations(state.position);
    updateHighlight();
    slider.value = String(state.position);
    dateLabel.textContent = formatDate(state.position);
    timelineSummary.textContent = formatTimelineSummary(state.position);
    if (state.selectedStation !== null) tooltip.innerHTML = tooltipHtml(state.selectedStation);
    renderer.resetCameraClippingRange();
    renderWindow.render();
  }

  slider.max = String(manifest.dates.length - 1);
  slider.addEventListener('input', (event) => {
    state.playPosition = Number(event.target.value);
    applyPosition(state.playPosition);
  });
  slider.addEventListener('pointerdown', () => { state.scrubbing = true; });
  slider.addEventListener('pointerup', () => {
    state.scrubbing = false;
    state.lastAnimationAt = performance.now();
  });
  slider.addEventListener('change', () => { state.scrubbing = false; });
  autoplayToggle.addEventListener('change', () => {
    state.lastAnimationAt = performance.now();
  });
  playbackSpeed.addEventListener('input', () => {
    const speed = Number(playbackSpeed.value);
    playbackSpeedValue.value = `${Number.isInteger(speed) ? speed.toFixed(0) : speed.toFixed(2)}×`;
    state.lastAnimationAt = performance.now();
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
  picker.addPickList(pickPlane.actor);

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
    const tooltipRect = tooltip.getBoundingClientRect();
    const railRect = document.querySelector('.right-rail').getBoundingClientRect();
    const timelineRect = document.querySelector('.timeline-shell').getBoundingClientRect();
    let left = event.clientX + 16;
    let top = event.clientY + 16;
    if (left + tooltipRect.width + 8 > railRect.left && event.clientY < railRect.bottom + 8) {
      left = event.clientX - tooltipRect.width - 16;
    }
    if (top + tooltipRect.height + 8 > timelineRect.top) {
      top = event.clientY - tooltipRect.height - 16;
    }
    left = Math.min(left, window.innerWidth - tooltipRect.width - 8);
    top = Math.min(top, window.innerHeight - tooltipRect.height - 8);
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

  function animate(timestamp) {
    if (state.lastAnimationAt === null) state.lastAnimationAt = timestamp;
    const elapsed = Math.min(timestamp - state.lastAnimationAt, manifest.timeline.intervalMs);
    state.lastAnimationAt = timestamp;
    if (autoplayToggle.checked && !state.scrubbing) {
      state.playPosition += (elapsed / manifest.timeline.intervalMs) * Number(playbackSpeed.value);
      if (state.playPosition >= manifest.dates.length) {
        state.playPosition %= manifest.dates.length;
      }
      applyPosition(Math.min(state.playPosition, manifest.dates.length - 1));
    }
    requestAnimationFrame(animate);
  }

  applyPosition(0);
  requestAnimationFrame(animate);
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
