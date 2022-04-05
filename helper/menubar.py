import tkinter as tk

class Menubar(tk.Menu):
    def __init__(self, master, bg, options):
        tk.Menu.__init__(self, master, background=bg, tearoff=False)
        self.master = master

        # Add all options
        for optname in options:
            cascade = tk.Menu(self, background=bg, tearoff=False)
            for menuname in options[optname]:
                command, accelerator = options[optname][menuname]
                cascade.add_command(label=menuname, 
                        command=command,
                        accelerator=accelerator)
            self.add_cascade(label=optname, menu=cascade)

