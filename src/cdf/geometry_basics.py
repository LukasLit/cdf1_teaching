"""
Geometry basics -- reusable Rhino.Geometry functions for Grasshopper.

Adding a new function with Copilot
-----------------------------------
1. Open this file and select this chat model, then ask Copilot something like:
   "Add a function here, all in Rhino geometry, that builds a <your shape/idea>.
   Follow the same style as create_cone / create_fractal_tree (defaults for
   optional inputs, a docstring listing params, return a Rhino.Geometry object)."
2. Once the function is added, ask Copilot:
   "Give me the Python code to use this function in a Grasshopper GHPython 3
   component, importing it from computational_design_and_fabrication."
3. Copy the snippet Copilot gives you into a GHPython component, wire up the
   inputs as sliders/panels, and set the output variable (e.g. `a`).
"""

import math
import Rhino.Geometry as rg

def create_cone(base_point=None, height=10.0, radius=5.0, cap_bottom=True):
    """
    Build a cone as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the cone's base circle
    height     : float -- cone height along the base plane's normal (Z by default)
    radius     : float -- base circle radius
    cap_bottom : bool  -- whether to cap the base circle (closed vs open cone)

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    plane = rg.Plane(base_point, rg.Vector3d.ZAxis)
    cone = rg.Cone(plane, height, radius)
    return cone.ToBrep(cap_bottom)


def create_box(base_point=None, x_size=10.0, y_size=10.0, z_size=10.0):
    """
    Build a world-aligned box from a reference corner as a Brep.

    base_point : Rhino.Geometry.Point3d -- reference corner (origin by default)
    x_size     : float -- signed extent along the X axis
    y_size     : float -- signed extent along the Y axis
    z_size     : float -- signed extent along the Z axis

    Negative sizes extend in the negative world-axis direction. Sizes must be
    non-zero because a zero extent cannot form a solid box.

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)
    if not isinstance(base_point, rg.Point3d):
        raise TypeError("base_point must be a Rhino.Geometry.Point3d.")

    if x_size is None:
        x_size = 10.0
    if y_size is None:
        y_size = 10.0
    if z_size is None:
        z_size = 10.0

    for name, size in (
        ("x_size", x_size),
        ("y_size", y_size),
        ("z_size", z_size),
    ):
        if not math.isfinite(size) or size == 0:
            raise ValueError("{} must be a finite, non-zero number.".format(name))

    box_origin = base_point + rg.Vector3d(
        min(x_size, 0.0),
        min(y_size, 0.0),
        min(z_size, 0.0),
    )
    plane = rg.Plane(box_origin, rg.Vector3d.ZAxis)
    box = rg.Box(
        plane,
        rg.Interval(0.0, abs(x_size)),
        rg.Interval(0.0, abs(y_size)),
        rg.Interval(0.0, abs(z_size)),
    )
    return box.ToBrep()


def _preview_geometry_items(geometry):
    if isinstance(geometry, (list, tuple)):
        return list(geometry)
    return [geometry]


def _preview_geometry_center(geometry):
    if geometry is None:
        raise ValueError("geometry items must not be None.")

    original_type = type(geometry).__name__
    visited = set()
    while geometry is not None and id(geometry) not in visited:
        visited.add(id(geometry))

        if isinstance(geometry, rg.Point3d):
            return geometry
        if isinstance(geometry, rg.Point):
            return geometry.Location
        if isinstance(geometry, rg.Line):
            return geometry.PointAt(0.5)

        get_bounding_box = getattr(geometry, "GetBoundingBox", None)
        if callable(get_bounding_box):
            bounding_box = get_bounding_box(True)
            break

        bounding_box = getattr(geometry, "BoundingBox", None)
        if bounding_box is not None:
            break

        script_variable = getattr(geometry, "ScriptVariable", None)
        if callable(script_variable):
            unwrapped = script_variable()
            if unwrapped is not None and unwrapped is not geometry:
                geometry = unwrapped
                continue

        unwrapped = getattr(geometry, "Value", None)
        if unwrapped is not None and unwrapped is not geometry:
            geometry = unwrapped
            continue

        raise TypeError(
            "Each item must be Rhino geometry with a bounding box; received "
            "{}. Set the Grasshopper geometry input type hint to Geometry "
            "(or its specific geometry type).".format(original_type)
        )
    else:
        raise TypeError(
            "Could not unwrap Grasshopper geometry item of type {}.".format(
                original_type
            )
        )

    if not bounding_box.IsValid:
        raise ValueError("Each geometry item must have a valid bounding box.")
    return bounding_box.Center


