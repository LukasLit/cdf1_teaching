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


def create_arc(center_point=None, radius=5.0, start_angle=0.0, end_angle=90.0, plane=None):
    """
    Build an arc in a plane as a NurbsCurve.

    center_point : Rhino.Geometry.Point3d -- arc center (origin by default)
    radius       : float -- arc radius
    start_angle  : float -- start angle in degrees
    end_angle    : float -- end angle in degrees
    plane        : Rhino.Geometry.Plane -- optional custom plane; if omitted,
                   the arc lies in the XY plane with the Z axis as normal

    Returns a Rhino.Geometry.NurbsCurve.
    """
    if center_point is None:
        center_point = rg.Point3d.Origin
    if not isinstance(center_point, rg.Point3d):
        raise TypeError("center_point must be a Rhino.Geometry.Point3d.")
    if radius is None or not math.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be a finite number greater than zero.")
    if start_angle is None or end_angle is None:
        raise ValueError("start_angle and end_angle must be provided.")

    start_angle = float(start_angle)
    end_angle = float(end_angle)
    if not math.isfinite(start_angle) or not math.isfinite(end_angle):
        raise ValueError("start_angle and end_angle must be finite numbers.")

    if plane is not None:
        if hasattr(plane, "Value"):
            plane = plane.Value
        if isinstance(plane, rg.Plane):
            center_point = plane.Origin
        else:
            # Grasshopper can hand back a placeholder Guid when no Plane is set.
            plane = rg.Plane(center_point, rg.Vector3d.ZAxis)
    if plane is None:
        plane = rg.Plane(center_point, rg.Vector3d.ZAxis)

    delta = end_angle - start_angle
    if delta <= 0:
        delta += 360.0

    plane_rotated = rg.Plane(plane)
    plane_rotated.Rotate(math.radians(start_angle), plane.Normal)
    arc = rg.Arc(plane_rotated, radius, math.radians(delta))
    return arc.ToNurbsCurve()


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


def create_point_grid(
    start_point=None,
    columns=5,
    rows=5,
    x_spacing=10.0,
    y_spacing=10.0,
):
    """
    Create a rectangular grid of points in the world XY plane.

    start_point : Rhino.Geometry.Point3d -- lower-left grid point (origin by default)
    columns     : int -- number of points in the X direction
    rows        : int -- number of points in the Y direction
    x_spacing   : float -- distance between columns
    y_spacing   : float -- distance between rows

    Returns a row-major list of Rhino.Geometry.Point3d, starting at
    start_point and proceeding along X before moving to the next Y row.
    """
    if start_point is None:
        start_point = rg.Point3d(0, 0, 0)
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")

    for name, count in (("columns", columns), ("rows", rows)):
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("{} must be a positive integer.".format(name))

    for name, spacing in (("x_spacing", x_spacing), ("y_spacing", y_spacing)):
        if spacing is None or not math.isfinite(spacing) or spacing <= 0:
            raise ValueError(
                "{} must be a finite number greater than zero.".format(name)
            )

    return [
        start_point + rg.Vector3d(column * x_spacing, row * y_spacing, 0.0)
        for row in range(rows)
        for column in range(columns)
    ]


def move_geometry(geometry, start_point, end_point):
    """
    Move Rhino geometry by the vector from start_point to end_point.

    geometry    : Rhino geometry item or list of Rhino geometry items
    start_point : Rhino.Geometry.Point3d -- start of the translation vector
    end_point   : Rhino.Geometry.Point3d -- end of the translation vector

    Returns the moved item, or a list of moved items when geometry is a list
    or tuple. Input geometry is duplicated and left unchanged.
    """
    if not isinstance(start_point, rg.Point3d):
        raise TypeError("start_point must be a Rhino.Geometry.Point3d.")
    if not isinstance(end_point, rg.Point3d):
        raise TypeError("end_point must be a Rhino.Geometry.Point3d.")

    transform = rg.Transform.Translation(end_point - start_point)

    def move_item(item):
        if item is None:
            raise ValueError("geometry items must not be None.")
        if isinstance(item, rg.Point3d):
            return transform.TransformPoint(item)
        if isinstance(item, rg.Vector3d):
            return transform.TransformVector(item)
        if isinstance(item, rg.Line):
            moved_line = rg.Line(item)
            if not moved_line.Transform(transform):
                raise RuntimeError("Rhino could not transform the line.")
            return moved_line

        duplicate = getattr(item, "Duplicate", None)
        if not callable(duplicate):
            raise TypeError(
                "Each geometry item must be Rhino geometry that can be duplicated."
            )
        moved_item = duplicate()
        if moved_item is None:
            raise RuntimeError("Rhino could not duplicate a geometry item.")
        if not moved_item.Transform(transform):
            raise RuntimeError("Rhino could not transform a geometry item.")
        return moved_item

    if isinstance(geometry, (list, tuple)):
        return [move_item(item) for item in geometry]
    return move_item(geometry)


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

"""Bauhaus elements for Rhino 8 / Grasshopper Python 3.

Each solid is built in a local plane. Geometry is returned for preview,
without adding objects to the Rhino document.
"""

import math
import Rhino.Geometry as rg


def _positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite number greater than zero.")
    return value


def _polygon(vertices):
    points = [rg.Point3d(x, y, 0) for x, y in vertices]
    return rg.PolylineCurve(points + [points[0]])


def _radial_point(radius, angle):
    return rg.Point3d(radius * math.cos(angle), radius * math.sin(angle), 0)


def _sector_outline(radius, sweep, inner_radius=0):
    """Closed outline with exact arcs, symmetric about local +Y."""
    middle = math.pi / 2
    start = middle - sweep / 2
    end = middle + sweep / 2
    outer_start = _radial_point(radius, start)
    outer_end = _radial_point(radius, end)
    outer_arc = rg.Arc(outer_start, _radial_point(radius, middle), outer_end)

    if inner_radius == 0 and sweep == math.pi:
        segments = [outer_arc, rg.Line(outer_end, outer_start)]
    else:
        inner_end = _radial_point(inner_radius, end)
        inner_start = _radial_point(inner_radius, start)
        inner_arc = rg.Arc(inner_end, _radial_point(inner_radius, middle), inner_start)
        segments = [
            outer_arc, rg.Line(outer_end, inner_end), inner_arc,
            rg.Line(inner_start, outer_start),
        ]

    outline = rg.PolyCurve()
    for segment in segments:
        if not outline.Append(segment):
            raise RuntimeError("Could not assemble the arc outline.")
    return outline


