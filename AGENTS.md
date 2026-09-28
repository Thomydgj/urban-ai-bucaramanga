# Urban AI Bucaramanga — Project Instructions

## 1. Project Overview

Urban AI Bucaramanga is an academic software engineering project that develops a web-based platform for urban analysis using remote sensing, geospatial data, machine learning, and artificial intelligence.

The main study area is Bucaramanga, Santander, Colombia.

The platform must allow users to:

1. Visualize urban geospatial information.
2. Analyze NDVI, NDBI, and LST.
3. Generate interpretable urban diagnostics.
4. Produce data-supported urban recommendations.
5. Generate conceptual before/after visual scenarios.
6. Analyze uploaded images using computer vision to identify urban land-cover categories such as vegetation, built-up areas, and roads.

The project has a 15-day MVP deadline. Functionality and reliability have priority over unnecessary complexity.

---

## 2. Core Engineering Principles

### 2.1 MVP First

Always prioritize:

1. A working feature.
2. A testable feature.
3. A documented feature.
4. Only then additional sophistication.

Do not introduce complex architecture, machine learning models, services, or dependencies unless they provide clear value to the MVP.

### 2.2 Scientific Traceability

Any value derived from satellite data must have a traceable origin.

Never fabricate:

- NDVI values.
- NDBI values.
- LST values.
- geographic coordinates.
- areas.
- percentages.
- model metrics.
- recommendations presented as data-driven conclusions.

If data is unavailable, explicitly represent it as unavailable.

### 2.3 Explainability

Urban recommendations must be explainable using measurable indicators.

Do not allow a generative AI model to invent unsupported urban conclusions.

Recommendations should be traceable to variables such as:

- NDVI
- NDBI
- LST
- vegetation coverage
- built-up coverage
- spatial distribution
- other explicitly documented variables

### 2.4 Scientific vs. Generative Outputs

Keep scientific analysis separate from generative visualization.

Scientific analysis includes:

- NDVI
- NDBI
- LST
- segmentation metrics
- geographic measurements
- statistical analysis

Generative visualization includes:

- conceptual urban scenarios
- before/after illustrations
- visual representations of proposed interventions

A generated image must never be presented as a physically accurate simulation unless a validated simulation model is actually being used.

---

## 3. Geospatial Principles

### 3.1 Coordinate Reference Systems

Always explicitly define the CRS of geospatial datasets.

Never assume that two datasets use the same CRS.

Before spatial operations:

1. Inspect CRS.
2. Transform CRS when necessary.
3. Document the transformation.

### 3.2 Raster Data

Raster operations must preserve:

- CRS
- transform
- resolution
- dimensions
- nodata information

Do not silently resample or reproject raster datasets.

When resampling is necessary, explicitly document:

- source resolution
- target resolution
- resampling method
- reason for resampling

### 3.3 NDVI

NDVI must be calculated using the appropriate near-infrared and red bands for the selected satellite sensor.

The implementation must document:

- satellite/source
- bands
- acquisition date
- cloud filtering
- mathematical formula
- preprocessing

Standard NDVI:

NDVI = (NIR - Red) / (NIR + Red)

### 3.4 NDBI

NDBI must be calculated using the appropriate SWIR and NIR bands for the selected satellite sensor.

The implementation must document:

- satellite/source
- bands
- acquisition date
- preprocessing

Standard NDBI:

NDBI = (SWIR - NIR) / (SWIR + NIR)

### 3.5 LST

Land Surface Temperature must use an appropriate thermal satellite product or a documented retrieval methodology.

Never calculate physically meaningful LST from an ordinary RGB photograph.

LST results must document:

- satellite/source
- product
- acquisition date
- units
- preprocessing
- quality/cloud filtering

---

## 4. Computer Vision Module

The computer vision module is intended to analyze uploaded images.

The initial target is semantic segmentation or equivalent pixel-level classification of:

- vegetation
- built-up areas
- roads
- other/unknown areas

The system should produce:

- segmented image
- pixel or area proportions
- category statistics
- confidence information when available

Do not claim that RGB imagery alone provides physical LST measurements.

If an LST-related estimation model is introduced in the future, it must clearly identify:

- input variables
- training data
- target variable
- assumptions
- uncertainty
- validation methodology

---

## 5. Machine Learning Principles

Prefer established pretrained models or transfer learning when appropriate.

Do not train large models from scratch unless there is a clear academic or engineering reason.

Every trained model must document:

- dataset
- train/validation/test split
- preprocessing
- architecture
- hyperparameters
- metrics
- limitations

