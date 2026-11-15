// ===================================================================
// Polelit — interfaz web. Lee los JSON de data/ (calculados en calculo/).
// ===================================================================
var meta = null;
var sitiosData = {};
var sitioActualId = null;
var horaActual = 0;
var reproduciendo = false;
var timerPlay = null;
var prioridad = "energy";
var lang = "en";

// ---------- 0. Textos en inglés y español ----------
var I18N = {
  en: {
    nav_about: "About", nav_how: "How it works", nav_sites: "Sites", nav_nav: "Navigator", nav_faq: "FAQ",
    mode_edu: "Educator view", mode_tech: "Technical view",
    hero_kicker: "NASA Space Apps 2026 · Lunar Landing Site Navigator",
    hero_title: "Find where to <span class=\"hl\">land</span> on the Moon's south pole",
    hero_lead: "See the Sun and the Earth over the real horizon of each landing site, hour by hour in 2027, to judge solar power and direct communication at a glance.",
    hero_open: "Open navigator →", hero_code: "View code on GitHub",
    stat_sites: "south-pole sites", stat_hours: "hours simulated", stat_valid: "vs 88.0% published",
    moon_note: "Illustrative image · Drag to rotate",
    about_kicker: "Why it matters", about_title: "Why is it so hard to choose where to land?",
    about_lead: "At the lunar south pole the Sun never rises high. A nearby mountain can leave a site in darkness for days, and the Earth, needed for direct communication, keeps hiding behind the horizon. Deep craters stay in permanent shadow and may trap water ice.",
    f1_t: "Real horizon", f1_p: "360° horizon computed from NASA LOLA elevation maps, including the curvature of the Moon. No atmosphere: only terrain blocks the view.",
    f2_t: "NASA ephemerides", f2_p: "Sun and Earth positions from JPL Horizons, every hour of 2027. Libration is included.",
    f3_t: "Validated", f3_p: "Average sunlight on the Shackleton–de Gerlache ridge: 88.2% (ours) vs 88.0% (Gläser et al. 2017).",
    how_kicker: "How it works", how_title: "Three steps to evaluate a site",
    s1_t: "Choose a site", s1_p: "Pick one of four south-pole landing sites, or let the tool recommend one for your mission.",
    s2_t: "Choose a date", s2_p: "Move through 2027 hour by hour, press Play, or pick a landing day.",
    s3_t: "Read the results", s3_p: "Sun and Earth over the horizon, time to sunset and Earthset, slope and nearby permanent shadow.",
    sites_kicker: "Mission planner", sites_title: "What does your mission need most?",
    g_energy: "Energy", g_energy_s: "Most sunlight for solar panels",
    g_comm: "Communication", g_comm_s: "Earth in view most of the time",
    g_both: "Balanced", g_both_s: "Sun and Earth at the same time",
    tags_note: "Tags use simple thresholds chosen by the team: green = good, amber = fair, red = poor.",
    reco_badge: "Recommended site", reco_go: "See it in the navigator →",
    reco_energy: "Sunlight {v}% of the year — the most of the four sites.",
    reco_comm: "Earth in view {v}% of the year — the most of the four sites.",
    reco_both: "Sun and Earth visible together {v}% of the year — the most of the four sites.",
    rank: "#{n}",
    t_light: "Light", t_earth: "Earth", t_night: "Longest night", t_slope: "Slope",
    lv_good: "Good", lv_mid: "Fair", lv_bad: "Poor",
    nav_kicker: "Navigator",
    v_light: "☀️ Sunlight", v_earth: "🌍 Earth in view", v_night: "🌙 Longest night", v_slope: "⛰️ Slope (50 m)",
    days: "days", day: "day", hours: "h",
    sky_title: "View from the lander",
    sky_note: "The grey ground is the horizon seen from this site, all 360 degrees. Heights are stretched so small hills show up. On the Moon the sky stays black even in daylight.",
    play: "Play", pause: "Pause",
    year_title: "A year of light and signal",
    year_note: "Yellow: Sun visible (brighter = more of the disk). Blue: Earth in view. The white line is the selected hour. Click to jump to a time.",
    cd_sun_up: "The Sun sets in {t}", cd_sun_down: "The Sun rises in {t}",
    cd_earth_up: "The Earth hides in {t}", cd_earth_down: "The Earth appears in {t}",
    cd_never: "not before the end of 2027",
    edu_up: "Sun is up ({p}%)", edu_down: "In shadow", edu_earth: "Earth in view", edu_noearth: "No Earth signal",
    tech_sunset: "Sunset in", tech_sunrise: "Sunrise in", tech_earthhide: "Earth hides in", tech_earthappear: "Earth appears in",
    win_title: "Best landing window in 2027",
    win_text: "<b>{a} → {b}</b> · {d} with the Sun and the Earth in view at the same time.",
    win_none: "There is no period with the Sun and the Earth in view at the same time.",
    k1_t: "2 km can change everything", k1_p: "On the rim of Shackleton crater the Sun is visible 85% of the year. Just 2 km inside the crater, it drops to 9%.",
    k2_t: "Moon vs Earth",
    k2_p: "Here the longest night lasts {d} days. On Earth, a night always lasts less than one day.",
    facts_title: "Whole year 2027", facts_note: "Totals over all 8,760 hours. They change only when you pick another site.",
    now_title: "Selected moment", day_title: "Selected day", pick_day: "Pick a day:", hourly: "Hour by hour (24 h)",
    th_hour: "Hour (UTC)", th_sunlit: "Sun lit", th_sunel: "Sun elevation", th_earth: "Earth in view", th_earthel: "Earth elevation",
    dl_day: "Download this day (.txt)", dl_year: "Download full year (.txt)",
    fa_sun: "Sunlight", fa_earth: "Earth in view", fa_night: "Longest night", fa_noearth: "Longest no-Earth",
    fa_both: "Sun and Earth", fa_slope: "Slope (50 m avg)", fa_shadow: "Distance to permanent shadow", fa_elev: "Elevation",
    no_sun: "Sun", no_sunel: "Sun elevation", no_earth: "Earth", no_earthel: "Earth elevation",
    up_vis: "Up ({p}% visible)", in_shadow: "In shadow", in_view: "In view", hidden: "Hidden", not2027: "not in 2027",
    d_sun: "Hours with Sun", d_earth: "Hours with Earth in view", d_both: "Hours with both", d_dark: "Longest darkness that day", of: "of",
    yes: "Yes", no: "No",
    map_title: "South Pole Overview",
    map_note: "Lunar south pole map showing permanently shadowed regions (dark) and the four landing sites. Click a site to select it.",
    cmp_title: "Compare the sites", c_site: "Site", c_sun: "Sunlight", c_night: "Longest night", c_earth: "Earth in view",
    c_both: "Sun and Earth", c_shadow: "Distance to shadow", c_slope: "Slope",
    cmp_note: "Green = best value in each column. Slope is the average within 50 m of the site.",
    faq_kicker: "FAQ", faq_title: "Common questions",
    q1: "Where does the data come from?",
    a1: "Sun and Earth positions come from NASA JPL Horizons, every hour of 2027. The terrain comes from LOLA elevation maps (Lunar Orbiter Laser Altimeter) published by NASA PGDA: an 80 m map for the horizon, 5 m maps for slope and a 20 m map of permanent shadows.",
    q2: "Why 2 meters above the ground?",
    a2: "That is the typical height of a lander's solar panels, the same height used in the reference study by Gläser et al. (2017).",
    q3: "What is a permanently shadowed region?",
    a3: "A place, usually inside a crater, that never receives direct sunlight. They are extremely cold and may hold water ice, one of the main reasons to explore the south pole.",
    q4: "Why is the lunar sky black even in daylight?",
    a4: "The Moon has no atmosphere to scatter sunlight. For the same reason there is no refraction: the horizon is set only by the terrain and the curvature of the Moon.",
    q5: "How accurate is it?",
    a5: "Average sunlight on the ridge is 88.2% vs 88.0% published by Gläser et al. (2017), and the longest night on the Shackleton rim is 64 h vs 65 h. Differences remain because we simulate one year (2027) with an 80 m map, while the paper averages 20 years with finer maps.",
    foot_name: "Pole + lit: \"the lit pole\". Team from Buenos Aires, NASA Space Apps Challenge 2026.",
    foot_data: "Data sources", foot_proj: "Project",
    foot_ai: "Built with the help of AI tools (Claude). Not an official NASA product."
  },
  es: {
    nav_about: "Proyecto", nav_how: "Cómo funciona", nav_sites: "Sitios", nav_nav: "Navegador", nav_faq: "Preguntas",
    mode_edu: "Vista educativa", mode_tech: "Vista técnica",
    hero_kicker: "NASA Space Apps 2026 · Navegador de sitios de aterrizaje lunar",
    hero_title: "Encontrá dónde <span class=\"hl\">aterrizar</span> en el polo sur de la Luna",
    hero_lead: "Mirá el Sol y la Tierra sobre el horizonte real de cada sitio de aterrizaje, hora por hora en 2027, para evaluar de un vistazo la energía solar y la comunicación directa.",
    hero_open: "Abrir el navegador →", hero_code: "Ver el código en GitHub",
    stat_sites: "sitios del polo sur", stat_hours: "horas simuladas", stat_valid: "vs 88,0 % publicado",
    moon_note: "Imagen ilustrativa · Arrastrá para girar",
    about_kicker: "Por qué importa", about_title: "¿Por qué es tan difícil elegir dónde aterrizar?",
    about_lead: "En el polo sur de la Luna el Sol nunca sube alto. Una montaña cercana puede dejar un sitio a oscuras durante días, y la Tierra, necesaria para comunicarse directamente, se esconde detrás del horizonte. Los cráteres profundos quedan en sombra permanente y pueden guardar hielo de agua.",
    f1_t: "Horizonte real", f1_p: "Horizonte de 360° calculado con los mapas de altura LOLA de NASA, incluyendo la curvatura de la Luna. Sin atmósfera: solo el terreno tapa la vista.",
    f2_t: "Efemérides de NASA", f2_p: "Posiciones del Sol y la Tierra de JPL Horizons, cada hora de 2027. Incluye la libración.",
    f3_t: "Validado", f3_p: "Luz media en la cresta Shackleton–de Gerlache: 88,2 % (nuestro) vs 88,0 % (Gläser et al. 2017).",
    how_kicker: "Cómo funciona", how_title: "Tres pasos para evaluar un sitio",
    s1_t: "Elegí un sitio", s1_p: "Elegí uno de los cuatro sitios del polo sur, o dejá que la herramienta te recomiende uno para tu misión.",
    s2_t: "Elegí una fecha", s2_p: "Recorré 2027 hora por hora, apretá Play o elegí un día de aterrizaje.",
    s3_t: "Leé los resultados", s3_p: "Sol y Tierra sobre el horizonte, tiempo hasta la puesta del Sol y de la Tierra, pendiente y sombra permanente cercana.",
    sites_kicker: "Planificador de misión", sites_title: "¿Qué necesita más tu misión?",
    g_energy: "Energía", g_energy_s: "La mayor cantidad de luz para los paneles",
    g_comm: "Comunicación", g_comm_s: "La Tierra visible la mayor parte del tiempo",
    g_both: "Equilibrado", g_both_s: "Sol y Tierra al mismo tiempo",
    tags_note: "Las etiquetas usan umbrales simples elegidos por el equipo: verde = bueno, ámbar = regular, rojo = malo.",
    reco_badge: "Sitio recomendado", reco_go: "Verlo en el navegador →",
    reco_energy: "Luz el {v} % del año: el más alto de los cuatro sitios.",
    reco_comm: "Tierra visible el {v} % del año: el más alto de los cuatro sitios.",
    reco_both: "Sol y Tierra visibles a la vez el {v} % del año: el más alto de los cuatro sitios.",
    rank: "N.º {n}",
    t_light: "Luz", t_earth: "Tierra", t_night: "Noche más larga", t_slope: "Pendiente",
    lv_good: "Buena", lv_mid: "Regular", lv_bad: "Mala",
    nav_kicker: "Navegador",
    v_light: "☀️ Luz", v_earth: "🌍 Tierra visible", v_night: "🌙 Noche más larga", v_slope: "⛰️ Pendiente (50 m)",
    days: "días", day: "día", hours: "h",
    sky_title: "Vista desde el módulo",
    sky_note: "El suelo gris es el horizonte visto desde este sitio, en 360 grados. Las alturas están exageradas para que se vean los cerros chicos. En la Luna el cielo es negro aunque sea de día.",
    play: "Play", pause: "Pausa",
    year_title: "Un año de luz y señal",
    year_note: "Amarillo: Sol visible (más claro = más disco). Azul: Tierra visible. La línea blanca es la hora elegida. Hacé clic para saltar a un momento.",
    cd_sun_up: "El Sol se pone en {t}", cd_sun_down: "El Sol sale en {t}",
    cd_earth_up: "La Tierra se oculta en {t}", cd_earth_down: "La Tierra aparece en {t}",
    cd_never: "no antes de fin de 2027",
    edu_up: "Sol arriba ({p} %)", edu_down: "En sombra", edu_earth: "Tierra visible", edu_noearth: "Sin señal de la Tierra",
    tech_sunset: "Puesta del Sol en", tech_sunrise: "Salida del Sol en", tech_earthhide: "La Tierra se oculta en", tech_earthappear: "La Tierra aparece en",
    win_title: "Mejor ventana de aterrizaje en 2027",
    win_text: "<b>{a} → {b}</b> · {d} con el Sol y la Tierra visibles al mismo tiempo.",
    win_none: "No hay ningún período con el Sol y la Tierra visibles al mismo tiempo.",
    k1_t: "2 km pueden cambiarlo todo", k1_p: "En el borde del cráter Shackleton el Sol se ve el 85 % del año. Solo 2 km más adentro del cráter, baja al 9 %.",
    k2_t: "Luna vs Tierra",
    k2_p: "Acá la noche más larga dura {d} días. En la Tierra, una noche siempre dura menos de un día.",
    facts_title: "Año completo 2027", facts_note: "Totales de las 8760 horas. Solo cambian al elegir otro sitio.",
    now_title: "Momento elegido", day_title: "Día elegido", pick_day: "Elegí un día:", hourly: "Hora por hora (24 h)",
    th_hour: "Hora (UTC)", th_sunlit: "Sol visible", th_sunel: "Elevación del Sol", th_earth: "Tierra visible", th_earthel: "Elevación de la Tierra",
    dl_day: "Descargar este día (.txt)", dl_year: "Descargar el año (.txt)",
    fa_sun: "Luz", fa_earth: "Tierra visible", fa_night: "Noche más larga", fa_noearth: "Máx. sin Tierra",
    fa_both: "Sol y Tierra", fa_slope: "Pendiente (media 50 m)", fa_shadow: "Distancia a sombra permanente", fa_elev: "Altura",
    no_sun: "Sol", no_sunel: "Elevación del Sol", no_earth: "Tierra", no_earthel: "Elevación de la Tierra",
    up_vis: "Arriba ({p} % visible)", in_shadow: "En sombra", in_view: "Visible", hidden: "Oculta", not2027: "no en 2027",
    d_sun: "Horas con Sol", d_earth: "Horas con Tierra visible", d_both: "Horas con ambos", d_dark: "Oscuridad más larga del día", of: "de",
    yes: "Sí", no: "No",
    map_title: "Mapa del polo sur",
    map_note: "Mapa del polo sur lunar con las regiones de sombra permanente (oscuras) y los cuatro sitios. Hacé clic en un sitio para elegirlo.",
    cmp_title: "Comparar los sitios", c_site: "Sitio", c_sun: "Luz", c_night: "Noche más larga", c_earth: "Tierra visible",
    c_both: "Sol y Tierra", c_shadow: "Distancia a la sombra", c_slope: "Pendiente",
    cmp_note: "Verde = mejor valor de cada columna. La pendiente es la media en 50 m alrededor del sitio.",
    faq_kicker: "Preguntas", faq_title: "Preguntas frecuentes",
    q1: "¿De dónde salen los datos?",
    a1: "Las posiciones del Sol y la Tierra vienen de JPL Horizons (NASA), cada hora de 2027. El terreno viene de los mapas de altura LOLA (Lunar Orbiter Laser Altimeter) publicados por NASA PGDA: un mapa de 80 m para el horizonte, mapas de 5 m para la pendiente y un mapa de 20 m de sombras permanentes.",
    q2: "¿Por qué a 2 metros del suelo?",
    a2: "Es la altura típica de los paneles solares de un módulo de aterrizaje, la misma que usa el estudio de referencia de Gläser et al. (2017).",
    q3: "¿Qué es una región de sombra permanente?",
    a3: "Un lugar, generalmente dentro de un cráter, que nunca recibe luz directa del Sol. Son muy frías y pueden guardar hielo de agua, uno de los motivos principales para explorar el polo sur.",
    q4: "¿Por qué el cielo lunar es negro aunque sea de día?",
    a4: "La Luna no tiene atmósfera que disperse la luz del Sol. Por eso tampoco hay refracción: el horizonte depende solo del terreno y de la curvatura de la Luna.",
    q5: "¿Qué tan preciso es?",
    a5: "La luz media en la cresta da 88,2 % contra 88,0 % publicado por Gläser et al. (2017), y la noche más larga en el borde de Shackleton da 64 h contra 65 h. Quedan diferencias porque simulamos un año (2027) con un mapa de 80 m, mientras el paper promedia 20 años con mapas más finos.",
    foot_name: "Pole + lit: \"el polo iluminado\". Equipo de Buenos Aires, NASA Space Apps Challenge 2026.",
    foot_data: "Fuentes de datos", foot_proj: "Proyecto",
    foot_ai: "Hecho con ayuda de herramientas de IA (Claude). No es un producto oficial de NASA."
  }
};
function t(k, vars) {
  var s = (I18N[lang] && I18N[lang][k]) || I18N.en[k] || k;
  if (vars) Object.keys(vars).forEach(function (v) { s = s.split("{" + v + "}").join(vars[v]); });
  return s;
}
function num(v, d) {   // número con coma decimal en español
  var s = Number(v).toFixed(d);
  return lang === "es" ? s.replace(".", ",") : s;
}
function pct(v) { return num(v, 1) + (lang === "es" ? " %" : "%"); }
function nombreSitio(s) { return lang === "es" ? (s.nombre || s.nombre_en) : (s.nombre_en || s.nombre); }
function infoSitio(id) { id = id || sitioActualId; return meta.sitios.find(function (s) { return s.id === id; }); }
function enTiempo(h) {   // horas -> "75 días" o "21 h"
  if (h == null) return t("cd_never");
  if (h < 48) return h + " " + t("hours");
  var d = h / 24;
  return num(d, d < 10 ? 1 : 0) + " " + t("days");
}

