# Copyright (c) 2024, Heath.
# You should have received a copy of the GNU Affero General Public License
# along with Heath; If not, see <http://www.gnu.org/licenses/>.
# 
# @license AGPL-3.0-or-later <https://spdx.org/licenses/AGPL-3.0-or-later>

"""
Inspired by Ladybug Tools 1.6.0: 
- HB Intersect Solids
- HB Room from Solid
- HB Solve Adjacency
- HB Guide Surface
- HB Aperture
- HB Apertures by Ratio
- HB Extruded Border Shades
- HB Louver Shades
- HB Add Subface
- HB Shade
- HB Model
- HB HeatCool HVAC
"""

from dataclasses import dataclass
import json
from typing import Any, List
from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message # type: ignore
import rhinoscriptsyntax as rs
import os, sys
import Rhino # type: ignore
from Rhino.Geometry import Brep, Surface # type: ignore
import scriptcontext as sc
import importlib
from pathlib import Path

from patch_honeybee import to_polyface3d_patched, to_face3d_patched

try:  # import the ladybug_rhino and honeybee dependencies
    from ladybug_rhino.config import units_system, angle_tolerance, tolerance
    # MEGA HACK because something changed in the Rhino API rendering HB useless
    # https://discourse.ladybug.tools/t/ladybug-modules-relying-on-rhino-geometry-collections-seem-not-to-work-in-rhino-8-python-3/25222
    # from ladybug_rhino.togeometry import to_polyface3d

    from honeybee_energy.constructionset import ConstructionSet
    from honeybee_energy.programtype import ProgramType
    from honeybee.boundarycondition import boundary_conditions, Outdoors
    from honeybee_energy.hvac.heatcool import EQUIPMENT_TYPES_DICT
    from honeybee_energy.config import folders as hb_energy_config_folders
    from honeybee.face import Face
    from honeybee.facetype import Wall
    from honeybee.aperture import Aperture
    from honeybee.model import Model
    from honeybee.shade import Shade
    from Rhino.Geometry import MeshingParameters as mp # type: ignore
    meshing_parameters = mp.FastRenderMesh
    
    importlib.reload(sys.modules["patch_honeybee"])
    from ladybug_rhino.grasshopper import document_counter
    from honeybee.room import Room
    from honeybee.typing import clean_string, clean_and_id_string, clean_and_id_ep_string
    
    from ladybug_rhino.intersect import bounding_box, intersect_solids
    from ladybug_geometry.geometry2d.pointvector import Vector2D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

def get_results_folder(ghdoc: Any) -> Path:
    """_summary_

    Args:
        ghdoc (Any): _description_

    Returns:
        Path: _description_
    """
    sc.doc = Rhino.RhinoDoc.ActiveDoc

    directory = os.path.dirname(str(Rhino.RhinoDoc.ActiveDoc.Path))
    if directory:
        mpl_folder = os.path.join(directory, heath_globals.results_folder)
    else:
        directory = (ghenv.Document.FilePath).split("\\")[:-1] # type: ignore
        full_path = '\\'.join(directory)
        mpl_folder = os.path.join(full_path, heath_globals.results_folder)

    try:
        os.makedirs(mpl_folder)
    except:
        pass

    sc.doc = ghdoc
    return mpl_folder

def create_hb_rooms(room_geo: List[Brep], construction_sets: List[ConstructionSet], programs: List[ProgramType], adj_srf: List[Brep], energy_systems: List[str]) -> List[Room]:
    """_summary_

    Args:
        room_geo (List[Brep]): _description_
        construction_sets (List[ConstructionSet]): _description_
        programs (List[ProgramType]): _description_
        adj_srf (List[Brep]): Breps representing surfaces which should have an adiabatic boundary condition
        windows (List[Brep]): Window surfaces
    Returns:
        List[Room]: _description_
    """
    room_solids = _intersect_room_geometry(room_geo)
    names = [] # todo: allow room names as input
    rooms = _create_rooms(room_solids, names)
    _apply_energy_property(rooms, construction_sets, "construction_set")
    _apply_energy_property(rooms, programs, "program_type")
    rooms = _solve_adjacency(rooms)
    if adj_srf:
        rooms = _update_boundary_conditions(rooms, adj_srf)
    if energy_systems:
        rooms = _set_energy_systems(rooms, energy_systems)
    
    return rooms

def _intersect_room_geometry(room_geo: List[Brep]) -> List[Brep]:
    """_summary_

    Args:
        room_geo (List[Brep]): _description_

    Returns:
        List[Brep]: _description_
    """
    bounding_boxes = [bounding_box(brep) for brep in room_geo]
    room_solids = intersect_solids(room_geo, bounding_boxes)
    return room_solids

