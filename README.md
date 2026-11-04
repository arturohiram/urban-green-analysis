# Urban green space and heat exposure in the Monterrey Metropolitan Area

Pixel-level vegetation map of the Monterrey Metropolitan Area (ZMM, Mexico) from Sentinel-2 imagery, combined with census, social-lag and surface-temperature data to rank the 2,155 urban census tracts (AGEB) by environmental criticality.

This is the data-analysis part of my final degree project (Industrial Physics Engineering, Tecnológico de Monterrey, 2025), where a team built the prototype of an Earth-observation nanosatellite. I did all the work in this repository: data download, labeling, model, validation and indicators. The original indicator analysis was done in QGIS; here every step is reproduced in Python and checked against the QGIS output.

![Vegetation map](results/map_vegetation.png)

## Key results

**1. Vegetation classifier (Random Forest, 13 spectral features, 1.14 M hand-labeled pixels)**

The original evaluation used a random 80/20 split of pixels. Neighbouring pixels of the same tile end up in train and test (and the 3×3 filter mixes them), so the score is optimistic. Re-evaluating with spatial groups:

| Evaluation | Balanced accuracy | Recall, no vegetation | Recall, vegetation |
|---|---|---|---|
| Random pixel split (original) | 0.961 | 0.939 | 0.982 |
| Grouped by tile (5 folds) | 0.940 | 0.908 | 0.973 |
| Leave one quadrant out (9 folds) | **0.917** | 0.855 | 0.978 |
| Baseline: NDVI > 0.3, no training | **0.942** | 0.918 | 0.966 |

- On areas the model has not seen, the Random Forest does **not** beat a fixed NDVI threshold. Vegetation is detected well by both; the gap is in recognizing what is *not* vegetation.
- The weakest quadrants are C4 and C7 (recall of non-vegetation 0.61 and 0.65): rock, shadow and dry scrub are classified as vegetation. Across the whole ZMM the model marks 82.2% of the area as vegetation vs 72.8% for NDVI, and the difference is concentrated in the arid north-west.
- Cause: 80% of the non-vegetation labels come from the urban center (quadrant C5); bare soil and rock are barely labeled.

![Random Forest vs NDVI](results/green_map_zmm.png)

**2. AGEB indicators (2,155 urban AGEB, 5.25 M inhabitants)**

| | All populated AGEB, 2,079 (median) | Priority AGEB (median) |
|---|---|---|
| Population density | 8,200 inh/km² | 15,700 inh/km² |
| Green inside the AGEB per inhabitant | 14.0 m² | 2.9 m² |
| Surface temperature vs urban mean | −0.1 °C | +2.0 °C |

- **155 priority AGEB with 599,810 inhabitants (11.4% of the ZMM)**: very high environmental criticality (density + temperature + lack of green access) and CONEVAL social lag *medium* or higher.
- The QGIS formulas are reproduced exactly (all 17 indicator columns match the QGIS layer when fed the same zonal statistics). With the new vegetation map, 152 of the 155 priority AGEB are also in the original QGIS result (174).

![Priority AGEB](results/map_priority_ageb.png)

![Land surface temperature](results/map_lst.png)

## Limitations

- **Validation covers the training grid only.** The model was trained on a first grid of tiles (C1–C9, about 2 km) and applied to a later export of the whole ZMM (Q11–Q33, about 3 km). Same collection, filters and bands, but different exports, so the prediction tiles are not directly validated.
- **Label imbalance.** See above: few labels of bare soil, rock and dry scrub.
- **The access component of the Green Score is saturated.** Access counts every vegetation pixel within 500 m (parks, private gardens, hills, empty lots), not public green space. Every populated AGEB is above the 9 m²/inhabitant target (minimum: 20 m²), so the access index, which weighs half of the score, is 100 everywhere. In practice the Green Score is driven by coverage and green per capita.
- **"Priority" means very high criticality and social lag medium or higher.** 153 of the 155 priority AGEB have *medium* social lag; none is *very high*.
- **Version-dependent results.** The Random Forest gives slightly different results across scikit-learn versions (balanced accuracy by quadrant 0.917 with 1.7.2 vs 0.930 with 1.9.1). The reported numbers use the versions in `requirements.txt`.
- **Original QGIS layer.** In the final QGIS layer the population column ended up overwritten with 0/1. The indicators had already been computed with the real population, but any total taken from that layer would be wrong. Here the population always comes from the census.

## Method