Never evaluate a model on data that was used for training.

Do not report accuracy without defining the evaluation dataset.

For segmentation, consider metrics such as:

- IoU
- Dice/F1
- precision
- recall

---

## 6. Recommendation Engine

Recommendations must be deterministic or explainable whenever possible.

The recommendation engine should expose:

- detected condition
- supporting indicators
- recommendation
- rationale

Example conceptual structure:

condition -> indicators -> recommendation -> rationale

Do not use an LLM as the sole source of truth for quantitative urban recommendations.

---

## 7. Backend

The backend will use Python and FastAPI unless there is a documented reason to change.

Backend responsibilities:

- API endpoints
- validation
- geospatial analysis orchestration
- machine learning inference
- recommendation logic
- persistence
- error handling

Do not put business logic directly inside API route handlers when it can be placed in a service/module.

---

## 8. Frontend

The frontend will use React and TypeScript.

Frontend responsibilities:

- map visualization
- layer controls
- statistics
- charts
- image upload
- segmentation visualization
- recommendations
- scenario visualization

Do not duplicate backend scientific calculations in the frontend.

The frontend should consume backend results through documented APIs.

---

## 9. Data Architecture

Separate:

- raw data
- processed data
- application data
- model artifacts
- source code

Never modify raw datasets directly.

Recommended structure:

data/
├── raw/
├── interim/
└── processed/

Large datasets and model weights must not be committed to Git unless explicitly required.

---

## 10. Security

Never commit:

- API keys
- passwords
- access tokens
- Earth Engine credentials
- private credentials
- secrets

Use environment variables.

Example:

.env

The repository must contain:

.env.example

with variable names but no real secrets.

---

## 11. Python

The project uses Python 3.12.

Always create and use a project-specific virtual environment.

Preferred Windows setup:

py -3.12 -m venv .venv

Dependencies must be explicitly declared.

Do not rely on globally installed Python packages.

---

## 12. Testing

Critical logic must have tests.

At minimum, test:

- NDVI calculations
- NDBI calculations
- recommendation rules
- API validation
- segmentation result processing

Tests must be deterministic whenever possible.

---

## 13. Code Quality

Prefer:

- small functions
- descriptive names
- type hints
- clear error handling
- modular architecture
- comments explaining why, not obvious syntax

Avoid:

- unnecessary abstractions
- duplicated logic
- giant functions
- hard-coded paths
- hard-coded credentials
- unexplained magic numbers

---

## 14. Dependencies

Do not install a new dependency merely because it is convenient.

Before adding a dependency:

1. Verify that it is necessary.
2. Check whether an existing dependency already solves the problem.
3. Prefer mature and well-maintained libraries.
4. Document important dependencies.

---

## 15. Git

Use small, meaningful commits.

Preferred format:

feat: add NDVI calculation
feat: add satellite data service
fix: correct raster CRS handling
test: add NDVI calculation tests
docs: update data methodology

Never commit:

- secrets
- virtual environments
- large raw datasets
- temporary files
- generated caches

---

## 16. Codex Behavior

Before modifying the project:

1. Inspect the repository.
2. Read AGENTS.md.
3. Understand the existing architecture.
4. Prefer minimal changes.
5. Do not rewrite unrelated code.
6. Explain important architectural decisions.
7. Run relevant tests after modifications.
8. Report failures instead of hiding them.

When requirements are ambiguous, choose the simplest implementation consistent with the MVP and clearly state the assumption.

Never fabricate successful execution, test results, data, or metrics.

---

## 17. Project Priorities

Priority order:

1. Functional MVP.
2. Correct geospatial analysis.
3. Reproducibility.
4. Explainability.
5. Testing.
6. User experience.
7. Advanced machine learning.
8. Experimental features.

A simple working feature is preferable to an advanced incomplete feature.

---

## 18. Current MVP

The first complete MVP should support:

1. Bucaramanga map.
2. Study-area selection.
3. NDVI visualization.
4. NDBI visualization.
5. LST visualization.
6. Basic statistics.
7. Explainable urban diagnosis.
8. Data-supported recommendations.
9. Conceptual before/after scenario.
10. Image upload.
11. Urban land-cover segmentation.
12. Basic area/category statistics.

---

## 19. Academic Integrity

This is an academic project.

The system must distinguish clearly between:

- measured data
- calculated indicators
- model predictions
- recommendations
- generated visualizations

Do not present generated or estimated information as measured ground truth.

All external datasets, methodologies, and models must be documented and properly cited in the project documentation.