def create_bauhaus_element(kind="half_disc", plane=None, unit=10.0,
                           width=4.0, depth=1.0, thickness=0.4,
                           sweep_deg=240.0, custom_profile=None):
    """Return (solid Brep, bottom outline) for one element.

    kind: disc, half_disc, open_ring, bar, wedge, diamond, or custom.
    plane: profile plane at the bottom of the solid. Extrudes along +normal.
    unit: length of one module in Rhino document units.
    width, depth, thickness: sizes in modules. Width is the diameter for
        round profiles. Depth is only used by bar, wedge and diamond.
    sweep_deg: covered angle of the open ring, in degrees (15 to 345).
        The inner radius is 65% of the outer radius.
    custom_profile: valid simple closed curve drawn on World XY in Rhino
        document units. Width and depth are ignored for this profile.

    The origin is the circle center for round profiles and the bounding
    rectangle center for polygonal profiles.
    """
    if plane is None:
        plane = rg.Plane.WorldXY
    if not isinstance(plane, rg.Plane) or not plane.IsValid:
        raise ValueError("plane must be a valid Rhino construction plane.")

    kind = kind.strip().lower()
    unit = _positive(unit, "unit")
    height = _positive(thickness, "thickness") * unit

    if kind == "custom":
        if not isinstance(custom_profile, rg.Curve):
            raise ValueError("Connect a Curve to custom_profile.")
        bounds = custom_profile.GetBoundingBox(True)
        if (not custom_profile.IsValid or not custom_profile.IsClosed
                or not bounds.IsValid or max(abs(bounds.Min.Z), abs(bounds.Max.Z)) > 1e-7):
            raise ValueError("custom_profile must be a valid closed curve on World XY (Z=0).")
        outline = custom_profile.DuplicateCurve()
    elif kind in ("disc", "half_disc", "open_ring"):
        radius = _positive(width, "width") * unit / 2
        if kind == "disc":
            outline = rg.Circle(rg.Plane.WorldXY, radius).ToNurbsCurve()
        elif kind == "half_disc":
            outline = _sector_outline(radius, math.pi)
        else:
            if not 15 <= sweep_deg <= 345:
                raise ValueError("sweep_deg must be between 15 and 345 degrees.")
            outline = _sector_outline(radius, math.radians(sweep_deg), 0.65 * radius)
    elif kind in ("bar", "wedge", "diamond"):
        x = _positive(width, "width") * unit / 2
        y = _positive(depth, "depth") * unit / 2
        if kind == "bar":
            outline = _polygon([(-x, -y), (x, -y), (x, y), (-x, y)])
        elif kind == "wedge":
            outline = _polygon([(-x, -y), (x, -y), (-x, y)])
        else:
            outline = _polygon([(0, -y), (x, 0), (0, y), (-x, 0)])
    else:
        raise ValueError("kind must be disc, half_disc, open_ring, bar, wedge, diamond, or custom.")

    extrusion = rg.Extrusion.Create(outline, rg.Plane.WorldXY, height, True)
    if extrusion is None:
        raise ValueError("Rhino could not extrude this outline.")
    solid = extrusion.ToBrep(True)
    if solid is None or not solid.IsValid or not solid.IsSolid:
        raise ValueError("The outline did not produce a valid closed solid.")

    placement = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
    if not solid.Transform(placement) or not outline.Transform(placement):
        raise RuntimeError("Rhino could not place the element in the supplied plane.")
    return solid, outline


def create_bauhaus_rod(start, end, radius=0.5):
    """Return (solid Brep, axis Line, tip, unit direction from start to tip).

    Start is the attachment at the main shape. End is the free tip that can
    be passed to a separate curved connector. Radius is in document units.
    """
    radius = _positive(radius, "radius")
    if not all(isinstance(p, rg.Point3d) and p.IsValid for p in (start, end)):
        raise ValueError("start and end must be valid Rhino points.")
    axis = rg.Line(start, end)
    direction = axis.Direction
    if not direction.Unitize():
        raise ValueError("start and end must be distinct.")
    section = rg.Circle(rg.Plane(start, direction), radius)
    solid = rg.Cylinder(section, axis.Length).ToBrep(True, True)
    if solid is None or not solid.IsValid or not solid.IsSolid:
        raise ValueError("Rhino could not create a valid solid rod.")
    return solid, axis, end, direction


# Parametric wall installation
"""Append these functions to cdf.geometry_basics (Rhino 8 / Python 3).

Coordinates in wall_plane: X horizontal, Y vertical, Z away from the wall.
Uses existing create_bauhaus_element, create_bauhaus_rod, create_dashed_line,
offset_loft_extrude_curves, create_diamond_pattern and create_pyramids_from_surfaces.
"""

def _wall_inputs(unit, mode, depth):
    if not math.isfinite(unit) or unit <= 0:
        raise ValueError("unit must be positive.")
    if mode not in (0, 1, 2):
        raise ValueError("mode must be 0 (grid), 1 (steps), or 2 (attractor).")
    if not 0 <= depth <= 1:
        raise ValueError("depth must be between 0 and 1.")
    return (0.2, 0.55, 1.0)[int(mode)] * depth


