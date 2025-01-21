from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message

class globals:
    version = "0.1.7"
    kdb_json_path = "brimstone_data/klimatdatabas_02.05.000.json"
    boverket_energy_schedules_path = "brimstone_data/231219hb_boverket_energy_schedules.json"
    kdb_hb_json_path = "brimstone_data/231211klimatdatabas_hb_materials.json"
    hb_kdb_csv_path = 'brimstone_data/230728_HBKlimatdatabas.csv'

class utils:
    @staticmethod
    def warn(ghenv, message):  
        ghenv.Component.AddRuntimeMessage(Message.Warning, message)

    @staticmethod
    def replace_null(value, default):
        return value if value is not None else default