| Notebook | What it does |
|---|---|
| `01_sentinel_download.ipynb` | Google Earth Engine: Sentinel-2 SR Harmonized, Jan–Nov 2025, <5% clouds, SCL cloud/shadow mask, per-pixel median. Bands B2, B3, B4, B8, B8A, B11, B12 at 10 m. Exported as 9 quadrants × 15 × 15 tiles. Landsat-8 surface temperature (2025 median, °C, 30 m). |
| `02_model_validation.ipynb` | 3×3 Gaussian filter + 13 features (7 bands, NDVI, NDWI, NBR, RENDVI, VARI, ExG). Random Forest (200 trees, balanced class weights). Random, tile-grouped and quadrant-grouped validation, NDVI baseline. Final model trained on all labels. |
| `03_prediction.ipynb` | Classifies the 2,025 tiles of the ZMM (Random Forest and NDVI), builds the mosaic and clips it to the ZMM boundary. |
| `04_ageb_indicators.ipynb` | Zonal statistics by AGEB and 500 m buffer, green per capita, green access, temperature difference, criticality index (quintiles of density, temperature and inverted access), CONEVAL filter, Green Score, comparison with QGIS. |
| `05_maps.ipynb` | Final maps over the Sentinel-2 true color mosaic: vegetation, surface temperature and priority AGEB. |

Shared code: `utils.py` (image reading and features), `config.py` (all paths).

Labels were drawn by hand with a polygon tool (`mask_tool.py`, OpenCV): 49 tiles, 1,138,928 labeled pixels (25% non-vegetation).

**Criticality index** (based on the Heat Vulnerability Index logic: exposure, sensitivity, adaptive capacity):
`crit_amb = density_quintile + temperature_quintile + (6 − access_quintile)`, from 3 to 15; very high = 12 or more.

**Green Score** = (coverage index + green-per-capita index + 2 × access index) / 4, each index scaled 0–100 against a target (30% coverage, 30 m²/inhabitant, 9 m²/inhabitant).

## Data

Only the training data is included: the hand-drawn masks and the 49 labeled Sentinel-2 tiles (`data/raw/training_masks`, `data/raw/training_tiles`, 31 MB), enough to run notebook 02. The rest of `data/` (about 1.5 GB of inputs) comes from these sources:

| Data | Source | Folder |
|---|---|---|
| Sentinel-2 L2A | Google Earth Engine, `COPERNICUS/S2_SR_HARMONIZED` (notebook 01) | `data/raw/sentinel2`, `data/raw/training_tiles` |
| Vegetation labels | Drawn by hand | `data/raw/training_masks` |
| Land surface temperature | Landsat-8 Collection 2 Level 2 (`ST_B10`), 2025 median, Google Earth Engine (notebook 01; the original script was not saved, the cell is rewritten from the documented parameters) | `data/raw/lst` |
| AGEB polygons | INEGI, Marco Geoestadístico | `data/raw/inegi` |
| Population | INEGI, Censo de Población y Vivienda 2020, results by AGEB (`RESAGEBURB_19CSV20.csv`) | `data/raw/inegi` |
| Social lag | CONEVAL, Grado de Rezago Social por AGEB urbana 2020 | `data/raw/coneval` |
| ZMM boundary | 16 municipalities, INEGI | `data/raw/boundaries` |

## How to run

```
conda create -n urban-green -c conda-forge python=3.12 -y
conda activate urban-green
pip install -r requirements.txt
jupyter lab
```

Place the data in `data/raw/` as in the table above and run notebooks 02 → 03 → 04 → 05 (01 only to download the imagery again). Notebook 02 takes about 1.5 h (grouped validation), 03 about 1 h.

All notebooks are saved with their outputs, so the results can be read on GitHub without running anything.

## Repository structure

```
├── 01_sentinel_download.ipynb
├── 02_model_validation.ipynb
├── 03_prediction.ipynb
├── 04_ageb_indicators.ipynb
├── 05_maps.ipynb
├── config.py              paths
├── utils.py               image reading and features
├── mask_tool.py           labeling tool
├── requirements.txt
├── results/               tables and figures
└── data/raw/              training masks and tiles (other inputs and outputs not included)
```

---

### Resumen en español

Mapa de vegetación de la Zona Metropolitana de Monterrey a partir de imágenes Sentinel-2 (Random Forest, 1.14 millones de píxeles etiquetados a mano), cruzado con el Censo 2020, el rezago social de CONEVAL y la temperatura superficial de Landsat-8 para identificar las AGEB urbanas más críticas. Validado por cuadrantes no vistos, el modelo alcanza 0.917 de exactitud balanceada, por debajo de un umbral simple de NDVI (0.942). Se identifican 155 AGEB prioritarias con 599,810 habitantes. Parte de análisis de datos de mi proyecto final de Ingeniería Física Industrial (Tec de Monterrey, 2025).
