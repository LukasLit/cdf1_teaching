# Grasshopper Python 3 inputs:
#   start_point: Point3d (start of the full line)
#   end_point: Point3d (end of the full line)
#   dash_length: float (slider; length of each dash)
#   gap_length: float (slider; space between dashes)
# Output:
#   a: list of dashed Rhino.Geometry.Line objects

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_dashed_line(
    start_point=start_point,
    end_point=end_point,
    dash_length=dash_length,
    gap_length=gap_length,
)
