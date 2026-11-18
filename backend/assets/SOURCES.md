# Asset sources and licences

Every model under `models/` needs an entry here. Keep the original licence text
next to the model if the licence requires it.

## Apple RoomPlan sample models (42 files)

- Chair, Table, Sofa and Storage/Shelf models under `models/Chair`, `models/Table`,
  `models/Sofa`, `models/Storage`.
- Source: Apple's public RoomPlan "providing custom models" sample project.
- Licence: see [LICENSE.apple.txt](LICENSE.apple.txt).
- Modifications: none to the geometry; mapping follows the sample's catalog.plist.

## Added models (14)

Conversion for all of them: imported from OBJ/FBX, node transforms baked in, rescaled
uniformly to a realistic size, pivot moved to the floor centre, exported as `.usdc`
(Y-up, metres) with `UsdPreviewSurface` materials. The default prim carries no xform ops
because the replacement engine adds its own fit. The Kenney OBJ files came without
`.mtl`/colour map, so those models use plain grey/white materials.

**Licences below come from the provider's usual terms and the download names. They must
be confirmed on each download page before this is merged.**

| Category | File | Original file | Source / creator | Licence (confirm) |
| --- | --- | --- | --- | --- |
| bed | `models/Bed/Default/DefaultBed.rooms.usdc` | `bedSingle.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| television | `models/Television/Default/DefaultTelevision.rooms.usdc` | `televisionVintage.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| bathtub | `models/Bathtub/Default/DefaultBathtub.rooms.usdc` | `bathtub.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| stairs | `models/Stairs/Default/DefaultStairs.rooms.usdc` | `stairsOpenSingle.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| toilet | `models/Toilet/Default/DefaultToilet.rooms.usdc` | `toilet.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| washerDryer | `models/WasherDryer/Default/DefaultWasherDryer.rooms.usdc` | `dryer.obj` | Kenney, Furniture Kit (kenney.nl) | CC0 |
| sink | `models/Sink/Default/DefaultSink.rooms.usdc` | `Bathroom_Sink.fbx` | Quaternius (via Poly Pizza) | CC0 |
| oven | `models/Oven/Default/DefaultOven.rooms.usdc` | `Kitchen_Oven_Large.fbx` | Quaternius (via Poly Pizza) | CC0 |
| refrigerator | `models/Refrigerator/Default/DefaultRefrigerator.rooms.usdc` | `Refrigirator.fbx` | CreativeTrio (via Poly Pizza) | CC0 (confirm) |
| stove | `models/Stove/Default/DefaultStove.rooms.usdc` | `Stove.fbx` | CreativeTrio (via Poly Pizza) | CC0 (confirm) |
| dishwasher | `models/Dishwasher/Default/DefaultDishwasher.rooms.usdc` | `Dishwasher 1.obj` + texture | "Poly by Google" (via Poly Pizza) | CC-BY 3.0, **attribution required** |
| fireplace | `models/Fireplace/Default/DefaultFireplace.rooms.usdc` | `SM_FirePlace_02.obj` | "Poly by Google" (via Poly Pizza) | CC-BY 3.0, **attribution required** |
| storage (cabinet) | `models/Storage/Cabinet/Cabinet.rooms.usdc` | `FileCabinet.fbx` | J-Toastie (via Poly Pizza) | **unknown, confirm (CC0 or CC-BY?)** |
| storage (default) | `models/Storage/Default/DefaultStorage.rooms.usdc` | `model.obj` + `materials.mtl` | Jarlan Perez (via Poly Pizza) | **unknown, confirm (CC0 or CC-BY?)** |

Attribution (CC-BY): "Dishwasher" and "Fireplace" by Poly by Google, licensed CC-BY 3.0,
obtained via poly.pizza. Add the original author names and links from the download pages.

Known limitations: the file cabinet and storage shelf keep no textures (flat materials). Fridge and stove textures were not included in the downloads, so they
are grey. Stairs orientation relative to RoomPlan stairs is unverified. Front directions
were checked on a preview render only (front = +Z).

Do not merge a model whose licence does not allow redistribution in this repository.
CC0 needs no attribution. CC-BY needs the creator named.