def _interpolate_preview_color(start_color, end_color, factor):
    from System.Drawing import Color

    return Color.FromArgb(
        round(start_color.A + (end_color.A - start_color.A) * factor),
        round(start_color.R + (end_color.R - start_color.R) * factor),
        round(start_color.G + (end_color.G - start_color.G) * factor),
        round(start_color.B + (end_color.B - start_color.B) * factor),
    )


def colors_by_distance(
    geometry,
    attractor_point,
    near_color=None,
    far_color=None,
    distance=10.0,
):
    """
    Create one preview color per geometry item based on distance to a point.

    geometry       : Rhino geometry item or list of geometry items
    attractor_point : Rhino.Geometry.Point3d -- point used for the distance field
    near_color     : System.Drawing.Color -- color at the attractor point
    far_color      : System.Drawing.Color -- color at or beyond distance
    distance       : float -- distance over which the colors transition

    Distances are measured in 3D from each item's bounding-box center.
    Colors are interpolated linearly from near_color at the attractor to
    far_color at the given distance, then clamped to far_color beyond it.
    Defaults are yellow near and red far.
    """
    from System.Drawing import Color

    if not isinstance(attractor_point, rg.Point3d):
        raise TypeError("attractor_point must be a Rhino.Geometry.Point3d.")
    if distance is None or not math.isfinite(distance) or distance <= 0:
        raise ValueError("distance must be a finite number greater than zero.")
    distance_limit = distance
    if near_color is None:
        near_color = Color.Yellow
    if far_color is None:
        far_color = Color.Red
    if not isinstance(near_color, Color) or not isinstance(far_color, Color):
        raise TypeError("near_color and far_color must be System.Drawing.Color values.")

    colors = []
    for item in _preview_geometry_items(geometry):
        center = _preview_geometry_center(item)
        item_distance = center.DistanceTo(attractor_point)
        blend = min(1.0, max(0.0, item_distance / distance_limit))
        colors.append(_interpolate_preview_color(near_color, far_color, blend))
    return colors


def prepare_custom_preview(
    geometry,
    color=None,
    attractor_point=None,
    near_color=None,
    far_color=None,
    distance=10.0,
):
    """
    Prepare geometry and colors for Grasshopper's Custom Preview component.

    geometry : Grasshopper geometry item or list of geometry items
    color    : one preview color/material or one color/material per geometry item
    attractor_point : optional Rhino.Geometry.Point3d for distance-based coloring
    near_color : color at the attractor point (yellow by default)
    far_color : color at or beyond distance (red by default)
    distance : distance over which near_color transitions to far_color

    Returns (geometry, color), to connect to Custom Preview's G and M inputs.
    When attractor_point is provided, color is generated for each item's
    bounding-box center; otherwise, the provided color is passed through.
    This controls Grasshopper preview only; it does not assign a Rhino document
    material or bake the geometry.
    """
    if attractor_point is not None:
        color = colors_by_distance(
            geometry,
            attractor_point,
            near_color,
            far_color,
            distance,
        )
    elif color is None:
        raise ValueError("Provide a color or an attractor_point for distance coloring.")

    return geometry, color


def create_circle(center_point=None, radius=5.0):
    """
    Build a circle in the XY plane as a NurbsCurve.

    center_point : Rhino.Geometry.Point3d -- circle center (origin by default)
    radius       : float -- circle radius

    Returns a Rhino.Geometry.NurbsCurve.
    """
    if center_point is None:
        center_point = rg.Point3d(0, 0, 0)
    if not isinstance(center_point, rg.Point3d):
        raise TypeError("center_point must be a Rhino.Geometry.Point3d.")
    if radius is None:
        radius = 5.0
    if radius <= 0:
        raise ValueError("radius must be greater than zero.")

    plane = rg.Plane(center_point, rg.Vector3d.ZAxis)
    circle = rg.Circle(plane, radius)
    return circle.ToNurbsCurve()


