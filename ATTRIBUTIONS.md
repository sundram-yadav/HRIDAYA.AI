# Attributions and licenses

## Dataset

Alizadehsani, R., Roshanzamir, M., & Sani, Z. (2013). *Extention of
Z-Alizadeh sani dataset*. UCI Machine Learning Repository.
https://doi.org/10.24432/C5461K

UCI describes this extension as 303 patients with 59 fields and explicitly
warns that the angiography labels (`LAD`, `LCX`, `RCA`, `Cath`) must not be
leaked into model inputs. The dataset file is kept local and is not redistributed
by this repository. The UCI metadata API did not provide a dataset-license
field; verify the current dataset terms and obtain any needed permission before
redistributing the source data.

## 3D heart asset

No external heart model is included or used. The dashboard generates its
procedural heart mesh and coronary paths in project code. If a GLB is added to
`frontend/public/models/heart.glb`, record its author, original source URL, and
license here before publishing it.

## Primary software dependencies

License names below refer to the upstream project/package metadata; see each
upstream source for complete notices and its transitive dependencies.

| Component | Upstream | License |
| --- | --- | --- |
| React / React DOM | https://github.com/facebook/react | MIT |
| Three.js | https://github.com/mrdoob/three.js | MIT |
| React Three Fiber | https://github.com/pmndrs/react-three-fiber | MIT |
| Drei | https://github.com/pmndrs/drei | MIT |
| Vite / React plugin | https://github.com/vitejs/vite | MIT |
| Recharts | https://github.com/recharts/recharts | MIT |
| FastAPI | https://github.com/fastapi/fastapi | MIT |
| Pydantic | https://github.com/pydantic/pydantic | MIT |
| NumPy | https://github.com/numpy/numpy | BSD-3-Clause |
| pandas | https://github.com/pandas-dev/pandas | BSD-3-Clause |
| scikit-learn | https://github.com/scikit-learn/scikit-learn | BSD-3-Clause |
| XGBoost | https://github.com/dmlc/xgboost | Apache-2.0 |
| SHAP | https://github.com/shap/shap | MIT |
| Matplotlib | https://github.com/matplotlib/matplotlib | Matplotlib license |

This repository does not yet declare a license for the project-authored code.
The maintainer must choose and add a root `LICENSE` before public redistribution.
