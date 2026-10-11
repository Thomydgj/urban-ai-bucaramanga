# Urban AI Bucaramanga

## Sistema de análisis geoespacial y priorización urbana mediante datos satelitales y aprendizaje automático

Urban AI Bucaramanga es un proyecto de análisis geoespacial orientado a identificar y caracterizar zonas urbanas con condiciones ambientales asociadas a una mayor prioridad de intervención.

El sistema integra información raster de **NDVI**, **NDBI** y **LST**, construye variables derivadas, analiza patrones espaciales, genera un índice de prioridad urbana y utiliza un modelo **Random Forest** para reproducir la clasificación obtenida.

El resultado final es una capa geoespacial de prioridad urbana, acompañada de mapas, estadísticas, validaciones y archivos preparados para análisis posterior.

---

## 1. Objetivo

Construir un pipeline reproducible capaz de:

1. Procesar información raster ambiental.
2. Homogeneizar la resolución y extensión espacial.
3. Integrar NDVI, NDBI y LST.
4. Construir un dataset espacial de características urbanas.
5. Explorar las relaciones entre las variables.
6. Identificar patrones mediante clustering.
7. Construir un `priority_score`.
8. Identificar el 10% de observaciones con mayor prioridad.
9. Analizar espacialmente las zonas prioritarias.
10. Entrenar un modelo Random Forest.
11. Generar predicciones espaciales.
12. Exportar una capa geográfica final.
13. Validar la consistencia de todo el pipeline.

---

## 2. Variables principales

### NDVI

El **Normalized Difference Vegetation Index (NDVI)** representa la presencia y vigor relativo de vegetación.

Valores relativamente altos indican una mayor señal de vegetación.

En el proyecto se utiliza como componente ambiental asociado a las condiciones de cobertura vegetal.

### NDBI

El **Normalized Difference Built-up Index (NDBI)** representa la señal relativa asociada a superficies construidas.

Valores relativamente altos se interpretan como una mayor presencia de superficies construidas.

### LST

La **Land Surface Temperature (LST)** representa la temperatura de la superficie terrestre.

En este proyecto se utiliza en grados Celsius.

---

## 3. Datos raster

Los datos iniciales se encuentran en:

```text
data/raw/
```

Principales archivos:

```text
urban_ai_bucaramanga_ndvi.tif
urban_ai_bucaramanga_ndbi.tif
urban_ai_bucaramanga_lst.tif
```

Los raster NDVI y NDBI presentan inicialmente:

```text
1379 × 2218
EPSG:4326
```

LST presenta:

```text
740 × 460
EPSG:4326
```

Para permitir el análisis conjunto, los raster fueron alineados a una cuadrícula común de:

```text
740 × 460
EPSG:4326
```

Los raster alineados se almacenan en:

```text
data/processed/
```

---

## 4. Construcción del dataset

A partir de los raster alineados se construyó:

```text
data/processed/urban_features.csv
```

El dataset contiene:

```text
x
y
ndvi
ndbi
lst
vegetation_signal
built_signal
```

Se obtuvieron:

```text
173,656 observaciones válidas
```

La integración espacial fue realizada utilizando únicamente observaciones donde las variables ambientales requeridas estaban disponibles.

---

## 5. Análisis exploratorio

El análisis exploratorio permitió evaluar:

- valores nulos;
- estadísticas descriptivas;
- distribución de las variables;
- relaciones entre NDVI, NDBI y LST;
- correlaciones.

Las correlaciones obtenidas fueron:

| Relación | Correlación |
|---|---:|
| NDVI – NDBI | -0.9479 |
| NDVI – LST | -0.7397 |
| NDBI – LST | 0.7864 |

Estos valores describen relaciones fuertes dentro del conjunto analizado.

No deben interpretarse automáticamente como relaciones causales.

Los resultados gráficos se almacenan en:

```text
data/processed/analysis/
```

---

## 6. Clustering urbano

Se evaluaron diferentes cantidades de clusters utilizando silhouette score.

Se analizaron:

```text
k = 2 ... 8
```

Los resultados identificaron:

```text
k = 2
silhouette = 0.6372
```

Los dos grupos presentan perfiles diferenciados.

### Cluster 0

```text
Observaciones: 135,602
NDVI medio:     0.7673
NDBI medio:    -0.2571
LST media:     30.37 °C
```

### Cluster 1

```text
Observaciones: 38,054
NDVI medio:     0.2420
NDBI medio:     0.0895
LST media:     39.47 °C
```

El segundo grupo presenta simultáneamente menor NDVI, mayor NDBI y mayor LST.

Los resultados espaciales se almacenan en:

```text
data/processed/analysis/
```

---

## 7. Priority Score

Se construyó un índice compuesto denominado:

```text
priority_score
```

El índice combina las señales ambientales utilizadas por el proyecto para identificar observaciones con características asociadas a mayor prioridad.

El percentil 90 fue utilizado como umbral inicial para identificar el grupo de alta prioridad:

```text
P90 = 0.628459
```

Esto produjo:

```text
17,366 observaciones
10.00%
```

