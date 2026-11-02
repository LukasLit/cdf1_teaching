# Grasshopper Python 3 inputs:
#   base_point: Point3d (optional; defaults to the world origin)
#   x_size: float slider (positive or negative; zero is invalid)
#   y_size: float slider (positive or negative; zero is invalid)
#   z_size: float slider (positive or negative; zero is invalid)
# Output:
#   a: box Brep

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_box(
    base_point=base_point,
    x_size=x_size,
    y_size=y_size,
    z_size=z_size,
)