def _create_rooms(room_solids: List[Brep], names: List[str]) -> List[Room]:
    """_summary_

    Args:
        room_solids (List[Brep]): _description_
        names (List[str]): _description_

    Returns:
        List[Room]: _description_
    """
    rooms = []
    roof_angle = 60 # default from HB
    floor_angle = 180 - roof_angle # default from HB

    for i, geo in enumerate(room_solids):
        display_name = 'Room_{}'.format(document_counter('room_count')) \
            if len(names) != len(room_solids) else \
            names[i]        
        name = clean_and_id_string(display_name)


        # create the Room
        room = Room.from_polyface3d(
            name, to_polyface3d_patched(geo), roof_angle=roof_angle,
            floor_angle=floor_angle, ground_depth=tolerance)
        room.display_name = display_name

        # check that the Room geometry is closed.
        if room.check_solid(tolerance, angle_tolerance, False) != '':
            msg = 'Input _geo is not a closed volume.\n' \
                'Room volume must be closed to access most honeybee features.\n' \
                'Preview the output Room to see the holes in your model.'
            print(msg)
            utils.warn(ghenv, msg) # type: ignore
        rooms.append(room)
    return rooms

def _apply_energy_property(rooms: List[Room], data: Any, key: str) -> None:
    """Sets an energy property for input rooms

    Args:
        rooms (List[Room]): Rooms to modify
        data (List[Any] | Any): Value to set (one value for all rooms or a list of values matching the rooms)
        key (str): Attribute to set
    """
    rooms = [room.duplicate() for room in rooms]
    for i, room in enumerate(rooms):
        data_pt = data[i] \
            if utils.list_len_equal(data, rooms) \
            else data[0]
        setattr(room.properties.energy, key, data_pt)

def _solve_adjacency(rooms: List[Room]) -> List[Room]:
    """_summary_

    Args:
        rooms (List[Room]): _description_

    Returns:
        List[Room]: _description_
    """
    adj_rooms = [room.duplicate() for room in rooms]
    adj_info = Room.solve_adjacency(adj_rooms, tolerance)
    # report all of the adjacency information
    for adj_face in adj_info['adjacent_faces']:
        print('"{}" is adjacent to "{}"'.format(adj_face[0], adj_face[1]))
    return adj_rooms

def _update_boundary_conditions(rooms: List[Room], adj_srf: List[Brep], bc: str = "Adiabatic") -> List[Room]:
    """_summary_

    Args:
        rooms (List[Room]): _description_
        adj_srf (List[Brep]): surfaces which should have bc
        bc(str): boundary condition (default: "Adiabatic")

    Returns:
        List[Room]: _description_
    """
    mod_rooms = [room.duplicate() for room in rooms]
    guide_faces = [g for geo in adj_srf for g in to_face3d_patched(geo)]  # convert to lb geometry
    for room in mod_rooms:
        select_faces: List[Face] = room.faces_by_guide_surface(
            guide_faces, tolerance=tolerance, angle_tolerance=angle_tolerance
        )
        for hb_face in select_faces:
            hb_face.boundary_condition = boundary_conditions.by_name(bc)
    return mod_rooms

def _set_energy_systems(rooms: List[Room], energy_system_ids: List[str]) -> List[Room]:
    """_summary_

    Args:
        rooms (List[Room]): _description_
        energy_system_ids (List[str]): _description_

    Raises:
        ValueError: _description_

    Returns:
        List[Room]: _description_
    """
    rooms = [room.duplicate() for room in rooms]
    
    # dictionary of HVAC template names
    ext_folder = hb_energy_config_folders.standards_extension_folders[0]
    hvac_reg = os.path.join(ext_folder, 'hvac_registry.json')
    with open(hvac_reg, 'r') as f:
        hvac_dict = json.load(f)

        for i, room in enumerate(rooms):
            system_type = energy_system_ids[i] if len(rooms) == len(energy_system_ids) else energy_system_ids[0]
            # process any input properties for the HVAC system
            try:  # get the class for the HVAC system
                try:
                    sys_id = hvac_dict[system_type]
                except KeyError:
                    sys_id = system_type
            except KeyError:
                raise ValueError('System Type "{}" is not recognized as a HeatCool HVAC '
                    'system.'.format(system_type))
            if room.properties.energy.is_conditioned:
                name = clean_and_id_ep_string('Heat-Cool HVAC')
                hvac_class = EQUIPMENT_TYPES_DICT[sys_id]
                hvac = hvac_class(name, "ASHRAE_2019", sys_id)
                room.properties.energy.hvac = hvac
    return rooms

def create_hb_apertures(window_geo: List[Surface]) -> List[Aperture]:
    """_summary_

    Args:
        window_geo (List[Surface]): _description_

    Returns:
        List[Aperture]: _description_
    """
    apertures = []
    name = clean_and_id_string("Aperture")
    for geo in window_geo:
        lb_faces = to_face3d_patched(geo)
        for j, lb_face in enumerate(lb_faces):
            ap_name = f"{name}_{j}"
            ap = Aperture(ap_name, lb_face)
            ap.display_name = ap_name
            apertures.append(ap)
    
    return apertures

@dataclass
class WindowSettings():
    window_wall_ratio: float
    window_height: float
    sill_height: float
    horizontal_separation: float
    wall_thickness: float

