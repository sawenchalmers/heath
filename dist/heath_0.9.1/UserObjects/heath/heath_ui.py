from HumanUIBaseApp import MainWindow # type: ignore
from MahApps.Metro import ThemeManager as tm # type: ignore
from System.Windows.Controls import TextBlock # type: ignore
from System.Windows import WindowState # type: ignore
import scriptcontext as sc
from Rhino.Geometry import Point3d # type: ignore

def handle_close_window():
    sc.sticky["heath_main_window"].pop("heath_main_window", None)

def heath_main_window(title: str, width: float, height: float, accent_color: str, location: Point3d, show: bool):
    if not show:
        pass
    else:
        if "heath_main_window" in sc.sticky:
            old_window: MainWindow = sc.sticky["heath_main_window"]
            try:
                old_window.Close()
            except:
                print("can't close window, it probably doesn't exist anymore")
        win = MainWindow()
        sc.sticky["heath_main_window"] = win
        #print(dir(win))
        win.Title = title
        win.Width = width
        win.Height = height

        current_style = tm.DetectAppStyle(win)
        tm.ChangeAppStyle(win, tm.GetAccent(accent_color), current_style.Item1)

        win.Left = location.X
        win.Right = location.Y

        win.Show()    

        if not win.IsVisible:
            status = "Hidden"
        elif win.WindowState == WindowState.Minimized:
            status = "Minimized"
        else:
            status = "Normal"

        return win, status

        """
        elements = []
        tb = TextBlock()
        tb.Text = "Heath provides a user interface for life cycle building performance assessment in the Rhino environment."
        tb.Height = 60
        elements.append(tb)
        print(elements)
        for e in elements:
            print(e)
            win.AddElement(e)
        """