def create_axis_line(start_point, axis="X", length=10.0):
    """
    Create a line from a point in the positive X, Y, or Z direction.

    start_point : Rhino.Geometry.Point3d -- line start
    axis        : str -- axis direction: "X", "Y", or "Z"
    length      : float -- line length

    Returns a Rhino.Geometry.Line.
    """
    if start_point is None:
        raise ValueError("start_point must be provided.")
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")
    if axis is None:
        axis = "X"
    if not isinstance(axis, str):
        raise TypeError('axis must be "X", "Y", or "Z".')
    if length is None:
        length = 10.0
    if length == 0:
        raise ValueError("length must not be zero.")

    axis = axis.strip().upper()
    directions = {
        "X": rg.Vector3d.XAxis,
        "Y": rg.Vector3d.YAxis,
        "Z": rg.Vector3d.ZAxis,
    }
    if axis not in directions:
        raise ValueError('axis must be "X", "Y", or "Z".')

    end_point = start_point + directions[axis] * length
    return rg.Line(start_point, end_point)


def create_diamond_pattern(
    start_point,
    diamond_width=2.0,
    diamond_height=2.0,
    gap=0.0,
    rows=5,
    columns=5,
    tolerance=0.001,
):
    """
    Create a grid of planar diamond surfaces in the XY plane with an edge gap.

    start_point    : Rhino.Geometry.Point3d -- bottom vertex of the first grid cell
    diamond_width  : float -- horizontal diagonal of each diamond
    diamond_height : float -- vertical diagonal of each diamond
    gap            : float -- perpendicular clear distance between neighboring edges
    rows           : int -- number of diamond rows in the tessellation
    columns        : int -- number of diamond columns in the tessellation
    tolerance      : float -- tolerance used to create planar Breps

    The grid spacing is based on the full diamond dimensions; each surface is
    inset around its cell center so neighboring surfaces are separated by gap.
    If gap would collapse a surface, the inset is capped to retain a small,
    tolerance-safe diamond.
    Returns a list of Rhino.Geometry.Brep surfaces.
    """
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")
    if diamond_width is None or not math.isfinite(diamond_width) or diamond_width <= 0:
        raise ValueError("diamond_width must be a finite number greater than zero.")
    if (
        diamond_height is None
        or not math.isfinite(diamond_height)
        or diamond_height <= 0
    ):
        raise ValueError("diamond_height must be a finite number greater than zero.")
    for name, count in (("rows", rows), ("columns", columns)):
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("{} must be a positive integer.".format(name))
    if isinstance(gap, (list, tuple)):
        if len(gap) != rows * columns:
            raise ValueError(
                "A gap list must contain exactly one value per diamond "
                "(rows * columns)."
            )
        gaps = gap
        for value in gaps:
            if value is None or not math.isfinite(value) or value < 0:
                raise ValueError(
                    "Each gap must be a finite number greater than or equal to zero."
                )
    else:
        if gap is None or not math.isfinite(gap) or gap < 0:
            raise ValueError(
                "gap must be a finite number greater than or equal to zero."
            )
        gaps = [gap] * (rows * columns)
    if tolerance is None or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be a finite number greater than zero.")

    half_width = diamond_width / 2.0
    half_height = diamond_height / 2.0
    minimum_scale = min(
        1.0,
        (4.0 * tolerance) / min(diamond_width, diamond_height),
    )

    column_step = rg.Vector3d(half_width, half_height, 0.0)
    row_step = rg.Vector3d(-half_width, half_height, 0.0)
    surfaces = []

    for row in range(rows):
        for column in range(columns):
            cell_bottom = start_point + column_step * column + row_step * row
            cell_center = cell_bottom + rg.Vector3d(0.0, half_height, 0.0)
            gap_value = gaps[row * columns + column]
            inset_scale = max(
                minimum_scale,
                1.0
                - gap_value
                * math.sqrt(
                    (1.0 / diamond_width**2) + (1.0 / diamond_height**2)
                ),
            )
            inset_half_width = half_width * inset_scale
            inset_half_height = half_height * inset_scale
            bottom = cell_center + rg.Vector3d(0.0, -inset_half_height, 0.0)
            right = cell_center + rg.Vector3d(inset_half_width, 0.0, 0.0)
            top = cell_center + rg.Vector3d(0.0, inset_half_height, 0.0)
            left = cell_center + rg.Vector3d(-inset_half_width, 0.0, 0.0)
            boundary = rg.Polyline([bottom, right, top, left, bottom])
            planar_breps = rg.Brep.CreatePlanarBreps(
                boundary.ToNurbsCurve(), tolerance
            )
            if planar_breps is None or len(planar_breps) != 1:
                raise RuntimeError("Rhino could not create a diamond surface.")
            surfaces.append(planar_breps[0])

    return surfaces