def auto_hb_apertures(rooms: List[Room], window_wall_ratio: float, window_height: float, sill_height: float, horizontal_separation: float) -> List[Aperture]:
    """_summary_

    Args:
        window_wall_ratio (float): _description_
        window_height (float): _description_
        sill_height (float): _description_
        horizontal_separation (float): _description_

    Returns:
        List[Aperture]: _description_
    """

    window_height = 2.0 if window_height is None else window_height
    sill_height = 0.8 if sill_height is None else sill_height
    horizontal_separation = 3.0 if horizontal_separation is None else horizontal_separation
        
    apertures = []
    for room in rooms:
        face: Face
        for face in room.faces:
            if isinstance(face.boundary_condition, Outdoors) and isinstance(face.type, Wall):
                face.apertures_by_ratio_rectangle(window_wall_ratio, window_height, sill_height, horizontal_separation)
                apertures.extend(face.apertures)
    return apertures

def add_border_shades(apt: Aperture, depth: float) -> List[Aperture]:
    """_summary_

    Args:
        apertures (List[Aperture]): _description_
        depth (float): _description_

    Returns:
        List[Aperture]: _description_
    """
    if isinstance(apt.boundary_condition, Outdoors):
        apt.extruded_border(depth)
    return apt

@dataclass
class LouverSettings():
    depth: float
    count: int
    dist: float
    angle: float
    direction: bool

def add_louver_shades(apt: Aperture, depth: float, count: int, dist: float, angle: float, direction: bool) -> List[Aperture]:
    """_summary_

    Args:
        apertures (List[Aperture]): _description_
        depth (float): _description_
        count (int): _description_
        dist (float): _description_
        angle (float): _description_
        direction (bool): _description_

    Returns:
        List[Aperture]: _description_
    """
    vec = Vector2D(*((1,0) if direction else (0, 1)))

    if not dist:
        louvers = apt.louvers_by_count(count, depth, 0, angle, vec)
    else:
        louvers = apt.louvers_by_distance_between(dist, depth, 0, angle, vec, max_count=count)
    
    return apt

def add_subfaces(rooms: List[Room], apertures: List[Aperture], window_settings: WindowSettings, louver_settings: LouverSettings ) -> List[Room]:
    """_summary_

    Args:
        rooms (List[Room]): _description_
        apertures (List[Aperture]): _description_

    Returns:
        List[Room]: _description_
    """
    rooms = [r.duplicate() for r in rooms]
    apertures = [a.duplicate() for a in apertures]
    
    apt_ids = [apt.identifier for apt in apertures]
    added_ids = set()

    for room in rooms:
        face: Face
        for face in room.faces:
            for i, apt in enumerate(apertures):
                if face.geometry.is_sub_face(apt.geometry, tolerance, angle_tolerance):
                    if apt.identifier in added_ids:
                        apt = apt.duplicate()
                        apt.add_prefix("Ajd") # no idea what this is
                    added_ids.add(apt.identifier)
                    apt_ids[i] = None
                    
                    face.add_aperture(apt)
            for apt in face.apertures:
                add_border_shades(apt, window_settings.wall_thickness)
                if louver_settings:
                    ls = louver_settings
                    add_louver_shades(apt, ls.depth, ls.count, ls.dist, ls.angle, ls.direction)

    unmatched_ids = [apt_id for apt_id in apt_ids if apt_id is not None]
    if len(unmatched_ids):
        msg = f"The following sub-faces were not matched with any parent Face:{', '.join(unmatched_ids)}"
        utils.warn(ghenv, msg) # type: ignore

    return rooms

def add_shades(geo_list: List[Brep]) -> List[Shade]:
    """_summary_

    Args:
        geo (List[Brep]): _description_

    Returns:
        List[Shade]: _description_
    """
    shades = []
    for i, geo in enumerate(geo_list):
        name = clean_and_id_string("Shade")
        faces = to_face3d_patched(geo, meshing_parameters)
        for j, face in enumerate(faces):
            shd_name = f"{name}_{i}"
            shd = Shade(shd_name, face, False)
            shd.display_name = shd_name
            shades.append(shd)
    return shades


def create_hb_model(name: str, rooms: List[Room], apertures: List[Aperture], shades: List[Shade]) -> Model:
    """_summary_

    Args:
        rooms (List[Room]): _description_
        apertures (List[Aperture]): _description_

    Returns:
        Model: _description_
    """
    return Model(clean_string(name), rooms, None, shades, apertures, None, None, units_system(), tolerance, angle_tolerance)

class heath_globals:
    version = "0.5.0-dev"
    results_folder = "results"

class utils:
    # not sure the "@staticmethod" thing is needed anymore in python 3
    @staticmethod
    def list_len_equal(list1, list2):
        return len(list1) == len(list2)

    @staticmethod
    def warn(ghenv, message):
        ghenv.Component.AddRuntimeMessage(Message.Warning, message)

    @staticmethod
    def replace_null(value, default):
        return value if value is not None else default