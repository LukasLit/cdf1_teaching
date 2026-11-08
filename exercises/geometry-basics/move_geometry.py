# Grasshopper Python 3 inputs:
#   geometry: Geometry (single item or list of items to move)
#   start_point: Point3d (start of the translation vector)
#   end_point: Point3d (end of the translation vector)
# Output:
#   a: moved geometry; lists stay lists
#
# Set the geometry input type hint to Geometry. Connect start_point and
# end_point as Point3d inputs.

import cdf.geometry_basics as geometry_basics

a = geometry_basics.move_geometry(
    geometry=geometry,
    start_point=start_point,
    end_point=end_point,
)
