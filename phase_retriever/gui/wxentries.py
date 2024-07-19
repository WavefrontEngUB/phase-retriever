import wx
import wx.propgrid

DEFAULT_WAVELENGTH = 0.52  # um
DEFAULT_PIXELSIZE = 0.043  # um
DEFAULT_NITERATIONS = 120  # iterations
DEFAULT_WINDOWSIZE = 256   # px
DEFAULT_WINDOWSIZE_R = 64  # px
DEFAULT_BANDWIDTH = 0      # px
DEFAULT_ROISIZE = 64       # px

choices = { "ext": ["png", "npy"],
            "mode": ["vectorial", "scalar"]
          }

# class TextedEntry(wx.Panel):
#     def __init__(self, parent, text):
#         super().__init__(parent)
#
#         self.init(text)
#
#     def init(self, text):
#         sizer = wx.BoxSizer(wx.HORIZONTAL)
#
#         label = wx.StaticText(self, label=text)
#
#         self.entry = entry = wx.TextCtrl(self)
#
#         sizer.Add(entry, 0, wx.LEFT | wx.EXPAND)
#         sizer.Add(label, 0, wx.LEFT | wx.EXPAND)
#
#         self.SetSizer(sizer)
#
#     def ChangeValue(self, value):
#         self.entry.SetValue(value)

