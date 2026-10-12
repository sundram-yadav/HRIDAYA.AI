# Dataset summary

Source file: `data/z_alizadeh_sani_extension.xlsx` (UCI extention of Z-Alizadeh sani, id=411).

- Rows: **303**
- Raw columns: **59**
- Missing cells (raw): **0**
- Leakage-safe feature count: **56**

## Targets (encoded 1 = disease / stenotic)

| Target | Positive | Negative | Prevalence |
| --- | --- | --- | --- |
| CAD | 216 | 87 | 0.713 |
| LAD | 177 | 126 | 0.584 |
| LCX | 119 | 184 | 0.393 |
| RCA | 114 | 189 | 0.376 |

## Raw columns and dtypes

| Column | dtype | nunique | missing | sample values |
| --- | --- | --- | --- | --- |
| Age | int64 | 46 | 0 | 53, 67, 54, 66, 50, 55 |
| Weight | int64 | 54 | 0 | 90, 70, 54, 67, 87, 75 |
| Length | int64 | 44 | 0 | 175, 157, 164, 158, 153, 165 |
| Sex | str | 2 | 0 | Male, Fmale |
| BMI | float64 | 263 | 0 | 29.387755102040817, 28.398718000730252, 20.077334919690664, 26.83864765261977, 37.165192874535435, 24.489795918367346 |
| DM | int64 | 2 | 0 | 0, 1 |
| HTN | int64 | 2 | 0 | 1, 0 |
| Current_Smoker | int64 | 2 | 0 | 1, 0 |
| EX_Smoker | int64 | 2 | 0 | 0, 1 |
| FH | int64 | 2 | 0 | 0, 1 |
| Obesity | str | 2 | 0 | Y, N |
| CRF | str | 2 | 0 | N, Y |
| CVA | str | 2 | 0 | N, Y |
| Airway_disease | str | 2 | 0 | N, Y |
| Thyroid_Disease | str | 2 | 0 | N, Y |
| CHF | str | 2 | 0 | N, Y |
| DLP | str | 2 | 0 | Y, N |
| BP | int64 | 17 | 0 | 110, 140, 100, 118, 130, 90 |
| PR | int64 | 21 | 0 | 80, 100, 70, 50, 84, 74 |
| Edema | int64 | 2 | 0 | 0, 1 |
| Weak_Peripheral_Pulse | str | 2 | 0 | N, Y |
| Lung_rales | str | 2 | 0 | N, Y |
| Systolic_Murmur | str | 2 | 0 | N, Y |
| Diastolic_Murmur | str | 2 | 0 | N, Y |
| Typical_Chest_Pain | int64 | 2 | 0 | 0, 1 |
| Dyspnea | str | 2 | 0 | N, Y |
| Function_Class | int64 | 4 | 0 | 0, 3, 2, 1 |
| Atypical | str | 2 | 0 | N, Y |
| Nonanginal | str | 2 | 0 | N, Y |
| Exertional_CP | str | 1 | 0 | N |
| LowTH_Ang | str | 2 | 0 | N, Y |
| Q_Wave | int64 | 2 | 0 | 0, 1 |
| St_Elevation | int64 | 2 | 0 | 0, 1 |
| St_Depression | int64 | 2 | 0 | 1, 0 |
| Tinversion | int64 | 2 | 0 | 1, 0 |
| LVH | str | 2 | 0 | N, Y |
| Poor_R_Progression | str | 2 | 0 | N, Y |
| BBB | str | 3 | 0 | N, LBBB, RBBB |
| FBS | int64 | 113 | 0 | 90, 80, 85, 78, 104, 86 |
| CR | float64 | 18 | 0 | 0.7, 1.0, 1.2, 0.8, 0.9, 0.6 |
| TG | int64 | 147 | 0 | 250, 309, 103, 63, 170, 139 |
| LDL | int64 | 110 | 0 | 155, 121, 70, 55, 110, 119 |
| HDL | float64 | 47 | 0 | 30.0, 36.0, 45.0, 27.0, 50.0, 34.0 |
| BUN | int64 | 33 | 0 | 8, 30, 17, 16, 13, 12 |
| ESR | int64 | 58 | 0 | 7, 26, 10, 76, 27, 18 |
| HB | float64 | 66 | 0 | 15.6, 13.9, 13.5, 12.1, 13.2, 14.1 |
| K | float64 | 27 | 0 | 4.7, 4.4, 4.0, 4.2, 4.8, 4.3 |
| Na | int64 | 25 | 0 | 141, 156, 139, 142, 140, 128 |
| WBC | int64 | 78 | 0 | 5700, 7700, 7400, 13000, 9200, 7300 |
| Lymph | int64 | 50 | 0 | 39, 38, 18, 55, 26, 58 |
| Neut | int64 | 52 | 0 | 52, 55, 60, 72, 39, 66 |
| PLT | int64 | 135 | 0 | 261, 165, 230, 742, 274, 194 |
| EF_TTE | int64 | 11 | 0 | 50, 40, 55, 45, 25, 30 |
| Region_RWMA | int64 | 5 | 0 | 0, 4, 2, 3, 1 |
| VHD | str | 4 | 0 | N, mild, Severe, Moderate |
| LAD | str | 2 | 0 | Stenotic, Normal |
| LCX | str | 2 | 0 | Normal, Stenotic |
| RCA | str | 2 | 0 | Stenotic, Normal |
| Cath | str | 2 | 0 | CAD, Normal |

## Leakage columns (never used as inputs)

LAD, LCX, RCA (Stenotic/Normal) and Cath (CAD/Normal). No separate CAD column exists in this file.
Cath is the overall CAD status target.

## Notes

- `Exertional_CP` is constant (`N`) and is dropped.
- `Sex` uses dataset spelling `Fmale` / `Male`.
- `Region_RWMA` is an integer 0–4 echo finding, not a 3D lesion map.
- Diastolic BP is absent; pulse pressure was not engineered.