def create_wall_layout(wall_plane, unit=10.0, mode=0, depth=1.0, seed=12,
                       anchor_size=4.4):
    """Return anchor plane, disc planes/widths, bar planes/widths,
    all body planes/widths, attractor, and wall panel.

    Satellite positions follow anchor_size. Local planes determine extrusion
    directions. Elevation includes a geometric clearance for tilted profiles.
    """
    import random
    spatiality = _wall_inputs(unit, mode, depth)
    if not isinstance(wall_plane, rg.Plane) or not wall_plane.IsValid:
        raise ValueError("Connect a valid wall_plane.")
    if not 3 <= anchor_size <= 6:
        raise ValueError("anchor_size must be between 3 and 6 modules.")
    rng = random.Random(int(seed))
    ratio = anchor_size / 4.4
    widths = [anchor_size, 1.6, 2.0, 3.8, 3.2]
    locations = [(0, 0), (-2.6, 4.8), (3.3, 2.4), (-1.2, 3.1), (1.8, -0.5)]
    inplane_angles = [180, 0, 0, 65, -10]
    tilts = [30, -55, 65, -35, 50]
    planes = []
    for i, ((x, y), width) in enumerate(zip(locations, widths)):
        jitter = rng.uniform(-0.12, 0.12) if i else 0.0
        x = (x * ratio + jitter) * unit
        y = (y * ratio + jitter) * unit
        tilt = math.radians(tilts[i] * spatiality)
        extent = width * unit * 0.6
        distance = unit * (0.25 + spatiality * (0.4 + i * 0.18)) + extent * abs(math.sin(tilt))
        plane = rg.Plane(wall_plane)
        plane.Origin = wall_plane.PointAt(x, y, distance)
        plane.Rotate(math.radians(inplane_angles[i]), plane.Normal, plane.Origin)
        plane.Rotate(tilt, plane.YAxis, plane.Origin)
        planes.append(plane)
    panel_plane = rg.Plane(wall_plane)
    panel_plane.Origin = wall_plane.PointAt(0, 0.4 * unit, -0.15 * unit)
    panel, _ = create_bauhaus_element("bar", panel_plane, unit,
                                     max(12 * ratio, 12), max(16 * ratio, 16), 0.15)
    return (planes[0], planes[1:3], widths[1:3], planes[3:5], widths[3:5],
            planes, widths, planes[2].Origin, panel)


def create_wall_mounts(wall_plane, body_planes, body_widths, unit=10.0,
                       thickness=0.35, rod_length=0.8):
    """Return rear support rods, two front rods, tips A/B, travel tangents A/B.

    Body order: half disc, two discs, two bars. Front rods attach to the half
    disc and right disc. Tangent B points into the second rod.
    """
    if len(body_planes) != 5 or len(body_widths) != 5:
        raise ValueError("Expected five body planes and widths from layout.")
    _positive(unit, "unit")
    _positive(rod_length, "rod_length")
    _positive(thickness, "thickness")
    supports = []
    contacts = []
    for i, plane in enumerate(body_planes):
        local_y = body_widths[i] * unit * 0.22 if i == 0 else 0.0
        bottom = plane.PointAt(0, local_y, 0)
        wall_contact = wall_plane.ClosestPoint(bottom)
        supports.append(create_bauhaus_rod(wall_contact, bottom, 0.09 * unit)[0])
        contacts.append(plane.PointAt(0, local_y, thickness * unit))
    front_rods = []
    tips = []
    for i in (0, 2):
        tip = contacts[i] + body_planes[i].Normal * (rod_length * unit)
        front_rods.append(create_bauhaus_rod(contacts[i], tip, 0.07 * unit)[0])
        tips.append(tip)
    return (supports, front_rods, tips[0], tips[1],
            body_planes[0].Normal, -body_planes[2].Normal)


def create_endpoint_wave(start, end, start_direction, end_direction,
                         wave_direction, amplitude=3.0, bends=2, radius=0.7,
                         tolerance=0.001):
    """Return centerline, flat-capped pipe Breps, and endpoint error.

    Cubic Hermite base plus sin(pi*t)^2-windowed waves. Each sampled segment
    is a cubic Bezier with analytic end derivatives. Endpoints and tangent
    directions are exact; the interior wave is a piecewise approximation.
    """
    if not isinstance(bends, int) or not 1 <= bends <= 3:
        raise ValueError("bends must be an integer from 1 to 3.")
    if not math.isfinite(amplitude) or amplitude < 0:
        raise ValueError("amplitude must be non-negative.")
    _positive(radius, "radius")
    _positive(tolerance, "tolerance")
    length = start.DistanceTo(end)
    if length <= tolerance:
        raise ValueError("Connector endpoints must be distinct.")
    tangent_a = rg.Vector3d(start_direction)
    tangent_b = rg.Vector3d(end_direction)
    wave = rg.Vector3d(wave_direction)
    if not tangent_a.Unitize() or not tangent_b.Unitize() or not wave.Unitize():
        raise ValueError("Connector directions must be nonzero.")
    tangent_a *= length * 0.9
    tangent_b *= length * 0.9
    chord = end - start
    frequency = 2 * math.pi * bends

    def evaluate(t):
        h = -2 * t**3 + 3 * t**2
        ha = t**3 - 2 * t**2 + t
        hb = t**3 - t**2
        envelope = math.sin(math.pi * t)**2
        wave_offset = amplitude * envelope * math.sin(frequency * t)
        point = start + chord * h + tangent_a * ha + tangent_b * hb + wave * wave_offset
        derivative = (chord * (-6 * t**2 + 6 * t)
                      + tangent_a * (3 * t**2 - 4 * t + 1)
                      + tangent_b * (3 * t**2 - 2 * t))
        wave_derivative = amplitude * (
            math.pi * math.sin(2 * math.pi * t) * math.sin(frequency * t)
            + envelope * frequency * math.cos(frequency * t))
        return point, derivative + wave * wave_derivative

    count = 16 * bends
    curve = rg.PolyCurve()
    for i in range(count):
        p0, d0 = evaluate(i / count)
        p1, d1 = evaluate((i + 1) / count)
        segment = rg.BezierCurve([p0, p0 + d0 / (3 * count),
                                 p1 - d1 / (3 * count), p1]).ToNurbsCurve()
        if not curve.Append(segment):
            raise RuntimeError("Could not assemble connector segments.")
    pipes = rg.Brep.CreatePipe(curve, radius, False, rg.PipeCapMode.Flat,
                              True, tolerance, math.radians(1))
    if not pipes or any(not b.IsValid or not b.IsSolid for b in pipes):
        raise ValueError("Pipe failed. Reduce amplitude, bends, or radius.")
    error = max(curve.PointAtStart.DistanceTo(start), curve.PointAtEnd.DistanceTo(end))
    return curve, list(pipes), error


