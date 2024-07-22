# Copyright (c) 2024, Heath.
# You should have received a copy of the GNU Affero General Public License
# along with Heath; If not, see <http://www.gnu.org/licenses/>.
# 
# @license AGPL-3.0-or-later <https://spdx.org/licenses/AGPL-3.0-or-later>

"""
Inspired by: 
- HB Intersect Solids
- HB Room from Solid
- HB Solve Adjacency
"""

from typing import Any, List
from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message # type: ignore
import rhinoscriptsyntax as rs
import os, sys
import Rhino # type: ignore
from Rhino.Geometry import Brep # type: ignore
import scriptcontext as sc
import importlib
from pathlib import Path

try:  # import the ladybug_rhino and honeybee dependencies
    from ladybug_rhino.config import angle_tolerance, tolerance
    # MEGA HACK because something changed in the Rhino API rendering HB useless
    # https://discourse.ladybug.tools/t/ladybug-modules-relying-on-rhino-geometry-collections-seem-not-to-work-in-rhino-8-python-3/25222
    # from ladybug_rhino.togeometry import to_polyface3d
    from patch_honeybee import to_polyface3d_patched

    from honeybee_energy.constructionset import ConstructionSet
    from honeybee_energy.programtype import ProgramType
    
    importlib.reload(sys.modules["patch_honeybee"])
    from ladybug_rhino.grasshopper import document_counter
    from honeybee.room import Room
    from honeybee.typing import clean_and_id_string
    
    from ladybug_rhino.intersect import bounding_box, intersect_solids 
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

def create_hb_model(room_geo: List[Brep], construction_sets: List[ConstructionSet], programs: List[ProgramType]) -> List[Room]:
    """_summary_

    Args:
        room_geo (List[Brep]): _description_
        construction_sets (List[ConstructionSet]): _description_
        programs (List[ProgramType]): _description_

    Returns:
        List[Room]: _description_
    """
    room_solids = _intersect_room_geometry(room_geo)
    names = [] # todo: allow room names as input
    rooms = _create_rooms(room_solids, names)
    _apply_energy_property(rooms, construction_sets, "construction_set")
    _apply_energy_property(rooms, programs, "program_type")
    adj_rooms = _solve_adjacency(rooms)
    return adj_rooms

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

# hmm, don't like this function mutating the rooms, but it is the HB way
def _apply_energy_property(rooms: List[Room], data: List[Any] | Any, key: str) -> None:
    """Sets am energy property for input rooms

    Args:
        rooms (List[Room]): Rooms to modify
        data (List[Any] | Any): Value to set (one value for all rooms or a list of values matching the rooms)
        key (str): Attribute to set
    """
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

class heath_globals:
    version = "0.3.0-dev"
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