// ---------- 1. Idioma y vista ----------
function aplicarIdioma(l) {
  lang = l;
  try { localStorage.setItem("polelit_lang", l); } catch (e) {}
  document.documentElement.lang = l;
  document.querySelectorAll("[data-i18n]").forEach(function (el) { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach(function (el) { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.lang === l ? "true" : "false"); });
  btnPlay.textContent = reproduciendo ? t("pause") : t("play");
  if (meta) {
    document.querySelectorAll("#site-buttons button").forEach(function (b) { b.textContent = nombreSitio(infoSitio(b.dataset.id)); });
    document.querySelectorAll(".map-site").forEach(function (b) {
      var s = infoSitio(b.dataset.id);
      if (s) b.querySelector(".map-label").textContent = nombreSitio(s);
    });
    construirTablaComparativa();
    renderPrioridad();
    renderTodo();
  }
}
document.querySelectorAll("[data-lang]").forEach(function (b) {
  b.addEventListener("click", function () { aplicarIdioma(b.dataset.lang); });
});
document.querySelectorAll(".mode button[data-mode]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    document.body.dataset.mode = btn.dataset.mode;
    document.querySelectorAll(".mode button[data-mode]").forEach(function (b) {
      b.setAttribute("aria-pressed", b === btn ? "true" : "false");
    });
    renderTodo();
  });
});