La validación mostró diferencias claras entre el grupo P90 y el resto:

| Variable | P90 | Resto |
|---|---:|---:|
| NDVI | 0.1171 | 0.7117 |
| NDBI | 0.1771 | -0.2210 |
| LST | 41.81 °C | 31.32 °C |
| Priority Score | 0.6904 | 0.2775 |

---

## 8. Análisis espacial

Las observaciones P90 fueron agrupadas espacialmente para identificar zonas de concentración.

Se identificaron:

```text
790 zonas espaciales
```

La mayor concentración alcanzó:

```text
64 observaciones
```

Las zonas con mayor prioridad presentan, en general, una combinación de:

- menor NDVI;
- mayor NDBI;
- mayor LST;
- mayor priority score.

Las capas espaciales se almacenan en:

```text
data/processed/analysis/
```

---

## 9. Modelamiento

Se construyó un dataset específico para aprendizaje automático:

```text
data/processed/modeling/urban_model_dataset.csv
```

Variables predictoras:

```text
x
y
ndvi
ndbi
lst
vegetation_signal
built_signal
```

Variable objetivo:

```text
high_priority
```

Distribución:

```text
Clase 0: 156,290
Clase 1:  17,366
```

La proporción es aproximadamente:

```text
90% / 10%
```

---

## 10. Random Forest

Se utilizó:

```text
RandomForestClassifier
```

con:

```text
300 árboles
random_state = 42
```

La importancia de variables obtenida fue:

| Variable | Importancia |
|---|---:|
| vegetation_signal | 0.265629 |
| ndvi | 0.260437 |
| built_signal | 0.189790 |
| ndbi | 0.145520 |
| lst | 0.119048 |
| y | 0.015846 |
| x | 0.003730 |

El modelo fue almacenado en:

```text
data/processed/modeling/urban_priority_model.joblib
```

---

## 11. Evaluación del modelo

El conjunto de datos fue dividido en:

```text
Train: 138,924
Test:   34,732
```

Resultados:

| Métrica | Resultado |
|---|---:|
| Accuracy | 0.998042 |
| Precision | 0.982705 |
| Recall | 0.997984 |
| F1 | 0.990286 |
| ROC-AUC | 0.999976 |

Estos valores indican una reproducción muy cercana de la clasificación objetivo dentro del conjunto de evaluación.

### Consideración metodológica

Es importante interpretar estas métricas correctamente.

La variable objetivo `high_priority` fue construida a partir del `priority_score`, y el modelo utiliza como predictores las mismas variables ambientales que participan en la construcción de dicha priorización.

Por lo tanto, estas métricas **no representan una validación independiente de impactos urbanos reales**.

Representan principalmente la capacidad del Random Forest para reproducir la regla de priorización definida por el proyecto.

Una validación externa requeriría datos independientes, por ejemplo:

- mediciones ambientales de campo;
- registros urbanos;
- infraestructura;
- indicadores socioambientales;
- observaciones temporales independientes;
- datos de referencia territorial.

---

## 12. Predicción espacial

El modelo generó probabilidades de prioridad para las observaciones espaciales.

Resultado:

```text
Observaciones: 173,656
Probabilidad mínima: 0.000000
Probabilidad máxima: 1.000000
Probabilidad media: 0.102037
```

Clasificación:

```text
Baja prioridad: 156,223
Alta prioridad:  17,433
```

La capa espacial fue exportada como:

```text
urban_model_predictions.gpkg
urban_model_predictions.geojson
```

---

## 13. Predicción raster

La probabilidad de prioridad fue proyectada nuevamente sobre la cuadrícula raster.

Raster de referencia:

```text
740 × 460
340,400 píxeles
```

Predicciones disponibles:

```text
173,656
```

NoData:

```text
166,744
```

Cobertura:

```text
51.02%
```

Archivos:

```text
urban_priority_probability.tif
urban_priority_class.tif
```

---

## 14. Validación espacial del modelo

La validación espacial obtuvo:

| Métrica | Resultado |
|---|---:|
| Accuracy | 0.999534 |
| Precision | 0.995755 |
| Recall | 0.999597 |
| F1 | 0.997672 |

Matriz espacial:

```text
True Positive:   17,359
True Negative:  156,216
False Positive:      74
False Negative:       7
```

Coincidencia:

```text
99.9534%
```

Esta validación confirma la consistencia de la predicción con respecto a la clasificación objetivo utilizada en el pipeline.

---

## 15. Capa final

La capa final contiene:

```text
173,656 observaciones
```

y cuatro niveles:

```text
MUY_ALTA
ALTA
MEDIA
BAJA
```

Distribución final:

| Nivel | Observaciones | Porcentaje |
|---|---:|---:|
| MUY_ALTA | 17,314 | 9.9703% |
| ALTA | 120 | 0.0691% |
| MEDIA | 486 | 0.2799% |
| BAJA | 155,736 | 89.6807% |

La capa final está disponible como:

```text
urban_ai_final_priority.gpkg
urban_ai_final_priority.geojson
urban_ai_final_priority.csv
```

