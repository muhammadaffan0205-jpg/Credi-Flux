# crediflux/views/coming_soon.py
import tkinter as tk
from tkinter import messagebox
from config import PALETTE

def show_coming_soon(parent, feature_name="This feature"):
    messagebox.showinfo("Coming Soon", f"{feature_name} will be available in the next update.")