// ---------- 2. Cargar sitios.json y un JSON por sitio ----------
fetch("data/sitios.json")
  .then(function (r) { return r.json(); })
  .then(function (data) {
    meta = data;
    var cont = document.getElementById("site-buttons");
    cont.innerHTML = "";
    data.sitios.forEach(function (s) {
      var b = document.createElement("button");
      b.type = "button";
      b.dataset.id = s.id;
      b.addEventListener("click", function () { seleccionarSitio(s.id); });
      cont.appendChild(b);
    });
    return Promise.all(data.sitios.map(function (s) {
      return fetch("data/" + s.id + ".json")
        .then(function (r) { return r.json(); })
        .then(function (det) { sitiosData[s.id] = det; });
    }));
  })
  .then(function () {
    sitioActualId = meta.sitios[0].id;
    aplicarIdioma(lang);
    seleccionarSitio(meta.sitios[0].id);
  });

function seleccionarSitio(id) {
  sitioActualId = id;
  document.querySelectorAll("#site-buttons button, .map-site, .site-card").forEach(function (b) {
    b.classList.toggle("active", b.dataset.id === id);
  });
  renderTodo();
}
document.querySelectorAll(".map-site").forEach(function (b) {
  b.addEventListener("click", function () { seleccionarSitio(b.dataset.id); });
});