def create_diamond_attractor_gaps(
    start_point,
    diamond_width,
    diamond_height,
    rows,
    columns,
    pull_point,
    distance_from,
    distance_to,
    gap_near,
    gap_far,
):
    """
    Map each diamond center's distance from a pull point to an individual gap.

    start_point    : Rhino.Geometry.Point3d -- bottom vertex of the first grid cell
    diamond_width  : float -- horizontal diamond diagonal and grid pitch
    diamond_height : float -- vertical diamond diagonal and grid pitch
    rows           : int -- number of diamond rows
    columns        : int -- number of diamond columns
    pull_point     : Rhino.Geometry.Point3d -- point attracting smaller gaps
    distance_from  : float -- distance mapped to gap_near
    distance_to    : float -- distance mapped to gap_far
    gap_near       : float -- minimum gap at or nearer than distance_from
    gap_far        : float -- maximum gap at or farther than distance_to

    Distances are measured in XY, ignoring the points' Z coordinates. The
    returned row-major gap list can be connected to create_diamond_pattern.
    """
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")
    if not isinstance(pull_point, rg.Point3d):
        raise TypeError("pull_point must be a Rhino.Geometry.Point3d.")
    if diamond_width is None or not math.isfinite(diamond_width) or diamond_width <= 0:
        raise ValueError("diamond_width must be a finite number greater than zero.")
    if (
        diamond_height is None
        or not math.isfinite(diamond_height)
        or diamond_height <= 0
    ):
        raise ValueError("diamond_height must be a finite number greater than zero.")
    for name, count in (("rows", rows), ("columns", columns)):
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("{} must be a positive integer.".format(name))
    if (
        distance_from is None
        or not math.isfinite(distance_from)
        or distance_from < 0
    ):
        raise ValueError("distance_from must be a finite non-negative number.")
    if (
        distance_to is None
        or not math.isfinite(distance_to)
        or distance_to <= distance_from
    ):
        raise ValueError("distance_to must be greater than distance_from.")
    if gap_near is None or not math.isfinite(gap_near) or gap_near < 0:
        raise ValueError("gap_near must be a finite non-negative number.")
    if gap_far is None or not math.isfinite(gap_far) or gap_far < gap_near:
        raise ValueError("gap_far must be greater than or equal to gap_near.")

    column_step = rg.Vector3d(diamond_width / 2.0, diamond_height / 2.0, 0.0)
    row_step = rg.Vector3d(-diamond_width / 2.0, diamond_height / 2.0, 0.0)
    first_center = start_point + rg.Vector3d(0.0, diamond_height / 2.0, 0.0)
    gaps = []
    for row in range(rows):
        for column in range(columns):
            center = first_center + column_step * column + row_step * row
            distance = math.sqrt(
                (center.X - pull_point.X) ** 2 + (center.Y - pull_point.Y) ** 2
            )
            blend = min(
                1.0,
                max(0.0, (distance - distance_from) / (distance_to - distance_from)),
            )
            gaps.append(gap_near + (gap_far - gap_near) * blend)

    return gaps


