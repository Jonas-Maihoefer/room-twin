# Furniture replacement placement diagnostic

## Finding

The displacement came from `apply_replacements()` centering the replacement on
the first placeholder mesh's raw point-bounds center. The replacement is a
sibling of the furniture prim and inherits that prim's transform, so this added
mesh-center offset is applied in the furniture's local frame a second time.
RoomPlan's placement anchor is the furniture prim origin. In the focus chair,
the proxy mesh is asymmetric around that origin: its point-bounds center is
16.823 cm below it. The replacement code copied that proxy-only offset into a
full-size chair.

The focus object is UUID `2BE035CE-5590-4D1A-A35B-0F8F1D8D3A73`, composed at
`/room/Mesh_grp/Object_grp/Chair_grp/Chair0`. Its prim origin matches the scan
translation `(0.253320, -0.252592, 0.057061) m`. Its source geometry bounds in
the prim frame have center `(0, -0.168230, 0) m`, so the former code placed the
replacement center at `(0.253320, -0.420822, 0.057061) m`. The replacement
bottom was `-0.904092 m`; the RoomPlan dimensions imply `-0.735862 m`.

## Focus chair transform evidence

- The source mesh has no additional authored mesh transform. Its point range
  has Y center `-0.168230 m` relative to the chair prim origin.
- The parent path is
  `/room/Mesh_grp/Object_grp/Chair_grp/Chair0`; transforms on `/room`,
  `/room/Mesh_grp`, `/room/Mesh_grp/Object_grp`, and
  `/room/Mesh_grp/Object_grp/Chair_grp` are identity. `Chair0` has one
  `xformOp:transform` carrying its yaw and translation.
- The chair prim's local-to-world matrix preserves its yaw and translation;
  its translation row is `(0.253320, -0.252592, 0.057061, 1)`.
- The referenced model is
  `models/Chair/Swivel_wBack_starLegs_noArms/Swivel_wBack_starLegs_noArms.rooms.usdc`,
  default prim `/Swivel_wBack_starLegs_noArms`. The asset is Y-up and
  `metersPerUnit=1`. Its native geometry bounds are
  `(-28.228163, -0.003363, -32.636364)` to
  `(28.228163, 110.807693, 30.566730)`; the bounds center is
  `(0, 55.402165, -1.034817)` in asset units. The asset root transform is
  identity; the geometry is nested below the default prim.
- The fit scale is approximately `(0.0096683, 0.0087224, 0.0095049)` and the
  fit translation is `(0, -0.483241, 0.009836) m`. The model Xform order is
  translate then scale. This centers the asset's own bounds and fits the scan
  dimensions `(0.545837, 0.966540, 0.600738) m`.
- The replacement root world transform equals the original chair prim's world
  transform. After the fix, its visible mesh bounds center in the oriented
  furniture frame is within `2 mm` of the prim origin, and its bottom is
  `-0.735862 m`, matching the scan-derived bottom.

## All six replacements

The old center column is the exact local offset used by the former code: the
first placeholder mesh's raw point-bounds center relative to its furniture
prim origin. The fixed center is measured from the composed replacement mesh in
the replacement root's oriented local frame. This frame comparison avoids
mistaking rotation-dependent world AABB centers for object placement.

| UUID (prefix) | Category | Old local center (m) | Fixed local center (m) | Fitted dimensions (m) | Bottom Y: old → fixed / expected (m) |
|---|---|---:|---:|---:|---:|
| `29e63f49` | chair | `(0, 0, 0)` | `(0, 0, 0)` | `(0.494019, 0.980086, 0.586182)` | `-0.735862 → -0.735862 / -0.735862` |
| `2be035ce` | chair | `(0, -0.168230, 0)` | `(0, 0, 0)` | `(0.545837, 0.966540, 0.600738)` | `-0.904092 → -0.735862 / -0.735862` |
| `41f7b8fb` | chair | `(0, -0.168230, 0)` | `(0, 0, 0)` | `(0.545837, 0.966540, 0.600738)` | `-0.904092 → -0.735862 / -0.735862` |
| `51ffb4a1` | shelf | `(0, 0, 0)` | `(0, 0, 0)` | `(1.084391, 1.201759, 0.387084)` | `0.021755 → 0.021755 / 0.021755` |
| `5b973e32` | table | `(0, 0, 0)` | `(0, 0, 0)` | `(1.416408, 0.787600, 0.902303)` | `-0.735862 → -0.735862 / -0.735862` |
| `ae74368d` | table | `(0, 0, 0)` | `(0, 0, 0)` | `(1.492960, 0.908733, 0.453998)` | `-0.735862 → -0.735862 / -0.735862` |

The original world AABB centers for the two affected chairs were
`(0.253320, -0.420822, 0.057061) m` and
`(-0.448658, -0.420822, 0.150765) m`. Their fixed replacement anchors are the
RoomPlan prim origins `(0.253320, -0.252592, 0.057061) m` and
`(-0.448658, -0.252592, 0.150765) m`. Rotated models can have world AABB
centers a few millimetres from their transformed local bounds center; the tests
therefore assert geometry in the object's oriented frame and check its world
pose separately.

## Validation

- Six replaced, two preserved, eight UUIDs accounted for. Issue D regenerated
  `output/issue-d-enhanced.usdz` after removing the Apple sample directory.
- A separate OpenUSD process reopened the package with the backend asset tree
  masked. All eight source furniture prim paths remained present, all six
  replacement models were packaged, and dependency resolution reported no
  unresolved assets or external dependencies.
- The CLI diagnostics report passed geometry, package, and architecture
  preservation checks. The source scan SHA-256 remained
  `198D8B344F46E9A3456F327F0A15A8AB83C0899D7B81360E9F50695820446BC6`.
- The complete backend suite ran in the Docker test image: 53 passed, zero
  skipped, with one dependency deprecation warning.
- Rendered visual review was not performed for Issue D. The numeric checks
  establish structural validity and measured placement, not rendered visual
  quality. To inspect manually, open
  `backend/output/issue-d-enhanced.usdz` in Apple Reality Composer/Quick Look
  or another USDZ viewer and compare it with `backend/testdata/room.usdz`.
