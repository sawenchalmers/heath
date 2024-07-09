from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message
import rhinoscriptsyntax as rs
import os, sys
import Rhino
import scriptcontext as sc
import importlib

try:  # import the ladybug_rhino and honeybee dependencies
    from ladybug_rhino.config import angle_tolerance, tolerance
    # MEGA HACK because something changed in the Rhino API rendering HB useless
    # https://discourse.ladybug.tools/t/ladybug-modules-relying-on-rhino-geometry-collections-seem-not-to-work-in-rhino-8-python-3/25222
    # from ladybug_rhino.togeometry import to_polyface3d
    from patch_honeybee import to_polyface3d_patched
    
    importlib.reload(sys.modules["patch_honeybee"])
    from ladybug_rhino.grasshopper import document_counter
    from honeybee.room import Room
    from honeybee.typing import clean_and_id_string
    
    from ladybug_rhino.intersect import bounding_box, intersect_solids 
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_rhino:\n\t{}'.format(e))

def get_results_folder(ghdoc):
    sc.doc = Rhino.RhinoDoc.ActiveDoc

    directory = os.path.dirname(str(Rhino.RhinoDoc.ActiveDoc.Path))
    if directory:
        mpl_folder = os.path.join(directory, heath_globals.results_folder)
    else:
        directory = (ghenv.Document.FilePath).split("\\")[:-1]
        full_path = '\\'.join(directory)
        mpl_folder = os.path.join(full_path, heath_globals.results_folder)

    try:
        os.makedirs(mpl_folder)
    except:
        pass

    sc.doc = ghdoc
    return mpl_folder

def create_hb_model(room_geo, construction_sets):
    room_solids = _intersect_room_geometry(room_geo)
    names = [] # todo: allow room names as input
    rooms = _create_rooms(room_solids, names)
    _apply_construction_sets(rooms, construction_sets)
    return rooms

def _intersect_room_geometry(room_geo):
    bounding_boxes = [bounding_box(brep) for brep in room_geo]
    room_solids = intersect_solids(room_geo, bounding_boxes)
    return room_solids

def _create_rooms(room_solids, names):
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
            utils.warn(ghenv.Component, msg)
        rooms.append(room)
    return rooms

# hmm, don't like this function mutating the rooms, but it is the HB way
def _apply_construction_sets(rooms, construction_sets):
    for i, room in enumerate(rooms):
        constr_set = construction_sets[i] \
            if utils.list_len_equal(construction_sets, rooms) \
            else construction_sets[0]
        room.properties.energy.construction_set = constr_set

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