def create_pyramids_from_surfaces(surfaces, height=1.0, tolerance=0.001):
    """
    Create a closed pyramid Brep from each planar surface.

    surfaces   : Rhino.Geometry.Surface, Brep, or iterable of either
    height     : float -- signed vertical distance from base centroid to apex
    tolerance  : float -- tolerance used to join the pyramid faces

    Each base must be a single planar face with one outer boundary and straight
    boundary edges. The apex is above or below the surface centroid along Z.
    Returns a list of closed solid Rhino.Geometry.Brep objects.
    """
    if surfaces is None:
        raise ValueError("surfaces must be provided.")
    if height is None or not math.isfinite(height) or height == 0:
        raise ValueError("height must be a finite non-zero number.")
    if tolerance is None or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be a finite number greater than zero.")

    if isinstance(surfaces, (rg.Surface, rg.Brep)):
        surfaces = [surfaces]

    pyramids = []
    for surface in surfaces:
        if isinstance(surface, rg.Surface):
            base_brep = surface.ToBrep()
        elif isinstance(surface, rg.Brep):
            base_brep = surface
        else:
            raise TypeError(
                "Each item in surfaces must be a Rhino.Geometry.Surface or Brep."
            )

        if base_brep is None or base_brep.Faces.Count != 1:
            raise ValueError("Each base must be a single-face surface or Brep.")
        face = base_brep.Faces[0]
        if not face.IsPlanar(tolerance):
            raise ValueError("Each base surface must be planar.")
        if any(loop.LoopType == rg.BrepLoopType.Inner for loop in face.Loops):
            raise ValueError("Base surfaces with holes are not supported.")

        area_properties = rg.AreaMassProperties.Compute(base_brep)
        if area_properties is None:
            raise RuntimeError("Rhino could not find the base surface centroid.")
        centroid = area_properties.Centroid
        apex = centroid + rg.Vector3d(0.0, 0.0, height)

        boundary_curves = base_brep.DuplicateNakedEdgeCurves(True, True)
        if boundary_curves is None or len(boundary_curves) < 3:
            raise ValueError("Each base must have a closed boundary with at least 3 edges.")

        faces = [base_brep]
        for boundary_curve in boundary_curves:
            if not boundary_curve.IsLinear(tolerance):
                raise ValueError(
                    "Pyramid bases must have straight boundary edges."
                )
            triangle = rg.Brep.CreateFromCornerPoints(
                boundary_curve.PointAtStart,
                boundary_curve.PointAtEnd,
                apex,
                tolerance,
            )
            if triangle is None:
                raise RuntimeError("Rhino could not create a pyramid side face.")
            faces.append(triangle)

        joined = rg.Brep.JoinBreps(faces, tolerance)
        if joined is None or len(joined) != 1 or not joined[0].IsSolid:
            raise RuntimeError(
                "Rhino could not join the base and side faces into a closed pyramid."
            )
        pyramids.append(joined[0])

    return pyramids


def create_sine_curve(
    length=10.0,
    amplitude=1.0,
    wavelength=5.0,
    direction=None,
    wave_direction=None,
    start_point=None,
    phase=0.0,
    sample_count=100,
):
    """
    Create a sampled sinusoidal NurbsCurve in a plane defined by two directions.

    length         : float -- length along the curve's travel direction
    amplitude      : float -- wave height on either side of the travel axis
    wavelength     : float -- distance along the travel axis for one full cycle
    direction      : Rhino.Geometry.Vector3d -- curve travel direction (X by default)
    wave_direction : Rhino.Geometry.Vector3d -- oscillation direction (Y by default)
    start_point    : Rhino.Geometry.Point3d -- curve origin (world origin by default)
    phase          : float -- phase shift in radians
    sample_count   : int -- number of curve intervals used to sample the sine wave

    Returns a Rhino.Geometry.NurbsCurve. The curve is an interpolated
    approximation of the sinusoid; sample_count controls its smoothness.
    """
    if start_point is None:
        start_point = rg.Point3d(0.0, 0.0, 0.0)
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")

    if direction is None:
        direction = rg.Vector3d.XAxis
    if wave_direction is None:
        wave_direction = rg.Vector3d.YAxis
    if not isinstance(direction, rg.Vector3d):
        raise TypeError("direction must be a Rhino.Geometry.Vector3d.")
    if not isinstance(wave_direction, rg.Vector3d):
        raise TypeError("wave_direction must be a Rhino.Geometry.Vector3d.")

    travel = rg.Vector3d(direction.X, direction.Y, direction.Z)
    wave = rg.Vector3d(wave_direction.X, wave_direction.Y, wave_direction.Z)
    if not travel.Unitize():
        raise ValueError("direction must not be a zero vector.")
    if not wave.Unitize():
        raise ValueError("wave_direction must not be a zero vector.")
    dot_product = travel.X * wave.X + travel.Y * wave.Y + travel.Z * wave.Z
    if abs(dot_product) > 1e-9:
        raise ValueError("direction and wave_direction must be perpendicular.")

    if length is None or not math.isfinite(length) or length <= 0:
        raise ValueError("length must be a finite number greater than zero.")
    if amplitude is None or not math.isfinite(amplitude):
        raise ValueError("amplitude must be a finite number.")
    if wavelength is None or not math.isfinite(wavelength) or wavelength <= 0:
        raise ValueError("wavelength must be a finite number greater than zero.")
    if phase is None or not math.isfinite(phase):
        raise ValueError("phase must be a finite number in radians.")
    if (
        not isinstance(sample_count, int)
        or isinstance(sample_count, bool)
        or sample_count < 3
    ):
        raise ValueError("sample_count must be an integer greater than or equal to 3.")

    points = []
    for index in range(sample_count + 1):
        distance = length * index / sample_count
        wave_offset = amplitude * math.sin(
            (2.0 * math.pi * distance / wavelength) + phase
        )
        point = start_point + travel * distance + wave * wave_offset
        points.append(point)

    curve = rg.Curve.CreateInterpolatedCurve(points, 3)
    if curve is None:
        raise RuntimeError("Rhino could not create the interpolated sine curve.")
    return curve