// ---------- 3. Barra de tiempo y Play ----------
var slider = document.getElementById("slider");
var btnPlay = document.getElementById("play");
slider.max = 8759;
slider.addEventListener("input", function () { horaActual = Number(slider.value); renderHora(); });
btnPlay.addEventListener("click", function () {
  reproduciendo = !reproduciendo;
  btnPlay.textContent = reproduciendo ? t("pause") : t("play");
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
  var s = infoSitio();
  document.getElementById("site-title").textContent = nombreSitio(s) + " · " + s.altura_m + " m";
  renderVeredicto();
  renderVentana();
  renderFacts();
  renderHora();
}

function renderHora() {
  if (!sitioActualId || !sitiosData[sitioActualId]) return;
  var det = sitiosData[sitioActualId];
  var h = horaActual;
  document.getElementById("when").textContent = fmtFecha(h);

  var solFrac = det.sol.frac[h];
  var tierraVis = det.tierra.visible[h];
  var solCuenta = solFrac > 0 ? t("tech_sunset") + " " + enHoras(det.sol.hasta_puesta[h]) : t("tech_sunrise") + " " + enHoras(det.sol.hasta_salida[h]);
  var tierraCuenta = tierraVis ? t("tech_earthhide") + " " + enHoras(det.tierra.hasta_puesta[h]) : t("tech_earthappear") + " " + enHoras(det.tierra.hasta_salida[h]);

  document.getElementById("r-edu").textContent =
    (solFrac > 0 ? t("edu_up", { p: Math.round(solFrac * 100) }) : t("edu_down")) +
    " · " + (tierraVis ? t("edu_earth") : t("edu_noearth"));
  document.getElementById("r-tech").textContent =
    "Sun el: " + det.sol.el[h].toFixed(2) + "° (frac: " + solFrac.toFixed(2) + ") · " +
    "Earth: " + (tierraVis ? t("yes") : t("no")) + " (el: " + det.tierra.el[h].toFixed(2) + "°) · " +
    solCuenta + " · " + tierraCuenta;

  // cuenta regresiva grande (vista educativa)
  document.getElementById("cd-sun").textContent = solFrac > 0
    ? t("cd_sun_up", { t: enTiempo(det.sol.hasta_puesta[h]) })
    : t("cd_sun_down", { t: enTiempo(det.sol.hasta_salida[h]) });
  document.getElementById("cd-earth").textContent = tierraVis
    ? t("cd_earth_up", { t: enTiempo(det.tierra.hasta_puesta[h]) })
    : t("cd_earth_down", { t: enTiempo(det.tierra.hasta_salida[h]) });

  dibujarHorizonte(det, h);
  dibujarFranjasAnuales();
  renderAhora(det, h);
  renderDia(det, h);
}

// ---------- 4. Vista desde el módulo (#sky) ----------
function dibujarHorizonte(det, h) {
  var c = document.getElementById("sky");
  c.width = c.clientWidth;
  c.height = c.clientHeight;
  var ctx = c.getContext("2d");
  var W = c.width, H = c.height;

  ctx.fillStyle = "#03050f";          // cielo negro: la Luna no tiene atmósfera
  ctx.fillRect(0, 0, W, H);

  var minEl = -5, maxEl = 5;
  function x(az) { return (az / 360) * W; }
  function y(el) { return H - ((el - minEl) / (maxEl - minEl)) * H; }
  function yLim(el) { return Math.max(10, Math.min(H - 10, y(el))); }

  // Sol (con halo si está visible)
  var sx = x(det.sol.az[h]), sy = yLim(det.sol.el[h]);
  if (det.sol.frac[h] > 0) {
    var g = ctx.createRadialGradient(sx, sy, 2, sx, sy, 40);
    g.addColorStop(0, "rgba(251,191,36,.55)"); g.addColorStop(1, "rgba(251,191,36,0)");
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(sx, sy, 40, 0, Math.PI * 2); ctx.fill();
  }
  ctx.fillStyle = det.sol.frac[h] > 0 ? "#fde047" : "rgba(253,224,71,0.25)";
  ctx.beginPath(); ctx.arc(sx, sy, 10, 0, Math.PI * 2); ctx.fill();

  // Tierra (apagada si está oculta; pegada al borde si queda fuera de escala)
  var ex = x(det.tierra.az[h]), ey = yLim(det.tierra.el[h]);
  ctx.fillStyle = det.tierra.visible[h] ? "#38bdf8" : "rgba(56,189,248,0.25)";
  ctx.beginPath(); ctx.arc(ex, ey, 8, 0, Math.PI * 2); ctx.fill();
  if (det.tierra.visible[h]) { ctx.strokeStyle = "#e0f2fe"; ctx.lineWidth = 1.5; ctx.stroke(); ctx.lineWidth = 1; }

  // Horizonte
  var az = det.horizonte.az, el = det.horizonte.el;
  var gt = ctx.createLinearGradient(0, H * 0.4, 0, H);
  gt.addColorStop(0, "#4b5672"); gt.addColorStop(1, "#1e2436");
  ctx.fillStyle = gt;
  ctx.strokeStyle = "#a5b4fc";
  ctx.beginPath();
  ctx.moveTo(0, H);
  for (var i = 0; i < el.length; i++) ctx.lineTo(x(az[i]), y(el[i]));
  ctx.lineTo(W, y(el[0]));
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // línea de 0° y puntos cardinales
  ctx.strokeStyle = "rgba(255,255,255,0.15)";
  ctx.setLineDash([4, 6]);
  ctx.beginPath(); ctx.moveTo(0, y(0)); ctx.lineTo(W, y(0)); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = "#a3acc9"; ctx.font = "12px sans-serif";
  var card = lang === "es" ? [["N", 0], ["E", 90], ["S", 180], ["O", 270]] : [["N", 0], ["E", 90], ["S", 180], ["W", 270]];
  card.forEach(function (p) { ctx.fillText(p[0], x(p[1]) + 4, 14); });
  ctx.fillText("0°", 4, y(0) - 4);
}

// ---------- 5. Franjas del año (#strips) ----------
function dibujarFranjasAnuales() {
  var c = document.getElementById("strips");
  if (!c.clientWidth) return;               // oculto en la vista educativa
  c.width = c.clientWidth;
  c.height = c.clientHeight || 80;
  var ctx = c.getContext("2d");
  var W = c.width;
  var det = sitiosData[sitioActualId];
  var n = det.sol.frac.length;

  ctx.clearRect(0, 0, W, c.height);
  for (var i = 0; i < n; i++) {
    var xx = (i / n) * W, w = Math.ceil(W / n);
    var f = det.sol.frac[i];
    ctx.fillStyle = f > 0 ? "rgba(251,191,36," + (0.25 + 0.75 * f) + ")" : "#111827";
    ctx.fillRect(xx, 4, w, 32);
    ctx.fillStyle = det.tierra.visible[i] ? "#38bdf8" : "#111827";
    ctx.fillRect(xx, 44, w, 32);
  }
  ctx.fillStyle = "#ffffff";
  ctx.fillRect((horaActual / n) * W - 1, 0, 2, 80);
}

// ---------- 6. Resumen, etiquetas y recomendación ----------
function resumenDe(det) {
  var r = det.resumen || {}, te = det.terreno || {};
  var n = det.sol.frac.length, ambos = 0;
  for (var i = 0; i < n; i++) if (det.sol.frac[i] > 0 && det.tierra.visible[i]) ambos++;
  return {
    luz: r.luz_pct, tierra: r.tierra_pct, noche: r.max_oscuridad_h, sinTierra: r.max_sin_tierra_h,
    ambos: ambos / n * 100, distKm: te.psr_dist_km, pend: te.pendiente_media_deg
  };
}
// Umbrales simples elegidos por el equipo (se aclara en la web)
function nivel(tipo, v) {
  if (v == null) return "mid";
  if (tipo === "luz") return v >= 80 ? "good" : v >= 60 ? "mid" : "bad";
  if (tipo === "tierra") return v >= 60 ? "good" : v >= 45 ? "mid" : "bad";
  if (tipo === "noche") return v <= 96 ? "good" : v <= 240 ? "mid" : "bad";
  if (tipo === "pend") return v <= 5 ? "good" : v <= 10 ? "mid" : "bad";
}
function txtNivel(nv) { return t(nv === "good" ? "lv_good" : nv === "mid" ? "lv_mid" : "lv_bad"); }

function renderVeredicto() {
  var x = resumenDe(sitiosData[sitioActualId]);
  var items = [
    ["v_light", pct(x.luz), nivel("luz", x.luz)],
    ["v_earth", pct(x.tierra), nivel("tierra", x.tierra)],
    ["v_night", num(x.noche / 24, 1) + " " + t("days"), nivel("noche", x.noche)],
    ["v_slope", num(x.pend, 1) + "°", nivel("pend", x.pend)]
  ];
  document.getElementById("verdict").innerHTML = items.map(function (it) {
    return "<div class='vcard " + it[2] + "'><div class='vlabel'>" + t(it[0]) + "</div><div class='vval'>" + it[1] +
      "</div><div class='vtag'>" + txtNivel(it[2]) + "</div></div>";
  }).join("");
  var k2 = document.getElementById("k2");
  if (k2) k2.textContent = t("k2_p", { d: num(x.noche / 24, 1) });
}

var CLAVE = { energy: "luz", comm: "tierra", both: "ambos" };
function renderPrioridad() {
  if (!meta) return;
  var clave = CLAVE[prioridad];
  var lista = meta.sitios.map(function (s) { return { s: s, x: resumenDe(sitiosData[s.id]) }; })
    .sort(function (a, b) { return b.x[clave] - a.x[clave]; });
  var top = lista[0];
  document.getElementById("reco").innerHTML =
    "<span class='badge'>" + t("reco_badge") + "</span><span class='rname'>" + nombreSitio(top.s) + "</span>" +
    "<a class='btn primary' href='#navigator' id='reco-go'>" + t("reco_go") + "</a>" +
    "<span class='rwhy'>" + t("reco_" + prioridad, { v: num(top.x[clave], 1) }) + "</span>";
  document.getElementById("reco-go").addEventListener("click", function () { seleccionarSitio(top.s.id); });

  document.getElementById("site-cards").innerHTML = lista.map(function (it, i) {
    var x = it.x;
    function tag(lbl, val, nv) { return "<span class='tag " + nv + "'><span>" + t(lbl) + "</span><span>" + val + "</span></span>"; }
    return "<button type='button' class='card site-card" + (it.s.id === sitioActualId ? " active" : "") + "' data-id='" + it.s.id + "'>" +
      "<span class='rank'>" + t("rank", { n: i + 1 }) + "</span><h3>" + nombreSitio(it.s) + "</h3><span class='tags'>" +
      tag("t_light", pct(x.luz), nivel("luz", x.luz)) +
      tag("t_earth", pct(x.tierra), nivel("tierra", x.tierra)) +
      tag("t_night", num(x.noche / 24, 1) + " " + t("days"), nivel("noche", x.noche)) +
      tag("t_slope", num(x.pend, 1) + "°", nivel("pend", x.pend)) +
      "</span></button>";
  }).join("");
  document.querySelectorAll(".site-card").forEach(function (b) {
    b.addEventListener("click", function () {
      seleccionarSitio(b.dataset.id);
      document.getElementById("navigator").scrollIntoView();
    });
  });
}
document.querySelectorAll(".goal-card").forEach(function (b) {
  b.addEventListener("click", function () {
    prioridad = b.dataset.goal;
    document.querySelectorAll(".goal-card").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
    renderPrioridad();
  });
});

// Mejor ventana: el tramo más largo con Sol y Tierra visibles a la vez
function renderVentana() {
  var det = sitiosData[sitioActualId], n = det.sol.frac.length;
  var mejorIni = -1, mejorLen = 0, ini = -1;
  for (var i = 0; i <= n; i++) {
    var ok = i < n && det.sol.frac[i] > 0 && det.tierra.visible[i];
    if (ok && ini < 0) ini = i;
    if (!ok && ini >= 0) { if (i - ini > mejorLen) { mejorLen = i - ini; mejorIni = ini; } ini = -1; }
  }
  var html = "<div class='ico'>🚀</div><div><h3>" + t("win_title") + "</h3><p>";
  if (mejorLen > 0) {
    html += t("win_text", { a: fmtFecha(mejorIni).slice(0, 16), b: fmtFecha(mejorIni + mejorLen - 1).slice(0, 16), d: enTiempo(mejorLen) });
  } else {
    html += t("win_none");
  }
  document.getElementById("window").innerHTML = html + "</p></div>";
}

// ---------- 7. Fichas del año y tabla comparativa ----------
function renderFacts() {
  var info = infoSitio(), x = resumenDe(sitiosData[sitioActualId]);
  llenarDL("facts", [
    [t("fa_sun"), pct(x.luz)],
    [t("fa_earth"), pct(x.tierra)],
    [t("fa_night"), x.noche + " h (" + num(x.noche / 24, 1) + " " + t("days") + ")"],
    [t("fa_noearth"), x.sinTierra + " h"],
    [t("fa_both"), pct(x.ambos)],
    [t("fa_slope"), num(x.pend, 1) + "°"],
    [t("fa_shadow"), x.distKm != null ? Math.round(x.distKm * 1000) + " m" : "—"],
    [t("fa_elev"), info.altura_m + " m"]
  ]);
}
function construirTablaComparativa() {
  var filas = meta.sitios.map(function (s) {
    var x = resumenDe(sitiosData[s.id]);
    return { nombre: nombreSitio(s), luz: x.luz, noche: x.noche, tierra: x.tierra, ambos: x.ambos, dist: x.distKm, pend: x.pend };
  });
  function mx(k) { return Math.max.apply(null, filas.map(function (f) { return f[k]; })); }
  function mn(k) { return Math.min.apply(null, filas.map(function (f) { return f[k]; })); }
  var best = { luz: mx("luz"), noche: mn("noche"), tierra: mx("tierra"), ambos: mx("ambos"), dist: mn("dist"), pend: mn("pend") };
  function td(k, v) { return "<td class='" + (filas.__f[k] === best[k] ? "best" : "") + "'>" + v + "</td>"; }
  document.querySelector("#cmp tbody").innerHTML = filas.map(function (f) {
    filas.__f = f;
    return "<tr><td><strong>" + f.nombre + "</strong></td>" +
      td("luz", pct(f.luz)) + td("noche", f.noche + " h") + td("tierra", pct(f.tierra)) +
      td("ambos", pct(f.ambos)) + td("dist", Math.round(f.dist * 1000) + " m") + td("pend", num(f.pend, 1) + "°") + "</tr>";
  }).join("");
}

// ---------- 8. Luna 3D ilustrativa (textura de threejs.org) ----------
(function iniciarLuna3D() {
  var canvas = document.getElementById("polo-3d");
  if (!canvas || typeof THREE === "undefined") return;
  var ancho = canvas.clientWidth || 520, alto = canvas.clientHeight || 420;
  var escena = new THREE.Scene();
  var camara = new THREE.PerspectiveCamera(36, ancho / alto, 0.1, 100);
  camara.position.set(0, -3.36, 2.52);
  camara.lookAt(0, 0, 0);
  var renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true });
  renderer.setSize(ancho, alto, false);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  
  renderer.outputEncoding = THREE.sRGBEncoding;   // colores correctos en .glb
var luna = new THREE.Group();
escena.add(luna);
new THREE.GLTFLoader().load("img/moon_small.glb", function (gltf) {
  var modelo = gltf.scene;
  var caja = new THREE.Box3().setFromObject(modelo);
  var tam = caja.getSize(new THREE.Vector3());
  var centro = caja.getCenter(new THREE.Vector3());
  var escala = 2 / Math.max(tam.x, tam.y, tam.z);   // que mida 2, como la esfera de antes
  modelo.scale.setScalar(escala);
  modelo.position.sub(centro.multiplyScalar(escala)); // centrado en el origen
  luna.add(modelo);
}, undefined, function (e) { console.error("No cargó la Luna 3D", e); });


  var luzSolar = new THREE.DirectionalLight(0xfffbeb, 1.7);
  luzSolar.position.set(3.5, -0.5, 2.0);
  escena.add(luzSolar);
  escena.add(new THREE.AmbientLight(0x475569, 0.45));
  var arrastrando = false, prevX = 0, prevY = 0;
  canvas.addEventListener("mousedown", function (e) { arrastrando = true; prevX = e.clientX; prevY = e.clientY; });
  window.addEventListener("mouseup", function () { arrastrando = false; });
  window.addEventListener("mousemove", function (e) {
    if (!arrastrando) return;
    luna.rotation.y += (e.clientX - prevX) * 0.005;
    luna.rotation.x = Math.max(-0.75, Math.min(0.75, luna.rotation.x + (e.clientY - prevY) * 0.005));
    prevX = e.clientX; prevY = e.clientY;
  });
  window.addEventListener("resize", function () {
    var w = canvas.clientWidth || 520, hh = canvas.clientHeight || 420;
    camara.aspect = w / hh; camara.updateProjectionMatrix(); renderer.setSize(w, hh, false);
  });
  (function animar() {
    if (!arrastrando) luna.rotation.y += 0.0008;
    renderer.render(escena, camara);
    requestAnimationFrame(animar);
  })();
})();