def create_wall_pattern(wall_plane, attractor, unit=10.0, mode=0, depth=1.0,
                        seed=12, count=4, anchor_size=4.4):
    """Return small solids, their centers, and sizes; count x count cells.

    Mode 0 regular lattice. Mode 1 alternating offsets/tilts. Mode 2 distance
    to the satellite controls scale and depth, with radial orientations.
    Seed selects diamonds or bars and bounded size variation in all modes.
    """
    import random
    spatiality = _wall_inputs(unit, mode, depth)
    if not isinstance(count, int) or not 2 <= count <= 6:
        raise ValueError("count must be an integer from 2 to 6.")
    rng = random.Random(int(seed) + 101)
    ratio = anchor_size / 4.4
    solids, centers, sizes = [], [], []
    for row in range(count):
        for col in range(count):
            x = (0.5 + 4.0 * col / (count - 1)) * ratio
            y = (3.8 + 3.0 * row / (count - 1)) * ratio
            if mode == 1:
                x += 0.25 * (row % 2)
            on_wall = wall_plane.PointAt(x * unit, y * unit, 0)
            distance = on_wall.DistanceTo(wall_plane.ClosestPoint(attractor))
            proximity = max(0, 1 - distance / (7 * unit * ratio))
            size = (0.35 + rng.uniform(0, 0.15)) * unit
            if mode == 1:
                size *= 0.75 if (row + col) % 2 else 1.25
            elif mode == 2:
                size *= 0.5 + 1.2 * proximity
            height = unit * (0.15 + spatiality * (0.3 + proximity))
            plane = rg.Plane(wall_plane)
            plane.Origin = on_wall + wall_plane.Normal * (0.15 * unit + 0.3 * size)
            if mode == 1:
                plane.Rotate(math.radians(35 * (-1)**col * spatiality), plane.XAxis, plane.Origin)
            elif mode == 2:
                delta = attractor - on_wall
                angle = math.atan2(delta * wall_plane.YAxis, delta * wall_plane.XAxis)
                plane.Rotate(angle, plane.Normal, plane.Origin)
                plane.Rotate(math.radians(40 * spatiality * proximity), plane.YAxis, plane.Origin)
            if rng.random() < 0.65:
                surfaces = create_diamond_pattern(rg.Point3d(0, -size/2, 0), size, size, 0, 1, 1)
                solid = create_pyramids_from_surfaces(surfaces, height)[0]
                solid.Transform(rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane))
            else:
                solid, _ = create_bauhaus_element("bar", plane, 1, size, size*0.4, height)
            solids.append(solid)
            centers.append(plane.Origin)
            sizes.append(size)
    return solids, centers, sizes


def create_wall_dashes(anchor_plane, unit=10.0, mode=0, depth=1.0,
                       dash_length=0.65, gap=0.45):
    """Return dashed solids and centerlines, in a plane following the anchor.

    Existing XY-based offset/extrusion functions operate locally first.
    The resulting geometry is then transformed into the dependent plane.
    """
    spatiality = _wall_inputs(unit, mode, depth)
    _positive(dash_length, "dash_length")
    if not math.isfinite(gap) or gap < 0.1:
        raise ValueError("gap must be at least 0.1 modules.")
    solids, rails = [], []
    for row in range(3):
        length = (3.5, 4.5, 5.5)[row] if mode == 1 else 4.5
        local_start = rg.Point3d((-2.6 + row*0.55)*unit, 1.7*unit, 0)
        local_end = local_start + rg.Vector3d(0, length*unit, 0)
        dashes = create_dashed_line(local_start, local_end, dash_length*unit, gap*unit)
        curves = [line.ToNurbsCurve() for line in dashes]
        plane = rg.Plane(anchor_plane)
        plane.Translate(anchor_plane.Normal * (unit*0.6))
        plane.Rotate(math.radians(spatiality * (row-1)*12), plane.XAxis, plane.Origin)
        transform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
        bodies = offset_loft_extrude_curves(curves, 0.14*unit, (0.12+0.1*spatiality*row)*unit)
        for body in bodies:
            body.Transform(transform)
            solids.append(body)
        for curve in curves:
            curve.Transform(transform)
            rails.append(curve)
    return solids, rails

# Parametric shelf: local X = width, Y = depth, Z = height.
def create_shelf_layout(origin, width=120.0, height=110.0, depth=24.0, mode=0):
    """Return shelf planes/widths, post starts/ends, and decoration planes.
    Mode changes bay divisions and shelf heights through one parameter.
    """
    if min(width,height,depth)<=0 or mode not in (0,1,2):
        raise ValueError('Positive dimensions and mode 0, 1 or 2 required.')
    fractions=[(0,.28,.56,.78,1),(0,.35,.55,.82,1),(0,.24,.62,.8,1)][int(mode)]
    levels=[(.08,.32,.57,.8),(.08,.38,.62,.86),(.08,.28,.65,.9)][int(mode)]
    xs=[f*width for f in fractions]
    zs=[f*height for f in levels]
    spans=[(0,4,0),(0,2,1),(1,4,1),(2,4,2),(0,2,2),(1,4,3)]
    planes=[]; widths=[]
    for left,right,level in spans:
        # Split overlapping middle-level shelves at the second support.
        if (left,right,level)==(0,2,1):right=1
        p=rg.Plane.WorldXY
        p.Origin=origin+rg.Vector3d((xs[left]+xs[right])/2,depth/2,zs[level])
        planes.append(p);widths.append(xs[right]-xs[left])
    starts=[];ends=[]
    for i,x in enumerate(xs):
        top=height if i in (1,2) else zs[3]
        for y in (0,depth):
            starts.append(origin+rg.Vector3d(x,y,0))
            ends.append(origin+rg.Vector3d(x,y,top))
    return planes,widths,starts,ends,xs,zs


def create_shelf_boards(planes, widths, depth=24.0, thickness=1.8,
                        inset_enabled=False, inset_amount=5.0, mode=0):
    """Shelf thickness grows upward from each layout plane."""
    adjusted = create_shelf_insets(planes, widths, depth, inset_enabled, inset_amount, mode)
    return [create_bauhaus_element('bar',p,1,w,d,thickness)[0]
            for p,w,d in zip(*adjusted)]


