# Grasshopper Python 3 inputs:
#   curves: Curve or Line inputs; use List Access for multiple curves
#   offset_distance: float slider (non-zero; planar offset distance)
#   extrusion_height: float slider (non-zero; extrusion along Z)
# Output:
#   a: extruded solid Breps

import cdf.geometry_basics as geometry_basics

a = geometry_basics.offset_loft_extrude_curves(
    curves=curves,
    offset_distance=offset_distance,
    extrusion_height=extrusion_height,
)