---

## 16. Perfil de las zonas MUY_ALTA

Las zonas clasificadas como `MUY_ALTA` presentan:

```text
Probabilidad media: 0.997891
NDVI medio:         0.116912
NDBI medio:         0.177294
LST media:          41.813749 °C
```

Este perfil representa la combinación de condiciones que el sistema considera de mayor prioridad bajo la metodología definida.

---

## 17. Validación final del proyecto

La validación final verificó:

```text
CSV ↔ GeoPackage
```

Resultado:

```text
173,656 ↔ 173,656
```

Además:

```text
[OK] Categorías completas
[OK] Distribución consistente
[OK] Priority probability consistente
[OK] CRS definido
[OK] Geometrías válidas
[OK] Sin valores nulos
```

CRS:

```text
EPSG:4326
```

Extensión espacial:

```text
Longitud:
-73.170340 → -73.046642

Latitud:
7.067361 → 7.266517
```

Archivo de validación:

```text
data/processed/modeling/final_project_validation.csv
```

---

## 18. Principales productos

### Análisis

```text
data/processed/analysis/
```

Incluye:

- clustering;
- análisis espacial;
- priority score;
- mapas de prioridad;
- resúmenes estadísticos;
- validaciones.

### Modelamiento

```text
data/processed/modeling/
```

Incluye:

- dataset de modelamiento;
- modelo Random Forest;
- métricas;
- predicciones;
- predicciones raster;
- validaciones;
- capa final;
- mapas finales.

---

## 19. Reproducibilidad

Activar el entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

Los módulos pueden ejecutarse mediante:

```powershell
python -m geospatial.processing.raster_inspector
python -m geospatial.processing.feature_builder

python -m geospatial.analysis.exploratory_analysis
python -m geospatial.analysis.urban_clustering
python -m geospatial.analysis.spatial_cluster_analysis
python -m geospatial.analysis.urban_priority
python -m geospatial.analysis.priority_mapping
python -m geospatial.analysis.priority_validation
python -m geospatial.analysis.priority_summary
python -m geospatial.analysis.priority_geospatial
python -m geospatial.analysis.priority_geospatial_check
python -m geospatial.analysis.priority_final_summary

python -m geospatial.modeling.model_dataset
python -m geospatial.modeling.model_train
python -m geospatial.modeling.model_evaluation
python -m geospatial.modeling.model_prediction
python -m geospatial.modeling.model_spatial_prediction
python -m geospatial.modeling.model_raster_prediction
python -m geospatial.modeling.model_raster_validation
python -m geospatial.modeling.model_summary
python -m geospatial.modeling.final_priority_layer
python -m geospatial.modeling.final_priority_map
python -m geospatial.modeling.final_project_validation
```

---

## 20. Limitaciones

El sistema debe interpretarse como una herramienta de **análisis y priorización espacial**, no como una medición directa de vulnerabilidad urbana ni como una recomendación automática de intervención.

Entre las principales limitaciones:

1. Las variables ambientales proceden de información raster y dependen de su resolución espacial y calidad.
2. NDVI, NDBI y LST representan dimensiones específicas del territorio y no describen por sí solas todas las condiciones urbanas.
3. El `priority_score` es una construcción metodológica del proyecto.
4. El modelo Random Forest aprende principalmente a reproducir dicha construcción.
5. Las métricas del modelo no constituyen una validación independiente contra observaciones externas.
6. El análisis representa las condiciones contenidas en los datos utilizados y no necesariamente su evolución temporal.
7. Se requiere información externa para evaluar impactos urbanos reales y apoyar decisiones operativas.

---

## 21. Trabajo futuro

El proyecto puede extenderse incorporando:

- datos socioeconómicos;
- densidad poblacional;
- cobertura arbórea;
- infraestructura urbana;
- red vial;
- equipamientos;
- cuerpos de agua;
- datos meteorológicos;
- series temporales satelitales;
- imágenes de mayor resolución;
- indicadores de vulnerabilidad;
- datos de campo;
- validación temporal;
- modelos espaciales y temporales más avanzados.

Una siguiente versión podría utilizar datos independientes como variable objetivo para transformar el problema desde la reproducción de un índice hacia una predicción validada externamente.

---

## 22. Conclusión

Urban AI Bucaramanga implementa un pipeline reproducible para transformar información ambiental raster en una representación espacial de prioridad urbana.

La integración de NDVI, NDBI y LST permitió identificar patrones diferenciados entre zonas con mayor y menor prioridad según la metodología definida.

El sistema produjo una capa final de **173,656 observaciones**, con geometrías válidas, CRS definido y consistencia entre los formatos tabular y espacial.

La clasificación final identifica **17,314 observaciones MUY_ALTA**, equivalentes al **9.97%** del conjunto analizado.

El resultado principal del proyecto es una infraestructura geoespacial reproducible que permite explorar, visualizar y analizar espacialmente las zonas identificadas como prioritarias.

La interpretación de estos resultados debe realizarse conjuntamente con información territorial independiente antes de utilizarlos como base para decisiones de intervención urbana.