# Grasshopper Python 3 inputs:
#   surfaces: Surface or Brep; use List Access for multiple bases
#   height: float slider (signed apex height along world Z; non-zero)
# Output:
#   a: list of closed pyramid solid Breps

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_pyramids_from_surfaces(
    surfaces=surfaces,
    height=height,
)
