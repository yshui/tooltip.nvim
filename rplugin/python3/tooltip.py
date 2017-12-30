import neovim
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import PangoCairo
from Xlib.protocol import request
from Xlib import display
import threading
import os

@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.thrd = threading.Thread(target=Gtk.main, name="gtk", daemon=True)
    @neovim.function('show_tooltip')
    def show_tooltip(self, args):
        # args: line, col, text markup
        w = Gtk.Window()
        w.type = Gtk.WindowType.POPUP
        layout = w.create_pango_layout(args[2])
        layout.set_width(-1)
        _, e = layout.get_pixel_extents()
        wid = int(os.environ['WINDOWID'])
        tline = float(nvim.eval("&lines"))
        tcol = float(nvim.eval("&columns"))
        g = request.GetGeometry(drawable=wid)
        x = int(g.x+g.width*args[1]/tcol)
        y = int(g.y+g.height*args[2]/tline)
        w.move(x, y)
        w.resize(e.width, e.height)
        w.show()