def create_dashed_line(start_point, end_point, dash_length=1.0, gap_length=1.0):
    """
    Divide the segment between two points into evenly spaced line dashes.

    start_point : Rhino.Geometry.Point3d -- start of the full line
    end_point   : Rhino.Geometry.Point3d -- end of the full line
    dash_length : float -- length of each dash
    gap_length  : float -- empty space between consecutive dashes

    Returns a list of Rhino.Geometry.Line objects. The final dash is shortened
    if the remaining line is shorter than dash_length.
    """
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")
    if not isinstance(end_point, rg.Point3d):
        raise TypeError("end_point must be a Rhino.Geometry.Point3d.")
    if dash_length is None or not math.isfinite(dash_length) or dash_length <= 0:
        raise ValueError("dash_length must be a finite number greater than zero.")
    if gap_length is None or not math.isfinite(gap_length) or gap_length < 0:
        raise ValueError(
            "gap_length must be a finite number greater than or equal to zero."
        )

    line_vector = end_point - start_point
    line_length = line_vector.Length
    if line_length == 0:
        return []

    direction = line_vector / line_length
    dashes = []
    position = 0.0
    while position < line_length:
        dash_end = min(position + dash_length, line_length)
        dash_start_point = start_point + direction * position
        dash_end_point = start_point + direction * dash_end
        dashes.append(rg.Line(dash_start_point, dash_end_point))
        position = dash_end + gap_length

    return dashes


