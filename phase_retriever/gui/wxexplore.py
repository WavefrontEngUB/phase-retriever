import wx
import wx.lib.agw.floatspin
import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift

class DataExplorer(wx.Panel):
    """Class to contain the controls for the exploration of the resulting data."""
    def __init__(self, parent):
        super().__init__(parent)

        self.init()

    def init(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.grid = grid = wx.propgrid.PropertyGrid(self, name="Explorer")

        grid.Append(wx.propgrid.PropertyCategory("Propagation bounds"))
        grid.Append(wx.propgrid.ArrayStringProperty("Min, max z (um)", name="bounds", value=["0", "8"]))

        #self.slider = slider = wx.Slider(self, id=wx.ID_ANY, minValue=0, maxValue=8,
        #        style=wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_AUTOTICKS, name="slider")
        self.spin = spin = wx.lib.agw.floatspin.FloatSpin(self, id=wx.ID_ANY, min_val=0, max_val=8,
                increment=0.01, digits=5)

        text = wx.StaticText(self, label="z position")

        sizer.Add(grid, 0, wx.EXPAND | wx.LEFT)
        sizer.Add(text, 0, wx.EXPAND | wx.LEFT)
        sizer.Add(spin, 0,  wx.CENTRE | wx.EXPAND)
        
        self.SetSizer(sizer)

    def GetSpin(self):
        return self.spin

    def GetZ(self):
        return self.spin.GetValue()
