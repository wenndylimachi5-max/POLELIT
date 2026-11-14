var meta = null;
var sitiosData = {};
var sitioActualId = null;
var horaActual = 0;
var reproduciendo = false;
var timerPlay = null;

// 1. Botones Educator view / Technical view
document.querySelectorAll(".mode button[data-mode]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var modo = btn.dataset.mode;
    document.body.dataset.mode = modo;
    document.querySelectorAll(".mode button[data-mode]").forEach(function (b) {
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    renderTodo();
  });
});

// 2. Cargar sitios.json y los 4 archivos individuales
fetch("data/sitios.json")
  .then(function (r) { return r.json(); })
  .then(function (data) {
    meta = data;
    var cont = document.getElementById("site-buttons");
    if (cont) {
      cont.innerHTML = "";
      data.sitios.forEach(function (s) {
        var b = document.createElement("button");
        b.type = "button";
        b.dataset.id = s.id;
        b.textContent = s.nombre_en;
        b.addEventListener("click", function () { seleccionarSitio(s.id); });
        cont.appendChild(b);
      });
    }
    return Promise.all(
      data.sitios.map(function (s) {
        return fetch("data/" + s.id + ".json")
          .then(function (r) { return r.json(); })
          .then(function (det) { sitiosData[s.id] = det; });
      })
    );
  })
  .then(function () {
    construirTablaComparativa();
    seleccionarSitio(meta.sitios[0].id);
  });

function seleccionarSitio(id) {
  sitioActualId = id;
  document.querySelectorAll("#site-buttons button").forEach(function (b) {
    b.classList.toggle("active", b.dataset.id === id);
  });
  renderTodo();
}

// 3. Barra de tiempo (8760 horas) y botón Play
var slider = document.getElementById("slider");
var btnPlay = document.getElementById("play");
slider.max = 8759;

slider.addEventListener("input", function () {
  horaActual = Number(slider.value);
  renderHora();
});

btnPlay.addEventListener("click", function () {
  reproduciendo = !reproduciendo;
  btnPlay.textContent = reproduciendo ? "Pause" : "Play";
  if (reproduciendo) {
    timerPlay = setInterval(function () {
      horaActual = (horaActual + 1) % (meta ? meta.horas : 8760);
      slider.value = horaActual;
      renderHora();
    }, 60);
  } else {
    clearInterval(timerPlay);
  }
});

var stripsCanvas = document.getElementById("strips");
stripsCanvas.addEventListener("click", function (e) {
  var rect = stripsCanvas.getBoundingClientRect();
  var ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  horaActual = Math.floor(ratio * ((meta ? meta.horas : 8760) - 1));
  slider.value = horaActual;
  renderHora();
});

function renderTodo() {
  if (!sitioActualId || !sitiosData[sitioActualId]) return;
  renderFacts();
  dibujarFranjasAnuales();
  renderHora();
}

function renderHora() {
  if (!sitioActualId || !sitiosData[sitioActualId]) return;
  var det = sitiosData[sitioActualId];
  var h = horaActual;

  var fecha = new Date(Date.UTC(meta.anio || 2027, 0, 1, h, 0, 0));
  document.getElementById("when").textContent =
    fecha.toISOString().replace("T", " ").slice(0, 16) + " UTC";

  var solFrac = det.sol.frac[h];
  var tierraVis = det.tierra.visible[h];

  var solCuenta = solFrac > 0
    ? "Sunset in " + det.sol.hasta_puesta[h] + " h"
    : "Sunrise in " + det.sol.hasta_salida[h] + " h";

  var tierraCuenta = tierraVis
    ? "Earth hides in " + det.tierra.hasta_puesta[h] + " h"
    : "Earth appears in " + det.tierra.hasta_salida[h] + " h";

  document.getElementById("r-edu").textContent =
    (solFrac > 0 ? "Sun is up (" + Math.round(solFrac * 100) + "%)" : "In shadow") +
    " · " + (tierraVis ? "Earth in view" : "No Earth signal") +
    " · " + solCuenta + " · " + tierraCuenta;

  document.getElementById("r-tech").textContent =
    "Sun el: " + det.sol.el[h].toFixed(2) + "° (frac: " + solFrac.toFixed(2) + ") · " +
    "Earth: " + (tierraVis ? "Yes" : "No") + " (el: " + det.tierra.el[h].toFixed(2) + "°) · " +
    solCuenta + " · " + tierraCuenta;

  dibujarHorizonte(det, h);
}