def offset_loft_extrude_curves(
    curves, offset_distance=1.0, extrusion_height=1.0, tolerance=0.001
):
    """
    Offset XY-plane curves, loft each pair, and extrude the lofted surfaces in Z.

    curves           : Rhino.Geometry.Curve, Line, or iterable of either
    offset_distance  : float -- sideways strip width; may be positive or negative
    extrusion_height : float -- extrusion distance along Z; may be negative
    tolerance        : float -- Rhino model tolerance for offset and booleans

    Returns a list of solid Rhino.Geometry.Brep extrusions.
    """
    if curves is None:
        raise ValueError("curves must be provided.")
    if (
        offset_distance is None
        or not math.isfinite(offset_distance)
        or offset_distance == 0
    ):
        raise ValueError("offset_distance must be a finite non-zero number.")
    if (
        extrusion_height is None
        or not math.isfinite(extrusion_height)
        or extrusion_height == 0
    ):
        raise ValueError("extrusion_height must be a finite non-zero number.")
    if tolerance is None or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be a finite number greater than zero.")

    if isinstance(curves, (rg.Curve, rg.Line)):
        curves = [curves]

    solids = []
    for curve in curves:
        if isinstance(curve, rg.Line):
            curve = curve.ToNurbsCurve()
        if not isinstance(curve, rg.Curve):
            raise TypeError(
                "Each item in curves must be a Rhino.Geometry.Curve or Line."
            )

        if not curve.IsPlanar():
            raise ValueError("All input curves must be planar.")
        bounding_box = curve.GetBoundingBox(True)
        if (
            not bounding_box.IsValid
            or bounding_box.Max.Z - bounding_box.Min.Z > tolerance
        ):
            raise ValueError("All input curves must lie in an XY plane.")
        plane = rg.Plane(
            rg.Point3d(0.0, 0.0, bounding_box.Min.Z),
            rg.Vector3d.ZAxis,
        )

        offset_curves = curve.Offset(
            plane, offset_distance, tolerance, rg.CurveOffsetCornerStyle.Sharp
        )
        if offset_curves is None or len(offset_curves) != 1:
            raise RuntimeError(
                "Rhino must create exactly one offset curve for each input curve."
            )
        offset_curve = offset_curves[0]

        loft_result = rg.Brep.CreateFromLoft(
            [curve, offset_curve],
            rg.Point3d.Unset,
            rg.Point3d.Unset,
            rg.LoftType.Straight,
            False,
        )
        if loft_result is None or len(loft_result) == 0:
            raise RuntimeError("Rhino could not loft an input curve and its offset.")

        extrusion_vector = rg.Vector3d(0.0, 0.0, extrusion_height)
        for loft in loft_result:
            translated_loft = loft.DuplicateBrep()
            if translated_loft is None:
                raise RuntimeError("Rhino could not duplicate the lofted surface.")
            if not translated_loft.Transform(
                rg.Transform.Translation(extrusion_vector)
            ):
                raise RuntimeError("Rhino could not translate the lofted surface.")

            boundary_curves = loft.DuplicateNakedEdgeCurves(True, True)
            if boundary_curves is None or len(boundary_curves) == 0:
                raise RuntimeError(
                    "Rhino could not find the lofted surface boundary to extrude."
                )

            extrusion_faces = [loft, translated_loft]
            for boundary_curve in boundary_curves:
                side_surface = rg.Surface.CreateExtrusion(
                    boundary_curve, extrusion_vector
                )
                if side_surface is None:
                    raise RuntimeError(
                        "Rhino could not extrude a boundary of the lofted surface."
                    )
                side_brep = rg.Brep.CreateFromSurface(side_surface)
                if side_brep is None:
                    raise RuntimeError(
                        "Rhino could not convert an extrusion face to a Brep."
                    )
                extrusion_faces.append(side_brep)

            joined = rg.Brep.JoinBreps(extrusion_faces, tolerance)
            if joined is None or len(joined) != 1 or not joined[0].IsSolid:
                raise RuntimeError(
                    "Rhino could not join the loft and its Z extrusion into a solid."
                )
            solids.append(joined[0])

    return solids


def create_sphere(center_point=None, radius=5.0):
    """
    Build a sphere as a Brep.

    center_point : Rhino.Geometry.Point3d or Rhino point GUID -- sphere center
                    (origin by default)
    radius       : float -- sphere radius

    Returns a Rhino.Geometry.Brep.
    """
    if center_point is None:
        center_point = rg.Point3d(0, 0, 0)
    elif not isinstance(center_point, rg.Point3d):
        from System import Guid

        if not isinstance(center_point, Guid):
            raise TypeError(
                "center_point must be a Rhino.Geometry.Point3d or a GUID "
                "for a point object in the active Rhino document."
            )

        import Rhino

        document = Rhino.RhinoDoc.ActiveDoc
        point_object = (
            document.Objects.FindId(center_point) if document is not None else None
        )
        if point_object is None or not isinstance(point_object.Geometry, rg.Point):
            raise ValueError(
                "center_point GUID does not identify a point object in the "
                "active Rhino document. Pass a Rhino.Geometry.Point3d instead."
            )
        center_point = point_object.Geometry.Location

    if radius is None:
            radius = 5.0
    if radius <= 0:
            raise ValueError("radius must be greater than zero.")

    sphere = rg.Sphere(center_point, radius)
    return sphere.ToBrep()


