# Standalone Grasshopper Python 3 script: no cdf module or external files needed.
#
# Inputs:
#   geometry: one or more geometry items (List access)
#   seed: integer random seed (Item access; defaults to 1)
# Outputs:
#   a: geometry list, for Custom Preview G
#   m: Rhino display materials, for Custom Preview M
#   material_names: assigned material name for each geometry
#
# Materials are embedded display materials for Grasshopper preview. They are
# portable with this script but do not include bitmap textures or bake materials
# onto objects in the Rhino document.

import random
import Rhino.Display as rd
from System.Drawing import Color
from Grasshopper.Kernel.Types import GH_Material


material_presets = [
    ("oak wood", (156, 101, 55), (90, 68, 46), 0.12, 0.0),
    ("walnut wood", (91, 55, 37), (75, 58, 46), 0.16, 0.0),
    ("pine wood", (194, 151, 92), (120, 101, 75), 0.1, 0.0),
    ("dark stained wood", (76, 48, 34), (82, 68, 58), 0.18, 0.0),
    ("concrete", (150, 150, 145), (80, 80, 78), 0.05, 0.0),
    ("light concrete", (190, 188, 177), (100, 98, 91), 0.05, 0.0),
    ("terrazzo", (207, 198, 180), (110, 106, 98), 0.08, 0.0),
    ("marble", (220, 216, 205), (170, 170, 165), 0.25, 0.0),
    ("red brick", (151, 67, 48), (86, 54, 46), 0.06, 0.0),
    ("steel", (135, 150, 165), (220, 225, 232), 0.75, 0.0),
    ("brushed aluminum", (185, 190, 195), (235, 238, 242), 0.72, 0.0),
    ("copper", (184, 105, 66), (230, 175, 130), 0.65, 0.0),
    ("brass", (181, 145, 65), (235, 210, 145), 0.68, 0.0),
    ("bronze", (125, 86, 54), (190, 155, 110), 0.62, 0.0),
    ("gold", (212, 170, 55), (255, 230, 150), 0.8, 0.0),
    ("black plastic", (42, 44, 47), (150, 155, 165), 0.42, 0.0),
    ("blue plastic", (55, 105, 190), (210, 220, 245), 0.45, 0.0),
    ("red ceramic", (165, 48, 44), (225, 190, 185), 0.58, 0.0),
    ("porcelain", (235, 233, 225), (245, 245, 240), 0.62, 0.0),
    ("glass", (130, 195, 220), (220, 240, 250), 0.75, 0.55),
]


def create_preview_material(preset):
    name, diffuse_rgb, specular_rgb, shine, transparency = preset
    display_material = rd.DisplayMaterial()
    display_material.Diffuse = Color.FromArgb(
        diffuse_rgb[0], diffuse_rgb[1], diffuse_rgb[2]
    )
    display_material.Specular = Color.FromArgb(
        specular_rgb[0], specular_rgb[1], specular_rgb[2]
    )
    display_material.Shine = shine
    display_material.Transparency = transparency
    return name, GH_Material(display_material)


items = [] if geometry is None else list(geometry)
random_seed = 1 if seed is None else int(seed)
rng = random.Random(random_seed)
material_library = [create_preview_material(preset) for preset in material_presets]

assignments = []
while len(assignments) < len(items):
    batch = list(material_library)
    rng.shuffle(batch)
    assignments.extend(batch)

chosen_materials = assignments[:len(items)]
a = items
m = [material for name, material in chosen_materials]
material_names = [name for name, material in chosen_materials]
