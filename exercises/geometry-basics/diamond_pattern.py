# Grasshopper Python 3 inputs:
#   start_point: Point3d (bottom vertex of the first grid cell)
#   diamond_width: float slider (horizontal diagonal / grid pitch)
#   diamond_height: float slider (vertical diagonal / grid pitch)
#   gap: float slider or list of per-diamond gaps (set to List Access for the list)
#   rows: integer slider (number of diamond rows; minimum 1)
#   columns: integer slider (number of diamond columns; minimum 1)
# Output:
#   a: list of planar diamond Breps

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_diamond_pattern(
    start_point=start_point,
    diamond_width=diamond_width,
    diamond_height=diamond_height,
    gap=gap,
    rows=rows,
    columns=columns,
)
