# Grasshopper Python 3 inputs:
#   length: float slider (distance along the travel direction)
#   amplitude: float slider (wave height)
#   wavelength: float slider (distance per complete cycle)
#   direction: Vector input (travel direction; default X)
#   wave_direction: Vector input (oscillation direction; default Y)
#   start_point: Point input (optional; defaults to the world origin)
#   phase: float slider (phase shift in radians)
#   sample_count: integer slider (curve smoothness; minimum 3)
# Output:
#   a: interpolated Rhino.Geometry.NurbsCurve

import cdf.geometry_basics as geometry_basics

a = geometry_basics.create_sine_curve(
    length=length,
    amplitude=amplitude,
    wavelength=wavelength,
    direction=direction,
    wave_direction=wave_direction,
    start_point=start_point,
    phase=phase,
    sample_count=sample_count,
)
