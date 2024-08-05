# Copyright (c) 2024, Heath.
# You should have received a copy of the GNU Affero General Public License
# along with Heath; If not, see <http://www.gnu.org/licenses/>.
# 
# @license AGPL-3.0-or-later <https://spdx.org/licenses/AGPL-3.0-or-later>


""" This file contains patched Honeybee functions which do not work in Python 3"""
""" Changed lines from ladybug_rhino.togeometry have a "patched" comment"""

import Rhino.Geometry as rg # type: ignore
from ladybug_geometry.geometry3d.polyface import Polyface3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_rhino.togeometry import to_point3d, _remove_dup_verts, from_face3ds_to_joined_brep, to_plane
import ladybug_rhino.planarize as _planar
from ladybug_rhino.config import tolerance

import sys
if (sys.version_info > (3, 0)):  # python 3
    xrange = range

def to_polyface3d_patched(geo, meshing_parameters=None):
    """A Ladybug Polyface3D object from a Rhino Brep.

    Args:
        geo: A Rhino Brep, Surface or Mesh that will be converted into a single
            Ladybug Polyface3D.
        meshing_parameters: Optional Rhino Meshing Parameters to describe how
            curved faces should be converted into planar elements. If None,
            Rhino's Default Meshing Parameters will be used.
    """
    mesh_par = meshing_parameters or rg.MeshingParameters.Default  # default
    if not isinstance(geo, rg.Mesh):
        if not isinstance(geo, rg.Brep):  # it's likely an extrusion object
            geo = geo.ToBrep()  # extrusion objects must be cast to Brep in Rhino 8
        if _planar.has_curved_face(geo):  # keep solidity
            new_brep = from_face3ds_to_joined_brep(
                _planar.curved_solid_faces(geo, mesh_par))
            return Polyface3D.from_faces(to_face3d_patched(new_brep[0], mesh_par), tolerance)
        return Polyface3D.from_faces(to_face3d_patched(geo, mesh_par), tolerance)
    return Polyface3D.from_faces(to_face3d_patched(geo, mesh_par), tolerance)


def to_face3d_patched(geo, meshing_parameters=None):
    """List of Ladybug Face3D objects from a Rhino Brep, Surface or Mesh.

    Args:
        geo: A Rhino Brep, Surface, Extrusion or Mesh that will be converted into
            a list of Ladybug Face3D.
        meshing_parameters: Optional Rhino Meshing Parameters to describe how
            curved faces should be converted into planar elements. If None,
            Rhino's Default Meshing Parameters will be used.
    """
    faces = []  # list of Face3Ds to be populated and returned
    if isinstance(geo, rg.Mesh):  # convert each Mesh face to a Face3D
        pts = tuple(to_point3d(pt) for pt in geo.Vertices)
        for face in geo.Faces:
            if face.IsQuad:
                all_verts = (pts[face[0]], pts[face[1]], pts[face[2]], pts[face[3]])
                lb_face = Face3D(all_verts)
                if lb_face.area != 0:
                    for _v in lb_face.vertices:
                        if lb_face.plane.distance_to_point(_v) >= tolerance:
                            # non-planar quad split the quad into two planar triangles
                            verts1 = (pts[face[0]], pts[face[1]], pts[face[2]])
                            verts2 = (pts[face[3]], pts[face[0]], pts[face[1]])
                            faces.append(Face3D(verts1))
                            faces.append(Face3D(verts2))
                            break
                    else:
                        faces.append(lb_face)
            else:
                all_verts = (pts[face[0]], pts[face[1]], pts[face[2]])
                lb_face = Face3D(all_verts)
                if lb_face.area != 0:
                    faces.append(lb_face)
    else:  # convert each Brep Face to a Face3D
        meshing_parameters = meshing_parameters or rg.MeshingParameters.Default
        if not isinstance(geo, rg.Brep):  # it's likely an extrusion object
            geo = geo.ToBrep()  # extrusion objects must be cast to Brep in Rhino 8
        for b_face in geo.Faces:
            if b_face.IsPlanar(tolerance):
                try:
                    bf_plane = to_plane(b_face.FrameAt(0, 0)[-1])
                except Exception:  # failed to extract the plane from the geometry
                    bf_plane = None  # auto-calculate the plane from the vertices
                all_verts = []
                for count in range(b_face.Loops.Count):  # Each loop is a boundary/hole
                    success, loop_pline = \
                        b_face.Loops[count].To3dCurve().TryGetPolyline() # patched
                    if not success:  # Failed to get a polyline; there's a curved edge
                        loop_verts = planar_face_curved_edge_vertices_patched(
                            b_face, count, meshing_parameters)
                    else:  # we have a polyline representing the loop
                        loop_verts = tuple(to_point3d(loop_pline[i]) # patched
                                           for i in range(loop_pline.Count - 1))
                    all_verts.append(_remove_dup_verts(loop_verts))
                if len(all_verts[0]) >= 3:
                    if len(all_verts) == 1:  # No holes in the shape
                        faces.append(Face3D(all_verts[0], plane=bf_plane))
                    else:  # There's at least one hole in the shape
                        hls = [hl for hl in all_verts[1:] if len(hl) >= 3]
                        faces.append(Face3D(
                            boundary=all_verts[0], holes=hls, plane=bf_plane))
            else:  # curved face must be meshed into planar Face3D objects
                faces.extend(_planar.curved_surface_faces(b_face, meshing_parameters))
    return faces


def planar_face_curved_edge_vertices_patched(b_face, count, meshing_parameters):
    """Extract vertices from a planar brep face loop that has one or more curved edges.

    This method ensures vertices along the curved edge are generated in a way that
    they align with an extrusion of that edge. Alignment may not be possible when
    the adjoining curved surface is not an extrusion.

    Args:
        b_face: A brep face with the curved edge.
        count: An integer for the index of the loop to extract.
        meshing_parameters: Rhino Meshing Parameters to describe how
            curved edge should be converted into planar elements.

    Returns:
        A list of ladybug Point3D objects representing the input planar face.
    """
    loop_pcrv = b_face.Loops[count].To3dCurve() # patched
    f_norm = b_face.NormalAt(0, 0)
    if f_norm.Z < 0:
        loop_pcrv.Reverse()
    loop_verts = []
    try:
        loop_pcrvs = [loop_pcrv.SegmentCurve(i)
                      for i in xrange(loop_pcrv.SegmentCount)]
    except Exception:
        try:
            loop_pcrvs = [loop_pcrv[0]]
        except Exception:
            loop_pcrvs = [loop_pcrv]
    for seg in loop_pcrvs:
        if seg.Degree == 1:
            loop_verts.append(_planar._point3d(seg.PointAtStart))
        else:
            # Ensure curve subdivisions align with adjacent curved faces
            seg_mesh = rg.Mesh.CreateFromSurface(
                rg.Surface.CreateExtrusion(seg, f_norm*0.01), #patched to handle surfaces smaller than 1m
                meshing_parameters)
            
            for i in xrange(int(seg_mesh.Vertices.Count / 2 - 1)): # patched
                loop_verts.append(_planar._point3d(seg_mesh.Vertices[i]))
    return loop_verts
