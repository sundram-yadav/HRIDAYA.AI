/** Anatomically plausible coronary paths in heart-local coordinates.
 * Adding a vessel is one object in ARTERIES.
 */
export const ARTERIES = [
  {
    id: 'lad',
    label: 'LAD',
    fullName: 'Left anterior descending',
    icon: '↓',
    points: [
      [0.02, 0.72, 0.18],
      [0.0, 0.42, 0.32],
      [0.04, 0.08, 0.28],
      [0.06, -0.38, 0.18],
      [0.04, -0.72, 0.04],
    ],
    branches: [
      [
        [0.0, 0.42, 0.32],
        [0.22, 0.28, 0.3],
        [0.28, 0.05, 0.22],
      ],
      [
        [0.04, 0.08, 0.28],
        [0.18, -0.12, 0.24],
        [0.2, -0.32, 0.14],
      ],
    ],
    stenosisT: 0.55,
  },
  {
    id: 'lcx',
    label: 'LCX',
    fullName: 'Left circumflex',
    icon: '↺',
    points: [
      [0.02, 0.72, 0.18],
      [-0.28, 0.62, 0.12],
      [-0.48, 0.38, -0.06],
      [-0.42, 0.05, -0.28],
      [-0.22, -0.22, -0.32],
    ],
    branches: [
      [
        [-0.48, 0.38, -0.06],
        [-0.38, 0.12, -0.18],
        [-0.22, -0.02, -0.22],
      ],
    ],
    stenosisT: 0.48,
  },
  {
    id: 'rca',
    label: 'RCA',
    fullName: 'Right coronary artery',
    icon: '→',
    points: [
      [0.08, 0.7, 0.12],
      [0.38, 0.58, 0.08],
      [0.52, 0.28, -0.04],
      [0.42, -0.08, -0.18],
      [0.12, -0.42, -0.22],
      [0.0, -0.55, -0.08],
    ],
    branches: [
      [
        [0.52, 0.28, -0.04],
        [0.4, 0.06, 0.12],
        [0.28, -0.18, 0.16],
      ],
    ],
    stenosisT: 0.52,
  },
];