// ---------- 9. Momento, día y descargas ----------
function fmtFecha(h) {
  var f = new Date(Date.UTC(meta.anio || 2027, 0, 1, h, 0, 0));
  return f.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}
function llenarDL(id, pares) {
  document.getElementById(id).innerHTML = pares.map(function (p) {
    return "<div><dt>" + p[0] + "</dt><dd>" + p[1] + "</dd></div>";
  }).join("");
}
function enHoras(v) { return v != null ? v + " h" : t("not2027"); }

function renderAhora(det, h) {
  var sol = det.sol.frac[h] > 0, tie = det.tierra.visible[h] > 0;
  document.getElementById("now-when").textContent = fmtFecha(h);
  llenarDL("now", [
    [t("no_sun"), sol ? t("up_vis", { p: Math.round(det.sol.frac[h] * 100) }) : t("in_shadow")],
    [t("no_sunel"), det.sol.el[h].toFixed(2) + "°"],
    [sol ? t("tech_sunset") : t("tech_sunrise"), enHoras(sol ? det.sol.hasta_puesta[h] : det.sol.hasta_salida[h])],
    [t("no_earth"), tie ? t("in_view") : t("hidden")],
    [t("no_earthel"), det.tierra.el[h].toFixed(2) + "°"],
    [tie ? t("tech_earthhide") : t("tech_earthappear"), enHoras(tie ? det.tierra.hasta_puesta[h] : det.tierra.hasta_salida[h])]
  ]);
}
function renderDia(det, h) {
  var i0 = h - (h % 24), i1 = Math.min(i0 + 24, det.sol.frac.length);
  var hs = 0, ht = 0, hb = 0, racha = 0, maxR = 0, filas = "";
  for (var i = i0; i < i1; i++) {
    var s = det.sol.frac[i] > 0, te = det.tierra.visible[i] > 0;
    if (s) hs++;
    if (te) ht++;
    if (s && te) hb++;
    racha = s ? 0 : racha + 1;
    if (racha > maxR) maxR = racha;
    filas += "<tr" + (i === h ? " class='cur'" : "") + "><td>" + fmtFecha(i).slice(11, 16) + "</td>" +
      "<td>" + Math.round(det.sol.frac[i] * 100) + "%</td><td>" + det.sol.el[i].toFixed(2) + "°</td>" +
      "<td>" + (te ? t("yes") : t("no")) + "</td><td>" + det.tierra.el[i].toFixed(2) + "°</td></tr>";
  }
  var n = i1 - i0;
  document.getElementById("dia").value = fmtFecha(i0).slice(0, 10);
  llenarDL("day", [
    [t("d_sun"), hs + " " + t("of") + " " + n],
    [t("d_earth"), ht + " " + t("of") + " " + n],
    [t("d_both"), hb + " " + t("of") + " " + n],
    [t("d_dark"), maxR + " h"]
  ]);
  document.querySelector("#hours tbody").innerHTML = filas;
}