def extrude_curve(profile_curve, height=10.0):
    """
    Extrude a closed planar curve into a capped solid Brep.

    profile_curve : Rhino.Geometry.Curve, Circle, or Rhino curve GUID
                    -- closed planar extrusion profile
    height        : float -- extrusion distance along the profile plane normal

    Returns a solid Rhino.Geometry.Brep.
    """
    if profile_curve is None:
        raise ValueError("profile_curve must be provided.")

    if not isinstance(profile_curve, (rg.Curve, rg.Circle)):
        from System import Guid

        if isinstance(profile_curve, Guid):
            import Rhino

            document = Rhino.RhinoDoc.ActiveDoc
            curve_object = (
                document.Objects.FindId(profile_curve)
                if document is not None
                else None
            )
            profile_curve = (
                curve_object.Geometry if curve_object is not None else None
            )
        else:
            script_variable = getattr(profile_curve, "ScriptVariable", None)
            if callable(script_variable):
                profile_curve = script_variable()

    if isinstance(profile_curve, rg.Circle):
        profile_curve = profile_curve.ToNurbsCurve()
    if not isinstance(profile_curve, rg.Curve):
        raise TypeError(
            "profile_curve must be a Rhino.Geometry.Curve, Circle, or a GUID "
            "for a curve object in the active Rhino document. In Grasshopper, "
            "set the input type hint to Curve."
        )
    if not profile_curve.IsClosed:
        raise ValueError("profile_curve must be closed to create a solid.")
    if not profile_curve.IsPlanar():
        raise ValueError("profile_curve must be planar.")
    if height is None:
        height = 10.0
    if height == 0:
        raise ValueError("height must not be zero.")

    extrusion = rg.Extrusion.Create(profile_curve, height, True)
    if extrusion is None:
        raise RuntimeError("Rhino could not create the extrusion.")

    brep = extrusion.ToBrep()
    if brep is None or not brep.IsSolid:
        raise RuntimeError("Rhino created an extrusion that is not a solid.")
    return brep


def create_pipe(rail_curve, radius=1.0):
    """
    Create a solid pipe along a curve with rounded ends.

    rail_curve : Rhino.Geometry.Curve -- pipe centerline
    radius     : float -- pipe radius

    Returns a list of solid Rhino.Geometry.Brep objects.
    """
    if rail_curve is None:
        raise ValueError("rail_curve must be provided.")

    if not isinstance(rail_curve, rg.Curve):
        from System import Guid

        if isinstance(rail_curve, Guid):
            import Rhino

            document = Rhino.RhinoDoc.ActiveDoc
            curve_object = (
                document.Objects.FindId(rail_curve) if document is not None else None
            )
            rail_curve = (
                curve_object.Geometry if curve_object is not None else None
            )
        else:
            script_variable = getattr(rail_curve, "ScriptVariable", None)
            if callable(script_variable):
                rail_curve = script_variable()

    if not isinstance(rail_curve, rg.Curve):
        raise TypeError(
            "rail_curve must be a Rhino.Geometry.Curve or a GUID for a curve "
            "object in the active Rhino document. In Grasshopper, set the "
            "input type hint to Curve."
        )
    if radius is None:
        radius = 1.0
    if radius <= 0:
        raise ValueError("radius must be greater than zero.")

    import Rhino

    document = Rhino.RhinoDoc.ActiveDoc
    tolerance = document.ModelAbsoluteTolerance if document is not None else 0.01
    angle_tolerance = (
        document.ModelAngleToleranceRadians
        if document is not None
        else math.radians(1.0)
    )
    pipes = rg.Brep.CreatePipe(
        rail_curve,
        radius,
        False,
        rg.PipeCapMode.Round,
        False,
        tolerance,
        angle_tolerance,
    )
    if pipes is None or len(pipes) == 0:
        raise RuntimeError("Rhino could not create the pipe.")
    if any(not pipe.IsSolid for pipe in pipes):
        raise RuntimeError("Rhino created a pipe that is not a capped solid.")
    return list(pipes)


def boolean_difference(brep_a, brep_b):
    """
    Perform a boolean difference operation between two Breps.

    brep_a : Rhino.Geometry.Brep -- the first Brep
    brep_b : Rhino.Geometry.Brep -- the second Brep to subtract from the first

    Returns a list of Rhino.Geometry.Brep resulting from the difference.
    """
    if brep_a is None or brep_b is None:
        raise ValueError("Both brep_a and brep_b must be provided.")

    result = rg.Brep.CreateBooleanDifference(brep_a, brep_b, 0.001)
    return result


def copy_brep_along_z(brep, distance, copy_count):
    """
    Create copies of a Brep, each offset in the +Z direction.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    distance : float -- the Z spacing between consecutive copies
    copy_count : int -- the number of copies to create

    Returns a list of Rhino.Geometry.Brep copies; copy i is moved by distance * (i + 1).
    """
    if brep is None:
        raise ValueError("brep must be provided.")
    if copy_count < 0:
        raise ValueError("copy_count must not be negative.")

    copies = []
    for i in range(1, int(copy_count) + 1):
        copy = brep.DuplicateBrep()
        copy.Transform(rg.Transform.Translation(rg.Vector3d(0, 0, distance * i)))
        copies.append(copy)
    return copies