def create_shelf_objects(origin, xs, zs, depth=24.0, thickness=1.8, seed=12,
                         inset_enabled=False, inset_amount=5.0, mode=0):
    """Objects sit on shelves; size is derived from bay width and free height."""
    import random
    rng=random.Random(int(seed))
    discs=[];blocks=[];frames=[]
    for bay,level in [(0,1),(1,0),(2,1),(3,2)]:
        bay_width=xs[bay+1]-xs[bay]
        gap=zs[min(level+1,3)]-zs[level]
        diameter=min(bay_width*.95,gap*.85)*rng.uniform(.85,1)
        p=rg.Plane(origin+rg.Vector3d((xs[bay]+xs[bay+1])/2,depth*.8,zs[level]+thickness+diameter/2),rg.Vector3d.XAxis,rg.Vector3d.ZAxis)
        discs.append(create_bauhaus_element('disc',p,1,diameter,1,1.2)[0])
    for bay,level in [(0,0),(1,1),(2,2),(3,0)]:
        size=min((xs[bay+1]-xs[bay])*.55,(zs[level+1]-zs[level])*.6)
        p=rg.Plane.WorldXY
        p.Origin=origin+rg.Vector3d((xs[bay]+xs[bay+1])/2,depth*.4,zs[level]+thickness)
        blocks.append(create_bauhaus_element('bar',p,1,size,depth*.55,size)[0])
    # Upright rectangular frames, attached to the upper shelf.
    for bay in (1,2):
        left=xs[bay];right=xs[bay+1];bottom=zs[3]+thickness
        top=bottom+(xs[-1]*.14 if bay==1 else xs[-1]*.1)
        pts=[origin+rg.Vector3d(x,depth*.9,z) for x,z in [(left,bottom),(left,top),(right,top),(right,bottom)]]
        for a,b in zip(pts,pts[1:]):frames.append(create_bauhaus_rod(a,b,.5)[0])
    if inset_enabled:
        spans = [(0,4,0),(0,1,1),(1,4,1),(2,4,2),(0,2,2),(1,4,3)]
        planes = [rg.Plane(origin + rg.Vector3d((xs[l]+xs[r])/2,depth/2,zs[z]), rg.Vector3d.ZAxis) for l,r,z in spans]
        widths = [xs[r]-xs[l] for l,r,z in spans]
        new_planes, new_widths, new_depths = create_shelf_insets(planes,widths,depth,True,inset_amount,mode)
        for bodies,indices in [(discs,[1,0,2,3]),(blocks,[0,2,3,0]),(frames,[5]*6)]:
            for body,index in zip(bodies,indices):
                old=planes[index]; new=new_planes[index]
                sx=new_widths[index]/widths[index]; sy=new_depths[index]/depth
                if bodies is frames:
                    body.Transform(rg.Transform.Scale(old,sx,sy,1))
                    body.Transform(rg.Transform.Translation(new.Origin-old.Origin))
                else:
                    box=body.GetBoundingBox(True)
                    foot=rg.Point3d(box.Center.X,box.Center.Y,box.Min.Z)
                    delta=foot-old.Origin
                    target=new.Origin+rg.Vector3d(delta.X*sx,delta.Y*sy,delta.Z)
                    body.Transform(rg.Transform.Scale(foot,min(sx,sy)))
                    body.Transform(rg.Transform.Translation(target-foot))
    return discs,blocks,frames


def create_shelf_insets(planes, widths, depth=24.0, enabled=False, amount=5.0, mode=0):
    """Six deterministic independent edge setbacks, controlled by mode and amount.
    False or zero returns the original footprints. Insets are limited to
    18 percent of width/depth per edge to preserve positive usable areas.
    """
    if mode not in (0,1,2) or not math.isfinite(amount) or amount<0:
        raise ValueError('mode must be 0/1/2 and amount nonnegative.')
    _positive(depth,'depth')
    if len(planes)!=len(widths):raise ValueError('planes and widths must match.')
    patterns=[(0,0,.15,0),(1,.1,.7,0),(.15,.8,0,.5),(.7,.1,.5,.1),(.2,1,.15,.6),(.55,.2,.6,0)]
    result_planes=[]; result_widths=[]; result_depths=[]
    for i,(plane,width) in enumerate(zip(planes,widths)):
        _positive(width,'width')
        left,right,front,back=patterns[(i+int(mode)*2)%len(patterns)]
        a=amount if enabled else 0
        left=min(a*left,width*.18);right=min(a*right,width*.18)
        front=min(a*front,depth*.18);back=min(a*back,depth*.18)
        p=rg.Plane(plane)
        p.Translate(p.XAxis*((left-right)/2)+p.YAxis*((front-back)/2))
        result_planes.append(p);result_widths.append(width-left-right);result_depths.append(depth-front-back)
    return result_planes,result_widths,result_depths


def create_shelf_grid(origin, width=120.0, height=110.0, depth=24.0,
                      mode=0, gaps_enabled=True, tower_height=0.18):
    """All board edges and frame junctions share the same support axes.
    Return planes, widths, rod starts/ends, X/Z grids, occupied cells.
    occupied cell = 4 * level + bay. Tower extension is a height fraction.
    """
    if mode not in (0,1,2) or not 0 <= tower_height <= .5:
        raise ValueError('mode must be 0/1/2 and tower_height between 0 and 0.5.')
    for name,value in [('width',width),('height',height),('depth',depth)]:
        _positive(value,name)
    fractions=[(0,.28,.56,.78,1),(0,.35,.55,.82,1),(0,.24,.62,.8,1)][int(mode)]
    levels=[(.08,.32,.57,.8),(.08,.38,.62,.86),(.08,.28,.65,.9)][int(mode)]
    xs=[f*width for f in fractions];zs=[f*height for f in levels]
    patterns=[
        [(0,4,0),(0,1,1),(2,4,1),(0,2,2),(3,4,2),(1,4,3)],
        [(0,4,0),(0,2,1),(3,4,1),(0,1,2),(2,4,2),(1,3,3)],
        [(0,4,0),(0,1,1),(2,4,1),(1,3,2),(0,2,3),(3,4,3)],
    ]
    spans=patterns[int(mode)] if gaps_enabled else [(0,4,i) for i in range(4)]
    planes=[];widths=[];cells=[]
    for left,right,level in spans:
        plane=rg.Plane.WorldXY
        plane.Origin=origin+rg.Vector3d((xs[left]+xs[right])/2,depth/2,zs[level])
        planes.append(plane);widths.append(xs[right]-xs[left])
        cells.extend(4*level+bay for bay in range(left,right))
    tall=height*(1+tower_height)
    tops=[zs[3],tall,tall,height,zs[3]]
    starts=[];ends=[]
    def rod(x1,y1,z1,x2,y2,z2):
        starts.append(origin+rg.Vector3d(x1,y1,z1))
        ends.append(origin+rg.Vector3d(x2,y2,z2))
    for i,x in enumerate(xs):
        for y in (0,depth):rod(x,y,0,x,y,tops[i])
    # Crossbars land precisely on the vertical supports, front and back.
    for left,right,top in [(1,2,tall),(2,3,height),(3,4,zs[3])]:
        for y in (0,depth):rod(xs[left],y,top,xs[right],y,top)
    # Join front/back rails at the tower and at the stepped frame peaks.
    for i in (1,2,3,4):rod(xs[i],0,tops[i],xs[i],depth,tops[i])
    return planes,widths,starts,ends,xs,zs,cells