// 4. Vista desde el módulo (#sky)
function dibujarHorizonte(det, h) {
  var c = document.getElementById("sky");
  if (!c.width) { c.width = 860; c.height = 220; }
  var ctx = c.getContext("2d");
  var W = c.width, H = c.height;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "#090d16";
  ctx.fillRect(0, 0, W, H);

  var minEl = -10, maxEl = 25;
  function yDeEl(el) {
    return H - ((el - minEl) / (maxEl - minEl)) * H;
  }

  // Sol
  var sx = (det.sol.az[h] / 360) * W;
  var sy = yDeEl(det.sol.el[h]);
  ctx.fillStyle = det.sol.frac[h] > 0 ? "#fde047" : "rgba(253,224,71,0.25)";
  ctx.beginPath(); ctx.arc(sx, sy, 10, 0, Math.PI * 2); ctx.fill();

  // Tierra
  var ex = (det.tierra.az[h] / 360) * W;
  var ey = yDeEl(det.tierra.el[h]);
  ctx.fillStyle = det.tierra.visible[h] ? "#38bdf8" : "rgba(56,189,248,0.25)";
  ctx.beginPath(); ctx.arc(ex, ey, 7, 0, Math.PI * 2); ctx.fill();

  // Horizonte 360°
  var hor = det.horizonte;
  ctx.fillStyle = "#334155";
  ctx.strokeStyle = "#94a3b8";
  ctx.beginPath();
  ctx.moveTo(0, H);
  for (var i = 0; i < hor.length; i++) {
    ctx.lineTo((i / (hor.length - 1)) * W, yDeEl(hor[i]));
  }
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
}

// 5. Franjas anuales (#strips)
function dibujarFranjasAnuales() {
  var c = document.getElementById("strips");
  if (!c.width) { c.width = 860; c.height = 80; }
  var ctx = c.getContext("2d");
  var W = c.width, H = c.height;
  var det = sitiosData[sitioActualId];
  var n = det.sol.frac.length;

  ctx.clearRect(0, 0, W, H);
  for (var i = 0; i < n; i++) {
    var x = (i / n) * W;
    var w = Math.ceil(W / n);
    var f = det.sol.frac[i];
    ctx.fillStyle = f > 0 ? "rgba(253, 224, 71," + (0.25 + 0.75 * f) + ")" : "#111827";
    ctx.fillRect(x, 4, w, 32);

    ctx.fillStyle = det.tierra.visible[i] ? "#38bdf8" : "#111827";
    ctx.fillRect(x, 44, w, 32);
  }
}

// 6. Lo que ofrece este sitio (#facts)
function renderFacts() {
  var info = meta.sitios.find(function (s) { return s.id === sitioActualId; });
  var det = sitiosData[sitioActualId];
  var r = det.resumen || {};
  var t = det.terreno || {};

  var datos = [
    ["Sunlight", r.luz_pct != null ? r.luz_pct.toFixed(1) + "%" : "—"],
    ["Earth in view", r.tierra_pct != null ? r.tierra_pct.toFixed(1) + "%" : "—"],
    ["Longest night", r.noche_max_h != null ? r.noche_max_h + " h" : "—"],
    ["Longest no-Earth", r.sin_tierra_max_h != null ? r.sin_tierra_max_h + " h" : "—"],
    ["Slope", t.pendiente_deg != null ? t.pendiente_deg.toFixed(1) + "°" : "—"],
    ["Distance to shadow", t.dist_sombra_m != null ? Math.round(t.dist_sombra_m) + " m" : "—"],
    ["Elevation", info.altura_m + " m"]
  ];

  document.getElementById("facts").innerHTML = datos.map(function (d) {
    return "<div><dt>" + d[0] + "</dt><dd>" + d[1] + "</dd></div>";
  }).join("");
}

