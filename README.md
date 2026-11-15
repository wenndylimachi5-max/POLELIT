# Polelit — Lunar South Pole Landing Site Navigator

**NASA Space Apps Challenge 2026 · Buenos Aires · Challenge: Lunar Landing Site Navigator**

**Website:** https://wenndylimachi5-max.github.io/POLELIT/web/

*Pole + lit: "the lit pole".* A web tool that shows the Sun and the Earth over the real horizon of four lunar south pole sites, hour by hour in 2027, to evaluate solar power and direct communication with Earth.

## What it does

- **Mission planner:** recommends a site based on the chosen priority (energy, communication or balanced).
- **View from the lander:** 360° horizon with the Sun and the Earth.
- **Time navigation:** move through 2027 hour by hour or pick a day.
- **Countdowns:** time until sunset and until the Earth hides or appears.
- **Best landing window:** longest period with the Sun and the Earth visible at the same time.
- **Compare two dates.**
- **Educator view and technical view**, in English and Spanish.

## How it works

1. **Sun and Earth:** positions from JPL Horizons (NASA), every hour of 2027, for an observer 2 m above the ground.
2. **Horizon:** computed from the LOLA 80 m map, in 360 directions up to 150 km, including the curvature of the Moon.
3. **Sunlight:** the Sun is treated as a disk, so the visible fraction is computed.
4. **Terrain:** slope from the LOLA 5 m maps and distance to permanent shadow from the 20 m map.
5. Results are saved as JSON files read by the website.

## Results (2027)

| Site | Sunlight | Earth in view | Longest night | Slope |
|---|---|---|---|---|
| Shackleton–de Gerlache Ridge | 88.2 % | 51.1 % | 188 h | 2.7° |
| Shackleton Rim | 85.1 % | 49.6 % | 64 h | 6.2° |
| de Gerlache Rim | 75.3 % | 54.8 % | 254 h | 8.2° |
| Malapert Massif | 52.1 % | 72.0 % | 383 h | 7.9° |

## Validation

Compared with Gläser et al. (2017):

| Site | Sunlight (Polelit / Gläser) | Longest night (Polelit / Gläser) |
|---|---|---|
| Shackleton–de Gerlache Ridge | 88.2 % / 88.0 % | 188 h / 112 h |
| Shackleton Rim | 85.1 % / 82.1 % | 64 h / 65 h |

Differences come from simulating one year with an 80 m map, while the paper averages 20 years with finer maps.

## Structure

```
calculo/   Python calculations
web/       Website
api/       Optional API (FastAPI)
```

## How to run

```
cd web
python -m http.server 8000
```

## Data and references

- [JPL Horizons (NASA/JPL)](https://ssd.jpl.nasa.gov/horizons/)
- [LOLA south pole maps, 80 m and 20 m (NASA PGDA)](https://pgda.gsfc.nasa.gov/products/90)
- [LOLA 5 m site maps (NASA PGDA)](https://pgda.gsfc.nasa.gov/products/78)
- [Moon 3D model (NASA SVS)](https://svs.gsfc.nasa.gov/14959)
- [Moon Trek (NASA)](https://trek.nasa.gov/moon/)
- [NASA DONKI](https://kauai.ccmc.gsfc.nasa.gov/DONKI/) and [NASA Image and Video Library](https://images.nasa.gov/) (API)
- Gläser et al. (2017), *Planetary and Space Science*
- Barker et al. (2021), *Planetary and Space Science*, doi:10.1016/j.pss.2020.105119
- Barker et al. (2023), *The Planetary Science Journal*, doi:10.3847/PSJ/acf3e1

## Use of AI

Claude (Anthropic) and ChatGPT (OpenAI) were used to help with code and texts. The logo was AI-generated.

## Team

Wenndy Limachi · Gerónimo Belfiori · Luis Loayza