function pad(v, n) { return String(v).padStart(n); }
function armarTxt(det, info, desde, hasta) {
  var x = resumenDe(det), L = [];
  L.push("POLELIT - hourly data (all times UTC)");
  L.push("Site: " + info.nombre_en);
  L.push("Latitude: " + det.lat + "   Longitude: " + det.lon + "   Elevation: " + info.altura_m + " m");
  L.push("Whole-year summary: sunlight " + x.luz + "%, Earth in view " + x.tierra + "%, longest night " + x.noche + " h, longest without Earth " + x.sinTierra + " h");
  L.push("");
  L.push("DATE_TIME_UTC".padEnd(20) + "  " + pad("SUN%", 4) + "  " + pad("SUN_EL", 8) + "  " + pad("SUN_AZ", 7) + "  " + pad("EARTH", 6) + "  " + pad("EARTH_EL", 8) + "  " + pad("EARTH_AZ", 7));
  for (var i = desde; i < hasta; i++) {
    L.push(fmtFecha(i) + "  " + pad(Math.round(det.sol.frac[i] * 100), 4) + "  " + pad(det.sol.el[i].toFixed(2), 8) + "  " +
      pad(det.sol.az[i].toFixed(1), 7) + "  " + pad(det.tierra.visible[i] ? "yes" : "no", 6) + "  " +
      pad(det.tierra.el[i].toFixed(2), 8) + "  " + pad(det.tierra.az[i].toFixed(1), 7));
  }
  return L.join("\r\n");
}
function descargarTxt(nombre, texto) {
  var url = URL.createObjectURL(new Blob([texto], { type: "text/plain;charset=utf-8" }));
  var a = document.createElement("a");
  a.href = url; a.download = nombre;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}
