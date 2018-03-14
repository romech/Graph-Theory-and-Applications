import tkinter as tk
from tkinter import filedialog
import os

app_window = tk.Tk()
txt_box = tk.Label(app_window, text='''1. Open an .osm file
2. Wait ~ 1 minute
3. Program  produces 3 files:
 - adj_list.txt
 - light_map.svg
 - full_map.pdf
4. Program closes''', height=8, width=30)
 
txt_box.config(font=("Sans", 14), justify=tk.LEFT)
txt_box.pack()
app_window.title('OSM Processing')
# Build a list of tuples for each file type the file dialog should display
my_filetypes = [('Open Street Map file', '.osm'), ('all files', '.*')]

def reqestFile():
    return filedialog.askopenfilename(parent=app_window,
                                        initialdir=os.getcwd(),
                                        title="Please select a file:",
                                        filetypes=my_filetypes)
if __name__ == "__main__":
    app_window.mainloop()
