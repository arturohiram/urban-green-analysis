from pathlib import Path

# Everything lives inside the project folder
repoRoot=Path(__file__).parent
dataRoot=repoRoot/'data'
rawFolder=dataRoot/'raw'
processedFolder=dataRoot/'processed'
resultsFolder=repoRoot/'results'          # tables and figures uploaded to GitHub

# Google Earth Engine
geeProject='ee-a01177863'
boundaryAsset='projects/ee-a01177863/assets/ZMM_Boundary'

# Sentinel-2
s2Folder=rawFolder/'sentinel2'            # Qxx/S2_ZMM_2025_Qxx_Rxx_Cxx.tif (tiles for prediction)
s2FullFolder=s2Folder/'full'              # full mosaic and its 9 quadrants

# Training data (labeled C tiles and hand-drawn masks)
trainImagesFolder=rawFolder/'training_tiles'   # Cx/Sentinel_Monterrey_15x15_Rxx_Cxx.tif
trainMasksFolder=rawFolder/'training_masks'    # mask_Cx_Rxx_Cxx.tif

# ZMM boundary (16 municipalities), EPSG:6372
boundaryFile=rawFolder/'boundaries'/'zmm_boundary.gpkg'

# AGEB data
agebFile=rawFolder/'inegi'/'ageb_zmm.gpkg'                     # urban AGEB polygons of the ZMM, EPSG:6372
censusFile=rawFolder/'inegi'/'RESAGEBURB_19CSV20.csv'          # INEGI Censo 2020 by AGEB and block
conevalFile=rawFolder/'coneval'/'GRS_AGEB_NL_2020_limpio.csv'  # CONEVAL social lag 2020
lstFile=rawFolder/'lst'/'LST_ZMM_2025.tif'                     # Landsat-8 surface temperature, deg C
qgisRefFile=rawFolder/'qgis_reference'/'AGEB_ZMM_metrics_LST.gpkg'  # original QGIS result, only to compare

# Model outputs
validationFolder=processedFolder/'validation'  # out-of-fold predictions
modelsFolder=processedFolder/'models'
predictionsFolder=processedFolder/'predictions' # vegetation masks per tile and ZMM mosaics