class ButtonsPane(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.dirname = None

        self.init()

    def init(self):

        button_size = (250, 30)

        factor = 0.4
        button_size_small = (int(button_size[0]*factor), button_size[1])
        button_size_large = (int(button_size[0]*(1-factor)), button_size[1])

        self.button = button = wx.Button(self, label="Search directory",
                                         size=button_size)
        self.cent_butt = centbut = wx.Button(self, label="Center beam",
                                             size=button_size)
        self.swap_butt = swapbut = wx.Button(self, label="Swap beams",
                                             size=button_size)
        self.auto_butt = autobut = wx.Button(self, label="Check bandwidth",
                                             size=button_size)
        self.ret_butt = ret_butt = wx.Button(self, label="Begin retrieval",
                                             size=button_size)
        self.export_butt = export_butt = wx.Button(self, label="Export results",
                                                   size=button_size)

        # sizerC = wx.BoxSizer(wx.HORIZONTAL)
        # sizerC.Add(centbut, 0, wx.CENTRE)
        # sizerC.Add(swapbut, 0, wx.CENTRE)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(button, 0, wx.CENTRE)
        sizer.Add(swapbut, 0, wx.CENTRE)
        sizer.Add(centbut, 0, wx.CENTRE)
        sizer.Add(autobut, 0, wx.CENTRE)
        sizer.Add(ret_butt, 0, wx.CENTRE)
        sizer.Add(export_butt, 0, wx.CENTRE)

        # sizer2 = wx.BoxSizer(wx.VERTICAL)
        # sizer2.AddSpacer(button_size[1])
        # sizer2.Add(swapbut, 0, wx.CENTRE)
        # sizer2.AddSpacer(button_size[1])
        # sizer2.AddSpacer(button_size[1])
        # sizer2.AddSpacer(button_size[1])

        # hsizer = wx.BoxSizer(wx.HORIZONTAL)
        # hsizer.AddSpacer(button_size_small[0]//2)
        # hsizer.Add(sizer, 0)
        # hsizer.Add(sizer2, 0)

        self.SetSizer(sizer)


class wxEntryPanel(wx.Panel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.init()

    def init(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # To hold all the data entries, we creat a grid (wokrsheet-like)
        self.pgrid = pgrid = wx.propgrid.PropertyGrid(self, name="EntryPanel")

        pgrid.Append(wx.propgrid.PropertyCategory("Dataset path"))
        pgrid.Append(wx.propgrid.StringProperty("Working Directory",
                                                name="path", value=""))
        pgrid.Append(wx.propgrid.EnumProperty("Input files extension", name="ext",
                                              choices=wx.propgrid.PGChoices(choices["ext"])))
        pgrid.Append(wx.propgrid.PropertyCategory("Beam location"))
        pgrid.Append(wx.propgrid.IntProperty("Window size", name="window_size",
                                             value=DEFAULT_WINDOWSIZE))
        pgrid.Append(wx.propgrid.ArrayStringProperty("Window center",
                                                     name="window_center",
                                                     value=["0", "0"]))
        pgrid.Append(wx.propgrid.ArrayStringProperty("Ref. center",
                                                     name="window_centerR",
                                                     value=["0", "0"]))
        pgrid.Append(wx.propgrid.IntProperty("Ref. size", name="window_sizeR",
                                             value=DEFAULT_WINDOWSIZE_R))
        pgrid.Append(wx.propgrid.PropertyCategory("Measurement properties"))
        pgrid.Append(wx.propgrid.FloatProperty("Wavelength (um)", name="lambda",
                                               value=DEFAULT_WAVELENGTH))
        pgrid.Append(wx.propgrid.FloatProperty("Pixel size (um)", name="pixel_size",
                                               value=DEFAULT_PIXELSIZE))
        # pgrid.Append(wx.propgrid.EnumProperty("Mode", name="mode",
        #                                       choices=wx.propgrid.PGChoices(choices["mode"])))
        pgrid.Append(wx.propgrid.PropertyCategory("Retrieving configuration"))
        pgrid.Append(wx.propgrid.IntProperty("Number of iterations", name="n_iter",
                                             value=DEFAULT_NITERATIONS))
        pgrid.Append(wx.propgrid.ArrayStringProperty("Phase origin",
                                                     name="phase_origin",
                                                     value=["0", "0"]))
        pgrid.Append(wx.propgrid.FloatProperty("Bandwidth (pixels)",
                                               name="bandwidth",
                                               value=DEFAULT_BANDWIDTH))
        pgrid.Append(wx.propgrid.PropertyCategory("Exploration"))
        pgrid.Append(wx.propgrid.IntProperty("ROI size", name="roi",
                                             value=DEFAULT_ROISIZE))
        # pgrid.Append(wx.propgrid.IntProperty("Z position", name="z_exp",
        #                                      value=0))

        self.polEntry = polEntry = ButtonsPane(self)

        sizer.Add(pgrid, 2, wx.EXPAND | wx.RIGHT)
        sizer.Add(polEntry, 1, wx.EXPAND | wx.RIGHT)
        self.SetSizer(sizer)

        # Dictionary with pairs of key-pointer to each property in the grid
        self.iter = {
                "lamb": pgrid.GetPropertyByName("lambda"),
                "pixel_size": pgrid.GetPropertyByName("pixel_size"),
                "n_iter": pgrid.GetPropertyByName("n_iter"),
                "window_size": pgrid.GetPropertyByName("window_size"),
                "window_center": pgrid.GetPropertyByName("window_center"),
                "phase_origin": pgrid.GetPropertyByName("phase_origin"),
                "window_sizeR": pgrid.GetPropertyByName("window_sizeR"),
                "window_centerR": pgrid.GetPropertyByName("window_centerR"),
                "bandwidth": pgrid.GetPropertyByName("bandwidth"),
                "path": pgrid.GetPropertyByName("path"),
                "ext": pgrid.GetPropertyByName("ext"),
                # "mode": pgrid.GetPropertyByName("mode"),
                "roi": pgrid.GetPropertyByName("roi"),
                # "z_exp": pgrid.GetPropertyByName("z_exp")
                }

    def GetButton(self, name):
        if name == "search":
            button = self.polEntry.button
        elif name == "center":
            button = self.polEntry.cent_butt
        elif name == "swap":
            button = self.polEntry.swap_butt
        elif name == "autoadjust":
            button = self.polEntry.auto_butt
        elif name == "begin":
            button = self.polEntry.ret_butt
        elif name == "export":
            button = self.polEntry.export_butt
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

    def GetValue(self, name):
        if name not in self.iter:
            raise NameError(f"Property {name} does not exist")
        ptr = self.iter[name]
        value = self.pgrid.GetPropertyValue(ptr)
        if name in choices.keys():
            value = choices[name][value]
        return value