import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory
import multiprocessing as mp
from .beamexplorer import BeamPropWin

class ProgressWindow(tk.Toplevel):
    def __init__(self, nsteps):
        tk.Toplevel.__init__(self)

        # Text de la barra de progrés
        self.text = ttk.Label(self, text="Exporting results...")
        self.nsteps = nsteps
        # Barra de progrés
        self.pvar = tk.IntVar()
        self.pbar = ttk.Progressbar(self, maximum=nsteps, variable=self.pvar)
        self.text.pack(anchor="w", fill="x")
        self.pbar.pack(fill="x")

    def update_bar(self, i):
        self.pvar.set(i)
        if i >= self.nsteps-1:
            self.quit()

    def quit(self):
        self.destroy()
        self.update()

class ExportWindow(tk.Toplevel):
    """Finestra per a exportar les imatges. Compta amb la mínima i màxima distància,
    el nombre d'imatges i diferents selectors per a desar vídeo i a quins fps..."""

    def __init__(self, config, lamb, video_fun):
        tk.Toplevel.__init__(self)
        self.config = config
        self.video_fun = video_fun
        self.lamb = lamb
        
        # Explorer
        self.explorer = BeamPropWin(self, 1, text="Propagation properties")
        self.explorer.pack_widgets()

        self.explorer.pack(fill="y")

        # Botó
        self.button = ttk.Button(self, text="Export", command=self.export_dialog)
        self.button.pack()

    def export_dialog(self, *args):
        # Paràmetres de la propagació
        vals_dict = self.explorer.get_values()
        self.n_ims = vals_dict["n_ims"]
        delta_z = vals_dict["delta_z"]
        video = vals_dict["video"]
        fps = vals_dict["fps"]
        self.queue = mp.Queue()
        self.p = mp.Process(target=self.video_fun, args=(*self.config, self.n_ims, 
                            delta_z, None, self.lamb, self.queue, video, fps))
        self.p.start()
        # Creem una finestra de progrés
        self.progress = ProgressWindow(self.n_ims)

        # Finalment, revisem com va el procés
        self.monitor_process()

    def monitor_process(self, *args):
        qsize = self.queue.qsize()
        if qsize > 0:
            for i in range(qsize):
                i = self.queue.get()
                self.progress.update_bar(i)
                if i >= self.n_ims-1:
                    self.quit()
        self.after(100, self.monitor_process)

    def quit(self):
        self.p.join()
        self.destroy()
        self.update()
