import wx
import wx.propgrid

class TextedEntry(wx.Panel):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.init(text)

    def init(self, text):
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, label=text)

        self.entry = entry = wx.TextCtrl(self)

        sizer.Add(entry, 0, wx.LEFT | wx.EXPAND)
        sizer.Add(label, 0, wx.LEFT | wx.EXPAND)

        self.SetSizer(sizer)

    def ChangeValue(self, value):
        self.entry.SetValue(value)

class DirectorySelector(wx.Panel):
    def __init__(self, parent, text):
        super().__init__(parent)

        self.dirname = None

        self.init(text)

    def init(self, text):
        # TODO: Remove references to old path indicator box
        sizer = wx.BoxSizer(wx.VERTICAL)
        #hsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.button = button = wx.Button(self, label="Search directory")
        self.auto_butt = autobut = wx.Button(self, label="Autoadjust")
        self.ret_butt = ret_butt = wx.Button(self, label="Begin retrieval")

        #self.info = info = TextedEntry(self, text)

        #hsizer.Add(info, 1, wx.CENTRE | wx.EXPAND)

        #sizer.Add(hsizer,  0, wx.CENTRE | wx.EXPAND)
        sizer.Add(button,   0, wx.CENTRE)
        sizer.Add(autobut,  0, wx.CENTRE)
        sizer.Add(ret_butt, 0, wx.CENTRE)

        self.SetSizer(sizer)

class wxEntryPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()

    def init(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Name and directory of the polarimetric images
        self.polEntry = polEntry = DirectorySelector(self, "Working directory")

        # To hold all the data entries, we creat a grid (wokrsheet-like)
        self.pgrid = pgrid = wx.propgrid.PropertyGrid(self, name="EntryPanel")

        pgrid.Append(wx.propgrid.PropertyCategory("Dataset path"))
        pgrid.Append(wx.propgrid.StringProperty("Working Directory", name="path", value=""))
        pgrid.Append(wx.propgrid.PropertyCategory("Measurement properties"))
        pgrid.Append(wx.propgrid.FloatProperty("Wavelength (um)", name="lambda", value=0.52))
        pgrid.Append(wx.propgrid.FloatProperty("Pixel size (um)", name="pixel_size", value=3.75))
        pgrid.Append(wx.propgrid.PropertyCategory("Retrieving configuration"))
        pgrid.Append(wx.propgrid.IntProperty("Number of iterations", name="n_iter", value=120))
        pgrid.Append(wx.propgrid.IntProperty("Window size", name="window_size", value=256))
        pgrid.Append(wx.propgrid.ArrayStringProperty("Window center", name="window_center", value=["0", "0"]))
        pgrid.Append(wx.propgrid.ArrayStringProperty("Phase origin", name="phase_origin", value=["0", "0"]))
        pgrid.Append(wx.propgrid.FloatProperty("Bandwidth (pixels)", name="bandwidth", value=20))

        sizer.Add(pgrid, 1, wx.EXPAND | wx.LEFT)
        sizer.Add(polEntry, 1, wx.EXPAND | wx.LEFT)
        self.SetSizer(sizer)

        # Dictionary with pairs of key-pointer to each property in the grid
        self.iter = {
                "lamb": pgrid.GetPropertyByName("lambda"),
                "pixel_size": pgrid.GetPropertyByName("pixel_size"),
                "n_iter": pgrid.GetPropertyByName("n_iter"),
                "window_size": pgrid.GetPropertyByName("window_size"),
                "window_center": pgrid.GetPropertyByName("window_center"),
                "phase_origin": pgrid.GetPropertyByName("phase_origin"),
                "bandwidth": pgrid.GetPropertyByName("bandwidth"),
                "path": pgrid.GetPropertyByName("path")
                }

    def GetButton(self, name):
        if name == "search":
            button = self.polEntry.button
        elif name == "autoadjust":
            button = self.polEntry.auto_butt
        elif name == "begin":
            button = self.polEntry.ret_butt
        return button

    def GetTextEntry(self, *args):
        return self.polEntry.info

    def GetValues(self):
        values = {}
        for name in self.iter:
            ptr = self.iter[name]
            values[name] = self.pgrid.GetPropertyValue(ptr)

        return values

    def GetPgrid(self):
        return self.pgrid

    def SetValue(self, **props):
        for name in props:
            if name not in self.iter:
                raise NameError(f"Property {name} does not exist")
            ptr = self.iter[name]
            self.pgrid.SetPropertyValue(ptr, props[name])