document.getElementById("dl-day").addEventListener("click", function () {
  var det = sitiosData[sitioActualId], i0 = horaActual - (horaActual % 24);
  descargarTxt("polelit_" + sitioActualId + "_" + fmtFecha(i0).slice(0, 10) + ".txt",
    armarTxt(det, infoSitio(), i0, Math.min(i0 + 24, det.sol.frac.length)));
});
document.getElementById("dl-year").addEventListener("click", function () {
  var det = sitiosData[sitioActualId];
  descargarTxt("polelit_" + sitioActualId + "_" + (meta.anio || 2027) + ".txt",
    armarTxt(det, infoSitio(), 0, det.sol.frac.length));
});
document.getElementById("dia").addEventListener("change", function () {
  if (!this.value || !meta) return;
  var p = this.value.split("-").map(Number);
  var dia = Math.round((Date.UTC(p[0], p[1] - 1, p[2]) - Date.UTC(meta.anio || 2027, 0, 1)) / 86400000);
  horaActual = Math.max(0, Math.min(meta.horas - 1, dia * 24 + (horaActual % 24)));
  slider.value = horaActual;
  renderHora();
});
window.addEventListener("resize", function () { if (meta) renderHora(); });

// Idioma por defecto: inglés (o el último elegido)
try { var guardado = localStorage.getItem("polelit_lang"); if (guardado === "es" || guardado === "en") lang = guardado; } catch (e) {}