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

Licences were checked on the provider pages on 2026-11-22 (page text, not just the
download name). CC0 needs no credit; CC BY 3.0 needs the credit in the next section.

| Category | File | Original file | Source / creator | Licence (as shown on the page) |
| --- | --- | --- | --- | --- |
| bed | `models/Bed/Default/DefaultBed.rooms.usdc` | `bedSingle.obj` | Kenney, Furniture Kit, https://kenney.nl/assets/furniture-kit | CC0 1.0 (Kenney page) |
| television | `models/Television/Default/DefaultTelevision.rooms.usdc` | `televisionVintage.obj` | Kenney, Furniture Kit | CC0 1.0 (Kenney page) |
| bathtub | `models/Bathtub/Default/DefaultBathtub.rooms.usdc` | `bathtub.obj` | Kenney, Furniture Kit | CC0 1.0 (Kenney page) |
| stairs | `models/Stairs/Default/DefaultStairs.rooms.usdc` | `stairsOpenSingle.obj` | Kenney, Furniture Kit | CC0 1.0 (Kenney page) |
| toilet | `models/Toilet/Default/DefaultToilet.rooms.usdc` | `toilet.obj` | Kenney, Furniture Kit | CC0 1.0 (Kenney page) |
| washerDryer | `models/WasherDryer/Default/DefaultWasherDryer.rooms.usdc` | `dryer.obj` | Kenney, Furniture Kit | CC0 1.0 (Kenney page) |
| sink | `models/Sink/Default/DefaultSink.rooms.usdc` | `Bathroom_Sink.fbx` | Quaternius, https://poly.pizza/m/OMCJDgMUui | "Public Domain (CC0)" |
| oven | `models/Oven/Default/DefaultOven.rooms.usdc` | `Kitchen_Oven_Large.fbx` | Quaternius, https://poly.pizza/m/VNjPRwui7t | "Public Domain (CC0)" |
| refrigerator | `models/Refrigerator/Default/DefaultRefrigerator.rooms.usdc` | `Refrigirator.fbx` | CreativeTrio, https://poly.pizza/m/G2vcjG4nvK | "Public Domain (CC0)" |
| stove | `models/Stove/Default/DefaultStove.rooms.usdc` | `Stove.fbx` | CreativeTrio, https://poly.pizza/m/EwEDIUf1hQ | "Public Domain (CC0)" |
| dishwasher | `models/Dishwasher/Default/DefaultDishwasher.rooms.usdc` | `Dishwasher 1.obj` + texture | "Poly by Google", https://poly.pizza/m/4HlUpiwqtvs | **CC BY 3.0** ("Creative Commons Attribution") |
| fireplace | `models/Fireplace/Default/DefaultFireplace.rooms.usdc` | `SM_FirePlace_02.obj` | "Poly by Google", https://poly.pizza/m/fBHV3AYiitX | **CC BY 3.0** ("Creative Commons Attribution") |
| storage (cabinet) | `models/Storage/Cabinet/Cabinet.rooms.usdc` | `FileCabinet.fbx` | J-Toastie, https://poly.pizza/m/9732ObD3OY | **CC BY 3.0** ("Creative Commons Attribution") |
| storage (default) | `models/Storage/Default/DefaultStorage.rooms.usdc` | `model.obj` + `materials.mtl` | Jarlan Perez, https://poly.pizza/m/6gKdASmfB9U | **CC BY 3.0** ("Creative Commons Attribution") |

CC BY 3.0 links point to https://creativecommons.org/licenses/by/3.0/ (the pages name
the licence as "Creative Commons Attribution" and give the version only in the link).
CC0 links point to https://creativecommons.org/publicdomain/zero/1.0/.

## Credits required by CC BY 3.0

The four models below were changed by this project (converted to USD, rescaled, pivot
moved to the floor centre, materials replaced by a neutral white, dishwasher texture
removed, cabinet rotated). Keep these credits wherever the models are shown or shipped
(for example an app credits screen or a README):

- "Dishwasher" by Poly by Google, https://poly.pizza/m/4HlUpiwqtvs, licensed under CC BY 3.0
- "Fireplace" by Poly by Google, https://poly.pizza/m/fBHV3AYiitX, licensed under CC BY 3.0
- "File Cabinet" by J-Toastie, https://poly.pizza/m/9732ObD3OY, licensed under CC BY 3.0
- "Storage Shelf" by Jarlan Perez, https://poly.pizza/m/6gKdASmfB9U, licensed under CC BY 3.0

Not independently confirmed:
- The Poly Pizza pages show no link to the original Google Poly / upstream source, so
  the upstream licence status could not be cross-checked. They show a CC BY licence on
  the page itself.
- The Kenney page states the licence for the Furniture Kit as a whole but does not list its
  models. The six Kenney files come from `.obj` files whose header says "Created by Kenney
  (www.kenney.nl)" and whose names match the kit. Check that they are from the Furniture
  Kit download you used.
- This is a reading of the pages, not legal advice.

Known limitations: the file cabinet and storage shelf keep no textures (flat materials). Fridge and stove textures were not included in the downloads, so they
are grey. Stairs orientation relative to RoomPlan stairs is unverified. Front directions
were checked on a preview render only (front = +Z).

Do not add a model whose licence does not allow redistribution in this repository.
