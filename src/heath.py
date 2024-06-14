from Grasshopper.Kernel import GH_RuntimeMessageLevel as Message

class globals:
    version = "0.1.0-dev"

class utils:
    @staticmethod
    def warn(ghenv, message):  
        ghenv.Component.AddRuntimeMessage(Message.Warning, message)

    @staticmethod
    def replace_null(value, default):
        return value if value is not None else default