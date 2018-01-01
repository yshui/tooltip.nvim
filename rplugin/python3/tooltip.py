import neovim
import gi
import cairo
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import PangoCairo
from Xlib.protocol import request, display
import threading
import os
import subprocess

@neovim.plugin
class Main(object):
    def __init__(self, vim):
        self.vim = vim
        self.d = display.Display()
        Gdk.threads_init()
        self.w = Gtk.Window(type = Gtk.WindowType.POPUP)
        self.w.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        self.w.connect("draw", self.draw)
        self.thrd = threading.Thread(target=Gtk.main, name="Gtk", daemon=True)
        self.thrd.start()

    def draw(self, w, cr):
        cr.set_source_rgb(self.bg.red, self.bg.green, self.bg.blue)
        cr.paint()
        cr.set_source_rgb(self.fg.red, self.fg.green, self.fg.blue)
        cr.move_to(self.bw, self.bw)
        PangoCairo.show_layout(cr, self.layout)
        return True

    @neovim.function('ShowTooltip', sync=True)
    def show_tooltip(self, args):
        # args: line, col, text markup
        if 'WINDOWID' not in os.environ:
            return

        self.bw = int(self.vim.vars.get("tooltip_border_width", 0))
        self.bg = Gdk.RGBA()
        self.bg.parse(self.vim.vars.get("tooltip_background", "black"))
        self.fg = Gdk.RGBA()
        self.fg.parse(self.vim.vars.get("tooltip_foreground", "white"))

        Gdk.threads_enter()
        # Create pango layout
        try:
            b, attr, text, accel = Pango.parse_markup(args[2], len(args[2]), "\0")
            self.layout = self.w.create_pango_layout(text)
            self.layout.set_attributes(attr)
            self.layout.set_width(-1)
        except GLib.GError:
            Gdk.threads_leave()
            return
        _, e = self.layout.get_pixel_extents()

        # Get the geometry of the terminal window
        wid = int(os.environ['WINDOWID'])
        g = request.GetGeometry(display=self.d, drawable=wid)
        coord = request.TranslateCoords(display=self.d, src_wid=wid, dst_wid=g.root, src_x=0, src_y=0)

        # Try to get the offset of current tmux pane
        offx = args[1]
        offy = args[0]
        tline = None
        tcol = None
        if 'TMUX' in os.environ:
            r = subprocess.run(["tmux", "display", "-p",
                "#{pane_left},#{pane_top},#{window_width},#{window_height}"],
                stdout=subprocess.PIPE)
            if r.returncode == 0:
                parts = list(map(float, r.stdout.split(b',')))
                offx = offx + parts[0]
                offy = offy + parts[1]
                tcol = parts[2]
                tline = parts[3]

        # If we didn't get the window size from tmux, try vim
        if tcol is None or tline is None:
            tline = float(self.vim.eval("&lines"))
            tcol = float(self.vim.eval("&columns"))

        # Calculate the offset of the tooltip
        offx = offx/tcol
        offy = offy/tline
        x = int(coord.x+g.width*offx)
        y = int(coord.y+g.height*offy)
        self.w.move(x, y)

        # Set the tooltip size to text size
        self.w.resize(e.width+self.bw*2, e.height+self.bw*2)
        self.w.show()
        Gdk.threads_leave()

    @neovim.function('HideTooltip')
    def hide_tooltip(self, args):
        Gdk.threads_enter()
        self.w.hide()
        Gdk.threads_leave()

    @neovim.autocmd('FocusLost', pattern='*')
    def on_focuslost(self):
        self.hide_tooltip([])