def create_shelf_grid_objects(origin,xs,zs,occupied,depth=24.0,thickness=1.8,seed=12):
    """Place objects only on occupied cells, relative to their board top.
    Each object fits its bay width and the clear height to the next level.
    """
    import random
    rng=random.Random(int(seed))
    discs=[];blocks=[]
    cells=sorted(set(int(c) for c in occupied if 0<=int(c)<12))
    # Keep a restrained alternating selection across the three lower levels.
    selected=[c for i,c in enumerate(cells) if i%3!=2]
    for i,cell in enumerate(selected):
        level,bay=divmod(cell,4)
        clear=zs[level+1]-zs[level]-thickness
        if clear<=0:raise ValueError('Shelf thickness exceeds the clear bay height.')
        size=min((xs[bay+1]-xs[bay])*.80,clear*.82)*rng.uniform(.85,1)
        x=(xs[bay]+xs[bay+1])/2
        bottom=zs[level]+thickness
        if i%2==0:
            plane=rg.Plane(origin+rg.Vector3d(x,depth*.75,bottom+size/2),rg.Vector3d.XAxis,rg.Vector3d.ZAxis)
            discs.append(create_bauhaus_element('disc',plane,1,size,1,1.2)[0])
        else:
            plane=rg.Plane.WorldXY
            plane.Origin=origin+rg.Vector3d(x,depth*.4,bottom)
            blocks.append(create_bauhaus_element('bar',plane,1,size*.8,depth*.55,size*.8)[0])
    return discs,blocks

SHELF_CATALOG = ('flat_disc','half_disc','open_ring','box','cone','sphere',
                 'wedge','diamond','pyramid','diamond_field','sine_band',
                 'dashes','rods','arc','disc_stack','cut_box','custom_L','point_grid')


def create_shelf_catalog_slots(origin,xs,zs,occupied,depth=24.0,thickness=1.8):
    """Allocate 18 specimens to real shelf cells, splitting wide cells as needed.
    Returns bottom-center points and maximum usable width/height/depth.
    """
    cells=sorted(set(int(c) for c in occupied))
    if not cells:raise ValueError('No occupied shelf cells.')
    points=[];widths=[];heights=[];depths=[]
    total=len(SHELF_CATALOG)
    for index in range(total):
        cell=cells[index%len(cells)];level,bay=divmod(cell,4)
        repetitions=(total-1-(index%len(cells)))//len(cells)+1
        slot=index//len(cells)
        width=(xs[bay+1]-xs[bay])/repetitions
        x=xs[bay]+width*(slot+.5)
        clear=zs[level+1]-zs[level]-thickness if level<3 else (zs[-1]-zs[0])*.25
        points.append(origin+rg.Vector3d(x,depth*.5,zs[level]+thickness))
        widths.append(width*.84);heights.append(clear*.85);depths.append(depth*.8)
    return points,widths,heights,depths


def create_shelf_catalog_object(kind,foot,max_width,max_height,max_depth,scale=0.85):
    """Reuse the existing Python shape library, then fit and place on a shelf.
    scale 0.2..2 is a proportion of the available slot, keeping the foot fixed.
    Values above 1 allow objects to exceed their assigned slot dimensions.
    Standing circular profiles have a flat cut 20 percent of radius above bottom.
    """
    if kind not in SHELF_CATALOG or not .2<=scale<=2:
        raise ValueError('Use a catalog kind and scale from 0.2 to 2.')
    for value in (max_width,max_height,max_depth):_positive(value,'slot size')
    upright=rg.Transform.PlaneToPlane(rg.Plane.WorldXY,rg.Plane(rg.Point3d.Origin,rg.Vector3d.XAxis,rg.Vector3d.ZAxis))
    bodies=[]
    if kind=='flat_disc':
        outline=rg.PolyCurve()
        outline.Append(rg.Arc(rg.Point3d(.6,-.8,0),rg.Point3d(0,1,0),rg.Point3d(-.6,-.8,0)))
        outline.Append(rg.Line(rg.Point3d(-.6,-.8,0),rg.Point3d(.6,-.8,0)))
        bodies=[extrude_curve(outline,.25)]
        bodies[0].Transform(upright)
    elif kind in ('half_disc','open_ring','wedge','diamond','custom_L'):
        profile=_polygon([(-1,-1),(1,-1),(1,-.3),(-.3,-.3),(-.3,1),(-1,1)]) if kind=='custom_L' else None
        bodies=[create_bauhaus_element('custom' if kind=='custom_L' else kind,unit=1,width=2,depth=2,thickness=.3,custom_profile=profile)[0]]
        bodies[0].Transform(upright)
    elif kind=='box':bodies=[create_box(x_size=1.5,y_size=1,z_size=2)]
    elif kind=='cone':bodies=[create_cone(height=2,radius=1)]
    elif kind=='sphere':
        sphere=create_sphere(radius=1)
        cutter=create_box(rg.Point3d(-2,-2,-2),4,4,1.2)
        bodies=list(boolean_difference(sphere,cutter) or [])
    elif kind in ('pyramid','diamond_field'):
        n=1 if kind=='pyramid' else 3
        gaps=create_diamond_attractor_gaps(rg.Point3d.Origin,1,1,n,n,rg.Point3d(0,1,0),0,3,.03,.18)
        surfaces=create_diamond_pattern(rg.Point3d.Origin,1,1,gaps,n,n)
        bodies=create_pyramids_from_surfaces(surfaces,1 if n==1 else .25)
    elif kind=='sine_band':
        rail=create_sine_curve(length=4,amplitude=.6,wavelength=2,sample_count=80)
        bodies=offset_loft_extrude_curves(rail,.18,.3)
        for b in bodies:b.Transform(upright)
    elif kind=='dashes':
        rails=create_dashed_line(rg.Point3d.Origin,rg.Point3d(4,0,0),.6,.3)
        bodies=offset_loft_extrude_curves(rails,.4,.4)
    elif kind=='rods':
        for x in (0,.6,1.2):
            rail=create_axis_line(rg.Point3d(x,0,0),'Z',2+x*.3)
            bodies.extend(create_pipe(rail.ToNurbsCurve(),.1))
        bodies.append(create_box(rg.Point3d(-.2,-.2,-.1),1.6,.4,.15))
    elif kind=='arc':
        rail=create_arc(radius=1,start_angle=0,end_angle=180)
        bodies=create_pipe(rail,.12)
        for b in bodies:b.Transform(upright)
    elif kind=='disc_stack':
        disc=extrude_curve(create_circle(radius=1),.25)
        bodies=[disc]+copy_brep_along_z(disc,.25,3)
    elif kind=='cut_box':
        box=create_box(rg.Point3d(-1,-.5,0),2,1,2)
        cutter=create_sphere(rg.Point3d(0,-.5,1.3),.7)
        bodies=list(boolean_difference(box,cutter) or [])
    elif kind=='point_grid':
        points=create_point_grid(columns=3,rows=3,x_spacing=.6,y_spacing=.6)
        bodies=[create_sphere(p,.15) for p in points]
        bodies.append(create_box(rg.Point3d(-.2,-.2,-.2),1.6,1.6,.1))
    if not bodies or any(not b.IsValid or not b.IsSolid for b in bodies):
        raise ValueError('Could not build solid specimen: '+kind)
    bounds=rg.BoundingBox.Empty
    for b in bodies:bounds.Union(b.GetBoundingBox(True))
    extent=bounds.Max-bounds.Min
    factor=scale*min(max_width/extent.X,max_depth/extent.Y,max_height/extent.Z)
    bottom=rg.Point3d(bounds.Center.X,bounds.Center.Y,bounds.Min.Z)
    for b in bodies:b.Transform(rg.Transform.Scale(bottom,factor))
    return move_geometry(bodies,bottom,foot)


