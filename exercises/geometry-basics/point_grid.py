# Grasshopper Python 3 inputs:
#   start_point: Point3d (optional; defaults to the world origin)
#   columns: integer slider (number of points in the X direction; minimum 1)
#   rows: integer slider (number of points in the Y direction; minimum 1)
#   x_spacing: float slider (distance between columns; greater than 0)
#   y_spacing: float slider (distance between rows; greater than 0)
# Output:
#   a: row-major list of Rhino.Geometry.Point3d

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_point_grid(
    start_point=start_point,
    columns=columns,
    rows=rows,
    x_spacing=x_spacing,
    y_spacing=y_spacing,
)
