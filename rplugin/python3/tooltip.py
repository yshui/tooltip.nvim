import neovim
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import PangoCairo
from Xlib.protocol import request, display
import threading
import os

@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.d = display.Display()
        Gdk.threads_init()
        self.thrd = threading.Thread(target=Gtk.main, name="Gtk", daemon=True)
        self.thrd.start()

    @neovim.function('ShowTooltip')
    def show_tooltip(self, args):
        # args: line, col, text markup
        Gdk.threads_enter()
        w = Gtk.Window(type = Gtk.WindowType.POPUP)
        w.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)

        b, attr, text, accel = Pango.parse_markup(args[2], len(args[2]), "\0")
        if not b:
            return

        layout = w.create_pango_layout(text)
        layout.set_attributes(attr)
        layout.set_width(-1)
        _, e = layout.get_pixel_extents()
        wid = int(os.environ['WINDOWID'])
        tline = float(self.vim.eval("&lines"))
        tcol = float(self.vim.eval("&columns"))
        g = request.GetGeometry(display=self.d, drawable=wid)
        x = int(g.x+g.width*args[1]/tcol)
        y = int(g.y+g.height*args[0]/tline)
        w.move(x, y)
        w.resize(e.width, e.height)
        w.show()
        Gdk.threads_leave()
        self.vim.command("echom 'returning'")