// 7. Tabla comparativa (#cmp)
function construirTablaComparativa() {
  var filas = meta.sitios.map(function (s) {
    var d = sitiosData[s.id];
    var r = d.resumen || {};
    var t = d.terreno || {};
    return {
      nombre: s.nombre_en,
      luz: r.luz_pct,
      noche: r.noche_max_h,
      tierra: r.tierra_pct,
      ambos: r.sol_y_tierra_pct,
      dist: t.dist_sombra_m,
      pend: t.pendiente_deg
    };
  });

  var maxLuz = Math.max.apply(null, filas.map(function (f) { return f.luz || 0; }));
  var minNoche = Math.min.apply(null, filas.map(function (f) { return f.noche != null ? f.noche : 99999; }));
  var maxTierra = Math.max.apply(null, filas.map(function (f) { return f.tierra || 0; }));
  var maxAmbos = Math.max.apply(null, filas.map(function (f) { return f.ambos || 0; }));
  var minDist = Math.min.apply(null, filas.map(function (f) { return f.dist != null ? f.dist : 999999; }));
  var minPend = Math.min.apply(null, filas.map(function (f) { return f.pend != null ? f.pend : 999; }));

  document.querySelector("#cmp tbody").innerHTML = filas.map(function (f) {
    return "<tr>" +
      "<td><strong>" + f.nombre + "</strong></td>" +
      "<td class='" + (f.luz === maxLuz ? "best" : "") + "'>" + (f.luz != null ? f.luz.toFixed(1) + "%" : "—") + "</td>" +
      "<td class='" + (f.noche === minNoche ? "best" : "") + "'>" + (f.noche != null ? f.noche + " h" : "—") + "</td>" +
      "<td class='" + (f.tierra === maxTierra ? "best" : "") + "'>" + (f.tierra != null ? f.tierra.toFixed(1) + "%" : "—") + "</td>" +
      "<td class='" + (f.ambos === maxAmbos ? "best" : "") + "'>" + (f.ambos != null ? f.ambos.toFixed(1) + "%" : "—") + "</td>" +
      "<td class='" + (f.dist === minDist ? "best" : "") + "'>" + (f.dist != null ? Math.round(f.dist) + " m" : "—") + "</td>" +
      "<td class='" + (f.pend === minPend ? "best" : "") + "'>" + (f.pend != null ? f.pend.toFixed(1) + "°" : "—") + "</td>" +
    "</tr>";
  }).join("");
}

// --- Luna 3D real con textura oficial fotorrealista de la NASA ---
(function iniciarLuna3DReal() {
  var canvas = document.getElementById("polo-3d");
  if (!canvas || typeof THREE === "undefined") return;

  var ancho = canvas.parentElement.clientWidth || 760;
  var alto = 360;

  var escena = new THREE.Scene();
  var camara = new THREE.PerspectiveCamera(36, ancho / alto, 0.1, 100);
  camara.position.set(0, -2.4, 1.8);
  camara.lookAt(0, 0, 0);

  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setSize(ancho, alto);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Cargar textura real de alta calidad de la Luna
  var loader = new THREE.TextureLoader();
  loader.setCrossOrigin("anonymous");
  
  // Usamos una textura equirectangular estándar de la Luna de alta fidelidad
  var texturaLunar = loader.load(
    "https://threejs.org/examples/textures/planets/moon_1024.jpg",
    function () { renderer.render(escena, camara); },
    undefined,
    function () {
      console.warn("No se pudo cargar la textura externa, usando modo de respaldo.");
    }
  );

  var geometria = new THREE.SphereGeometry(1.0, 64, 64);
  var material = new THREE.MeshStandardMaterial({
    map: texturaLunar,
    roughness: 0.9,
    metalness: 0.05
  });

  var luna = new THREE.Mesh(geometria, material);
  escena.add(luna);

  // Luz solar lateral para modelar los cráteres y el relieve de forma natural
  var luzSolar = new THREE.DirectionalLight(0xfffbeb, 1.7);
  luzSolar.position.set(3.5, -0.5, 2.0);
  escena.add(luzSolar);

  var luzAmbiente = new THREE.AmbientLight(0x475569, 0.45);
  escena.add(luzAmbiente);

  var arrastrando = false;
  var prevX = 0, prevY = 0;

  canvas.addEventListener("mousedown", function (e) {
    arrastrando = true;
    prevX = e.clientX;
    prevY = e.clientY;
  });
  window.addEventListener("mouseup", function () { arrastrando = false; });
  window.addEventListener("mousemove", function (e) {
    if (!arrastrando) return;
    luna.rotation.y += (e.clientX - prevX) * 0.005;
    luna.rotation.x = Math.max(-0.75, Math.min(0.75, luna.rotation.x + (e.clientY - prevY) * 0.005));
    prevX = e.clientX;
    prevY = e.clientY;
  });

  window.addEventListener("resize", function () {
    var nuevoAncho = canvas.parentElement.clientWidth || 760;
    camara.aspect = nuevoAncho / alto;
    camara.updateProjectionMatrix();
    renderer.setSize(nuevoAncho, alto);
  });

  function animar() {
    if (!arrastrando) {
      luna.rotation.y += 0.0005; // Rotación lenta y elegante
    }
    renderer.render(escena, camara);
    requestAnimationFrame(animar);
  }

  animar();
})();