# Grasshopper Python 3 inputs:
#   start_point: Point3d (bottom vertex of the first grid cell)
#   diamond_width: float slider (horizontal diagonal / grid pitch)
#   diamond_height: float slider (vertical diagonal / grid pitch)
#   rows: integer slider (same count as the diamond-pattern component)
#   columns: integer slider (same count as the diamond-pattern component)
#   pull_point: Point3d (attractor point; distances use XY only)
#   distance_from: float slider (distance mapped to gap_near)
#   distance_to: float slider (distance mapped to gap_far; greater than distance_from)
#   gap_near: float slider (smallest gap, near the pull point)
#   gap_far: float slider (largest gap, farther from the pull point)
# Output:
#   a: row-major list of gap values; connect to diamond_pattern's gap input

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_diamond_attractor_gaps(
    start_point=start_point,
    diamond_width=diamond_width,
    diamond_height=diamond_height,
    rows=rows,
    columns=columns,
    pull_point=pull_point,
    distance_from=distance_from,
    distance_to=distance_to,
    gap_near=gap_near,
    gap_far=gap_far,
)