def create_shelf_attractor_field(foot, max_width, max_height, max_depth,
                                 scale=0.85, pull_point=None, influence=0.6,
                                 gap_near=0.03, gap_far=0.45, count=5):
    """Return pyramids, visible world attractor, and per-cell gaps.
    pull_point X/Y are normalized field coordinates 0..1. Its Z is ignored.
    influence is measured in fractions of the field width.
    A fixed envelope prevents changing gaps from rescaling the whole field.
    """
    if pull_point is None:pull_point=rg.Point3d(.25,.3,0)
    if not isinstance(count,int) or not 2<=count<=10:
        raise ValueError('count must be between 2 and 10.')
    if not .2<=scale<=1:raise ValueError('scale must be between 0.2 and 1.')
    if not 0<=gap_near<=gap_far<.7:
        raise ValueError('Require 0 <= gap_near <= gap_far < 0.7.')
    for value in (influence,max_width,max_height,max_depth):_positive(value,'positive parameter')
    local_attractor=rg.Point3d((pull_point.X-.5)*count,pull_point.Y*count,0)
    gaps=create_diamond_attractor_gaps(rg.Point3d.Origin,1,1,count,count,
                                      local_attractor,0,influence*count,gap_near,gap_far)
    surfaces=create_diamond_pattern(rg.Point3d.Origin,1,1,gaps,count,count)
    bodies=create_pyramids_from_surfaces(surfaces,.35)
    factor=scale*min(max_width/count,max_depth/count,max_height/.35)
    reference=rg.Point3d(0,count/2,0)
    for b in bodies:b.Transform(rg.Transform.Scale(reference,factor))
    bodies=move_geometry(bodies,reference,foot)
    visible_attractor=foot+(local_attractor-reference)*factor
    return bodies,visible_attractor,gaps

