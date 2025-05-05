
import tkinter as tk
from tkinter import messagebox
from threading import Thread
from robot_updater import run_batch_updates  # assumes robot_updater.py is in same folder

def start_update():
    load_ids = [e.get().strip() for e in load_entries if e.get().strip()]
    driver_ids = [e.get().strip() for e in driver_entries if e.get().strip()]
    if len(load_ids) != len(driver_ids):
        messagebox.showerror("Mismatch", "Each Load ID must have a matching Driver ID.")
        return
    if not load_ids:
        messagebox.showwarning("No Data", "Please enter at least one Load ID and Driver ID.")
        return
    Thread(target=lambda: run_batch_updates(load_ids, driver_ids)).start()

root = tk.Tk()
root.title("Robot Updater UI")

tk.Label(root, text="Enter up to 15 Load IDs and Driver IDs").grid(row=0, column=0, columnspan=2)

load_entries = []
driver_entries = []

for i in range(15):
    load_e = tk.Entry(root, width=30)
    driver_e = tk.Entry(root, width=30)
    load_e.grid(row=i+1, column=0, padx=5, pady=2)
    driver_e.grid(row=i+1, column=1, padx=5, pady=2)
    load_entries.append(load_e)
    driver_entries.append(driver_e)

tk.Button(root, text="Run Batch Update", command=start_update).grid(row=17, column=0, columnspan=2, pady=10)

root.mainloop()
