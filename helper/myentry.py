import tkinter as tk
import tkinter.ttk as ttk

class myEntry(ttk.Frame):
    """Custom Entry widget with both a label and an entry box."""
    def __init__(self, master, text="", def_entry="", state=tk.NORMAL,
            textvariable=None):
        self.master = master
        ttk.Frame.__init__(self, master)

        # Add text label
        self.text = ttk.Label(self, text=text)
        # Add the entry box
        self.entry = ttk.Entry(self, state=state, textvariable=textvariable)
        self.entry.insert(0, def_entry)

        # Pack it up
        self.text.pack(side=tk.TOP, anchor=tk.W)
        self.entry.pack(side=tk.BOTTOM, anchor=tk.W)

    def get(self):
        """Get the contents of the entry box."""
        content = self.entry.get()
        return content

    def change_text(self, newtext):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, newtext)

    def configure(self, state):
        self.entry.configure(state=state)
        self.text.configure(state=state)

    def set_callback(self, fun):
        self.entry.configure(validate="all", validatecommand=fun)