# Parametric rear diamond net: LunchBox supplies the panel geometry.
def shelf_net_frame(origin, width, height, depth, tower_height, offset, columns, rows):
    import Rhino.Geometry as rg
    import math
    h=height*(1+tower_height)
    center=rg.Point3d(origin.X+width/2,origin.Y+depth+offset,origin.Z+h/2)
    span=math.sqrt(width*width+h*h)*2.1
    pts=[center+rg.Vector3d(x*span/2,0,z*span/2) for x,z in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    return pts[0],pts[1],pts[2],pts[3],max(2,int(round(columns*span/width))),max(2,int(round(rows*span/h))),center,h


def shelf_net_clip(edges, center, width, height, shift_x, shift_z, angle, shear):
    import Rhino.Geometry as rg
    import math
    result=[];seen=set();r=math.radians(angle);co=math.cos(r);si=math.sin(r)
    def transform(p):
        x=p.X-center.X;z=p.Z-center.Z
        x=x+shear*z
        return (co*x-si*z+shift_x*width,si*x+co*z+shift_z*height)
    for curve in edges:
        a=transform(curve.PointAtStart);b=transform(curve.PointAtEnd)
        dx=b[0]-a[0];dz=b[1]-a[1];lo=0.;hi=1.;valid=True
        for p,q in [(-dx,a[0]+width/2),(dx,width/2-a[0]),(-dz,a[1]+height/2),(dz,height/2-a[1])]:
            if abs(p)<1e-10:
                if q<0:valid=False;break
            elif p<0:lo=max(lo,q/p)
            else:hi=min(hi,q/p)
        if not valid or hi-lo<1e-8:continue
        ends=[rg.Point3d(center.X+a[0]+t*dx,center.Y,center.Z+a[1]+t*dz) for t in [lo,hi]]
        key=tuple(sorted(tuple(round(v,6) for v in (p.X,p.Y,p.Z)) for p in ends))
        if key in seen:continue
        seen.add(key)
        result.append(rg.LineCurve(*ends))
    return result


def shelf_net_colors(meshes, groups, colors, sharpness=4.0, blend_radius=5.0):
    import Rhino.Geometry as rg
    import System.Drawing as sd
    centers=[];palette=[]
    for geoms,col in zip(groups,colors):
        box=rg.BoundingBox.Empty
        for g in geoms:
            if hasattr(g,'Value'):g=g.Value
            if g is not None:box.Union(g.GetBoundingBox(True))
        if box.IsValid:
            centers.append(box.Center);palette.append(col)
    if not centers:return [],[]
    # Distances in elevation (X/Z): shelf depth does not dilute the colour field.
    def color(p):
        distances=[((p.X-q.X)**2+(p.Z-q.Z)**2+blend_radius**2)**.5 for q in centers]
        nearest=min(distances)
        weights=[(nearest/d)**sharpness for d in distances];total=sum(weights)
        return sd.Color.FromArgb(*[int(round(sum(w*getattr(c,ch) for w,c in zip(weights,palette))/total)) for ch in ['R','G','B']])
    result=[]
    for mesh in meshes:
        m=mesh.DuplicateMesh()
        m.VertexColors.Clear()
        for p in m.Vertices:m.VertexColors.Add(color(p))
        result.append(m)
    return result,centers


def create_shelf_object_dimensions(kind, foot, width=1.0, height=1.0, depth=1.0, radius=1.0, size=1.0):
    """Explicit model-unit dimensions; placement follows shelf, dimensions follow sliders.
    For round profiles radius is the outer radius. Circle proportions are preserved.
    """
    import Rhino.Geometry as rg
    bodies=create_shelf_catalog_object(kind,rg.Point3d.Origin,1,1,1,1)
    box=rg.BoundingBox.Empty
    for b in bodies:box.Union(b.GetBoundingBox(True))
    e=box.Max-box.Min
    if kind in ('flat_disc','half_disc','open_ring','arc'):
        width=2*radius;height=width*e.Z/e.X
    elif kind=='sphere':
        width=depth=2*radius;height=width*e.Z/e.X
    elif kind in ('cone','disc_stack'):
        width=depth=2*radius
    for v in [width,height,depth,size]:_positive(v,'dimension')
    bottom=rg.Point3d(box.Center.X,box.Center.Y,box.Min.Z)
    transform=rg.Transform.Scale(rg.Plane(bottom,rg.Vector3d.ZAxis),size*width/e.X,size*depth/e.Y,size*height/e.Z)
    for b in bodies:b.Transform(transform)
    return move_geometry(bodies,bottom,foot)

def shelf_grid_render_materials(meshes, attributes, rhino_doc, texture_folder, roughness=.28):
    """Render-safe textures for straight coloured mesh rods; keep object/group identity."""
    import Rhino
    import Rhino.Geometry as rg
    import System.Drawing as sd
    import os,math,struct,zlib,hashlib
    os.makedirs(texture_folder,exist_ok=True)
    meshes=[m.DuplicateMesh() for m in meshes]
    attributes=[a.Duplicate() for a in attributes]
    for offset in range(0,len(meshes),256):
        batch=meshes[offset:offset+256];width=128;height=len(batch)*4
        rows=[]
        for j,m in enumerate(batch):
            pts=[rg.Point3d(p) for p in m.Vertices];colors=list(m.VertexColors)
            if len(colors)!=len(pts):raise ValueError('Missing grid vertex colours')
            center=m.GetBoundingBox(True).Center
            # Principal direction of each straight pipe, using covariance power iteration.
            vecs=[(p.X-center.X,p.Y-center.Y,p.Z-center.Z) for p in pts]
            cov=[[sum(v[i]*v[j] for v in vecs) for j in range(3)] for i in range(3)]
            axis=[1,.37,.71]
            for _ in range(12):
                nxt=[sum(cov[i][j]*axis[j] for j in range(3)) for i in range(3)]
                length=math.sqrt(sum(x*x for x in nxt))
                if length<1e-15:break
                axis=[x/length for x in nxt]
            projected=[sum(v[i]*axis[i] for i in range(3)) for v in vecs];lo=min(projected);span=max(projected)-lo
            samples=sorted((((v-lo)/max(span,1e-9),c) for v,c in zip(projected,colors)), key=lambda x:x[0])
            # Average coincident cross-section colours, then interpolate along the rod.
            groups={}
            for t,c in samples:
                key=round(t,5);groups.setdefault(key,[]).append(c)
            stops=[(t,tuple(sum(getattr(c,ch) for c in cs)/len(cs) for ch in ['R','G','B'])) for t,cs in sorted(groups.items())]
            row=bytearray();k=0
            for x in range(width):
                t=x/(width-1)
                while k<len(stops)-2 and stops[k+1][0]<t:k+=1
                a,ca=stops[k];b,cb=stops[min(k+1,len(stops)-1)];f=max(0,min(1,(t-a)/max(b-a,1e-9)))
                row.extend(int(round(ca[q]*(1-f)+cb[q]*f)) for q in range(3))
            rows.extend([bytes(row)]*4)
            m.TextureCoordinates.Clear()
            for v in projected:
                t=(v-lo)/max(span,1e-9)
                m.TextureCoordinates.Add((.5+t*(width-1))/width,1-(j*4+2)/height)
        raw=b''.join(b'\x00'+row for row in rows)
        digest=hashlib.sha256(raw).hexdigest()[:20]
        path=os.path.join(texture_folder,'grid_'+digest+'.png')
        def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
        with open(path,'wb') as f:f.write(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
        name='Grid gradient metal '+digest+' %.3f'%roughness
        index=next((m.MaterialIndex for m in rhino_doc.Materials if not m.IsDeleted and m.Name==name),-1)
        if index<0:
            mat=Rhino.DocObjects.Material();mat.Name=name;mat.ToPhysicallyBased()
            p=mat.PhysicallyBased;p.BaseColor=Rhino.Display.Color4f(sd.Color.White);p.Metallic=1.;p.Roughness=roughness;p.SynchronizeLegacyMaterial()
            mat.SetBitmapTexture(path)
            index=rhino_doc.Materials.Add(mat)
        for a in attributes[offset:offset+len(batch)]:
            a.MaterialIndex=index;a.MaterialSource=Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject
    return meshes,attributes
