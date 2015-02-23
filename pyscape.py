#!/usr/bin/env python2

"""
PyScape

A soundscape generation tool in Python

The sound files need to be mono, otherwise panning won't work!

Martin C. Doege
<mdoege@compuserve.com>

2014-12-16
"""

import gettext
from Tkinter import *
import tkMessageBox
from tkFileDialog import *
import os
import sys
import random
import math
import csv
import platform
from random import random as r
from os.path import basename
from time import time

import openal

try:
    from PIL import Image, ImageTk
except:
    Image, ImageTk = None, None
    print "Python Imaging Library not found;"
    print "background images disabled."


def get_size(a, b):
    """Get image dimensions for resize"""
    x1, y1, x2, y2 = [float(q) for q in a[0], a[1], b[0], b[1]]
    asp1 = x1 / y1
    asp2 = x2 / y2
    if asp1 > asp2:
        w = x2
        h = x2 / asp1
    else:
        h = y2
        w = y2 * asp1
    return int(w + .5), int(h + .5)


def getcol(r, n, z=False):
    """Attempt to read boolean from file"""
    try:
        return r[n] == "True"
    except:
        return z


def getcol_float(r, n, z=0.):
    """Attempt to read float from file"""
    try:
        return float(r[n])
    except:
        return z


class Source():
    """A sound source"""
    def __init__(s, n, x, y, fn, m, active=False, animated=False, mod_amp=False, offset=None, looping=True):
        cx, cy = x * m.pix[0], y * m.pix[1]
        s.n = n
        s.fn = fn
        s.m = m
        s.active = active
        s.solo = False
        s.selected = False
        s.animated = animated
        s.vx, s.vy = 0, 0
        s.speed = 5
        s.mod_amp = mod_amp
        if (offset is None) or (offset == 0.):
            s.offset = r() * 30.
        else:
            s.offset = offset
        s.source = m.contextlistener.get_source()
        s.source.buffer = openal.Buffer(fn)
        s.circ = m.w.create_oval(
            cx - m.cr, cy - m.cr, cx + m.cr, cy + m.cr, fill="white", tags="C%u" % n)
        s.text = m.w.create_text(cx, cy, text="%u" % n, tags="T%u" % n)
        m.w.tag_bind("C%u" % n, "<Button-2>", s.clicked)
        m.w.tag_bind("T%u" % n, "<Button-2>", s.clicked)
        m.w.tag_bind("C%u" % n, "<Button-1>", s.sel)
        m.w.tag_bind("T%u" % n, "<Button-1>", s.sel)
        m.w.tag_bind("C%u" % n, "<B1-Motion>", s.moved)
        m.w.tag_bind("T%u" % n, "<B1-Motion>", s.moved)
        m.w.tag_bind("C%u" % n, "<Button-3>", s.makesolo)
        m.w.tag_bind("T%u" % n, "<Button-3>", s.makesolo)
        s.update_color()
        s.x, s.y = cx, cy
        s.source.looping = looping
        s.update_parameters()

    def clicked(s, event=""):
        """Turn active on/off"""
        s.m.w.tag_raise("C%u" % s.n)
        s.m.w.tag_raise("T%u" % s.n)
        s.active = not s.active
        if s.active:
            s.m.but_act.select()
        else:
            s.m.but_act.deselect()
        s.update_color()
        s.play_or_stop()
        if event:
            s.m.dirty()

    def play_or_stop(s):
        """Play (if active) or stop the sound"""
        if s.active and not s.m.stop_it:
            s.source.play()
        else:
            s.source.stop()

    def makesolo(s, event=""):
        """Make sound solo"""
        s.solo = not s.solo
        if s.solo and s.selected:
            but_sol.select()
        else:
            but_sol.deselect()
        if s.solo:
            for p in s.m.par:
                if p.n != s.n:
                    p.solo = False
                    p.source.stop()
                    p.update_color()
            s.source.play()
        else:
            for p in s.m.par:
                p.play_or_stop()
                p.update_color()
        s.update_color()

    def moved(s, event=""):
        """Source has been dragged by the mouse"""
        x, y = event.x, event.y
        s.moveto(x, y)
        s.m.dirty()

    def moveto(s, x, y):
        """Move source to new position and update"""
        dx, dy = x - s.x, y - s.y
        s.m.w.move("C%u" % s.n, dx, dy)
        s.m.w.move("T%u" % s.n, dx, dy)
        s.x, s.y = x, y
        s.update_parameters()

    def update_parameters(s):
        """Calculate new position and gain"""
        sx = (math.pi * s.x / s.m.pix[0]) - math.pi / 2
        vol = 3. * (1. - (1. * s.y / s.m.pix[1]))**2
        x2 = math.sin(sx)
        y2 = math.cos(sx)
        s.source.position = [x2, y2, 0]
        s.gain_pure = max(0, vol)

    def sel(s, event=""):
        """Source has been selected, update properties area"""
        for p in s.m.par:
            p.selected = False
        s.selected = True
        if s.active:
            s.m.but_act.select()
        else:
            s.m.but_act.deselect()
        if s.solo:
            s.m.but_sol.select()
        else:
            s.m.but_sol.deselect()
        if s.animated:
            s.m.but_ani.select()
        else:
            s.m.but_ani.deselect()
        if s.mod_amp:
            s.m.but_modamp.select()
        else:
            s.m.but_modamp.deselect()
        if s.source.looping:
            s.m.but_trig.deselect()
        else:
            s.m.but_trig.select()
        s.m.lab.delete(0, END)
        s.m.lab.insert(0, basename(s.fn))
        for p in s.m.par:
            p.update_sel()

    def update_sel(s):
        """Change circle outline when selected"""
        if s.selected:
            s.m.w.itemconfig("C%u" % s.n, width=3, outline="turquoise")
        else:
            s.m.w.itemconfig("C%u" % s.n, width=1, outline="black")

    def update_color(s):
        """Change circle fill color"""
        if s.solo:
            cc = "blue"
            tc = "white"
        elif s.active:
            cc = "yellow"
            tc = "black"
        else:
            cc = "gray"
            tc = "white"
        s.m.w.itemconfig("C%u" % s.n, fill=cc)
        s.m.w.itemconfig("T%u" % s.n, fill=tc)
        s.m.update_title()

    def getdata(s):
        """Dump this source's parameters for saving"""
        return [s.n, "%.5f" % (1. * s.x / s.m.pix[0]), "%.5f" % (1. * s.y / s.m.pix[1]), s.active, s.fn, s.animated, s.mod_amp, "%.3f" % s.offset, s.source.looping > 0]


class Main():

    def __init__(self):
        random.seed()

        self.device = openal.Device()
        self.contextlistener = self.device.ContextListener()
        self.contextlistener.position = 0, 0, 0
        self.contextlistener.velocity = 0, 0, 0
        self.contextlistener.orientation = 0, 1, 0, 0, 0, 1

        self.master = Tk()

        self.pix = 800, 600		# canvas size
        self.cr = 20			# circle size
        self.ps_ext = '.pyscape'  # file extension for presets
        self.wpath = os.path.join("sounds", "fm3")  # initial path to WAV files
        self.preset_path = "presets"		# initial path to presets
        self.image_path = "backgrounds"  # initial path to background images
        # system global directory (not needed)
        self.global_dir = "/usr/share/pyscape"
        # look in current directory or shared directory?
        self.use_global = False

        # minutes until fadeout and suspend when the timer is active
        self.sleep_time = 30

        # user-level command to suspend the system:
        #  (define as an empty string if you do not want the system to suspend automatically)
        self.suspend_command = "systemctl suspend"

        if os.path.isdir(self.global_dir):
            self.wpath = os.path.join(self.global_dir, self.wpath)
            self.preset_path = os.path.join(self.global_dir, self.preset_path)
            self.image_path = os.path.join(self.global_dir, self.image_path)
            self.use_global = True
            gettext.install(
                "pyscape", localedir="/usr/share/locale", unicode=True)
        else:
            gettext.install("pyscape", localedir="mo", unicode=True)

        #######################################################################

        # Remember last directory used for images, sounds, and presets:
        self.image_dir = self.image_path
        self.sound_dir = self.wpath
        self.preset_dir = self.preset_path

        self.par = []

        # has the user changed the currently loaded preset?
        self.dirty_flag = False

        f1 = Frame(self.master)
        f1.pack(side=LEFT)
        self.w = Canvas(f1, width=self.pix[0], height=self.pix[1], bg="white")
        self.w.pack()

        f2 = Frame(self.master)
        f2.pack(side=RIGHT, fill=BOTH)
        self.gitem = LabelFrame(f2, text=_("Item properties"), padx=5, pady=5)
        self.gitem.pack(side=TOP, padx=10, pady=10, fill=BOTH)

        self.but_act = Checkbutton(
            self.gitem, text=_("Active"), command=self.tog_act)
        self.but_act.grid(row=1, pady=10, sticky=W)

        self.imfullpath = None

        self.load_background()
        self.titem = LabelFrame(
            f2, text=_("Item time behavior"), padx=5, pady=5)
        self.titem.pack(side=TOP, padx=10, pady=10, fill=BOTH)
        self.lab = Entry(self.gitem)
        self.lab.grid(row=0, pady=10)
        self.lab.delete(0, END)
        self.lab.insert(0, _("(no selection)"))

        self.but_sol = Checkbutton(
            self.gitem, text=_("Solo"), command=self.tog_sol)
        self.but_sol.grid(row=2, pady=10, sticky=W)

        self.do_ani = True

        self.but_ani = Checkbutton(
            self.titem, text=_("Animate"), command=self.tog_ani)
        self.but_ani.grid(row=0, pady=10, sticky=W)

        self.but_modamp = Checkbutton(
            self.titem, text=_("Modulate amplitude"), command=self.tog_modamp)
        self.but_modamp.grid(row=1, pady=10, sticky=W)

        self.but_trig = Checkbutton(
            self.titem, text=_("Trigger"), command=self.tog_trigger)
        self.but_trig.grid(row=2, pady=10, sticky=W)

        Button(f1, text=_("Save preset"), command=self.save_file).pack(
            side=RIGHT)
        Button(f1, text=_("Load preset"), command=self.load_file).pack(
            side=RIGHT)

        Button(f1, text=_("Load sound directory"), command=self.load_dir).pack(
            side=LEFT)
        Button(f1, text=_("Add sounds"), command=self.load_sounds).pack(
            side=LEFT)
        Button(f1, text=_("Remove unused sounds"), command=self.rm_inact).pack(
            side=LEFT)
        Button(f1, text=_("Arrange sounds"), command=self.sort_all).pack(
            side=LEFT)

        self.stop_it = False
        self.sleep_timer = False
        self.off_time = 0

        self.but_on = Button(
            f2, text=_("Play"), command=self.start_act, state=DISABLED, pady=20)
        self.but_off = Button(
            f2, text=_("Pause"), command=self.stop_act, pady=20)
        self.but_back = Button(
            f2, text=_("Change wallpaper"), command=self.select_background, pady=20)
        self.but_timer = Button(
            f2, text=_("Timer (off)"), command=self.toggle_timer, pady=20)

        self.but_timer.pack(side=BOTTOM, fill=X)
        self.but_back.pack(side=BOTTOM, fill=X, pady=10)
        self.but_off.pack(side=BOTTOM, fill=X)
        self.but_on.pack(side=BOTTOM, fill=X, pady=10)
        demos = (
            (10, 11, 13, 14, 15, 16), (3, 7), (6, 11), (7, 16), (4, 10, 17))

        if len(sys.argv) > 1:
            print _("Loading"), sys.argv[1]
            self.load_file(mypath=sys.argv[1])
        else:
            self.load_dir(mypath=self.wpath)
            if len(self.par) > 16:
                for j in random.choice(demos):
                    self.par[j - 1].clicked()
                    self.par[j - 1].animated = True
                    if r() < .25:
                        self.par[j - 1].mod_amp = True

        self.master.after(50, self.update_all)

        mainloop()

    def dirty(self):
        """Set application state to dirty"""
        self.dirty_flag = True

    def clean(self):
        """Set application state to clean"""
        self.dirty_flag = False

    def update_title(self):
        """Update window title"""
        for p in self.par:
            if p.solo:
                self.master.title(
                    _("Playing %s; use RMB to quit solo mode") % basename(p.fn))
                return
        a = len(self.par)
        b = len([x for x in self.par if x.active])
        self.master.title(
            _("%u of %u sources active (LMB=select/drag; MMB=toggle on/off; RMB=solo)") % (b, a))

    def load_background(self, f=None, imfull=None):
        """Load background image"""

        self.images = (
            ("jungle.pyscape",     "Poco_azul_800x600.jpg"),
            ("sea.pyscape",
             "Cabo_Espichel,_Portugal,_2012-08-18,_DD_08_800x600.jpg"),
            ("water.pyscape",
             "Elakala_Waterfalls_pub5_-_West_Virginia_-_ForestWander_800x600.jpg"),
            ("explosions.pyscape", "USAF_EOD_explosion_800x600.jpg"),
            ("beach.pyscape",
             "Anse_Source_d_Argent_2-La_Digue_800x600.jpg"),
            ("rain.pyscape",
             "Flickr - Rainbirder - Square-tailed Black Bulbul ( Hypsipetes ganeesa humii) in the rain_800x600.jpg"),
            ("village.pyscape",    "Rigi_Kulm_cows_2012_800x600.jpg"),
            ("plane.pyscape",
             "Thai_Airways_Economy_Class_Cabin_800x600.jpg"),
        )
        if Image is None:
            return
        i = "Buddha_in_shilparamam_800x600.jpg"
        if f:
            for a, b in images:
                if a in f:
                    i = b
        im = os.path.join(self.image_path, i)
        xa, ya = 0, 0
        if imfull:
            imfile = Image.open(imfull)
            self.imfullpath = imfull
            if imfile.size[0] > self.pix[0] or imfile.size[1] > self.pix[1]:
                xd, yd = get_size(imfile.size, self.pix)
                imfile = imfile.resize((xd, yd), Image.ANTIALIAS)
                xa = (self.pix[0] - xd) / 2
                ya = (self.pix[1] - yd) / 2
        else:
            imfile = Image.open(im)
            self.imfullpath = im
        self.photo = ImageTk.PhotoImage(imfile)
        self.w.create_image(xa, ya, image=self.photo, anchor=NW, tags="BACK")
        self.w.tag_lower("BACK")
        cc = imfile.getpixel((0, 0))
        self.w.config(bg="#%02x%02x%02x" % (cc[0], cc[1], cc[2]))

    def tog_act(self):
        """Toggle sound active flag"""
        for p in self.par:
            if p.selected:
                p.active = not p.active
                p.play_or_stop()
                p.update_color()
                self.dirty()

    def tog_sol(self):
        """Toggle sound solo flag"""
        for p in self.par:
            if p.selected:
                p.makesolo()

    def tog_ani(self):
        """Toggle sound animated flag"""
        for p in self.par:
            if p.selected:
                p.animated = not p.animated
                self.dirty()

    def tog_modamp(self):
        """Toggle sound amplitude modulation flag"""
        for p in self.par:
            if p.selected:
                p.mod_amp = not p.mod_amp
                self.dirty()

    def tog_trigger(self):
        """Toggle sound triggered flag"""
        for p in self.par:
            if p.selected:
                p.source.looping = not p.source.looping
                self.dirty()
                if p.source.looping:
                    p.source.play()
                else:
                    p.source.stop()

    def save_file(self):
        """Save as preset"""
        mypath = asksaveasfilename(filetypes=[(_("PyScape presets"), self.ps_ext), (_(
            "All files"), ".*")], defaultextension=self.ps_ext, initialdir=self.preset_dir)
        if not len(mypath):
            return
        with open(mypath, 'wb') as csvfile:
            wr = csv.writer(csvfile)
            for p in self.par:
                wr.writerow(p.getdata())
            if self.imfullpath:
                wr.writerow(("background", self.imfullpath))
        self.preset_dir = os.path.dirname(mypath)
        self.clean()

    def load_file(self, mypath=None):
        """Load preset"""

        if not mypath and self.dirty_flag:
            if not tkMessageBox.askokcancel(_("Load preset"), _("You have unsaved changes.\nProceed?")):
                return
        if not mypath:
            mypath = askopenfilename(filetypes=[(_("PyScape presets"), self.ps_ext), (_(
                "All files"), ".*")], initialdir=self.preset_dir)
            if not len(mypath):
                return
        for p in self.par:
            n = p.n
            p.active = False
            p.play_or_stop()
            self.w.delete("C%u" % n)
            self.w.delete("T%u" % n)
        self.par = []
        self.update_title()
        self.load_background(f=mypath)
        try:
            with open(mypath, 'rb') as csvfile:
                wr = csv.reader(csvfile)
                for row in wr:
                    if row[0] == "background":
                        try:
                            self.load_background(imfull=row[1])
                        except:
                            tkMessageBox.showwarning(
                                _("Load preset"),
                                _("Could not load background image %s") % row[
                                    1]
                            )
                        continue
                    act = (row[3] == 'True')
                    fname = row[4]
                    if platform.system() == "Windows" and '/' in fname:
                        fname = fname.split('/')
                        fname = os.path.join(fname)
                    if platform.system() == "Linux" and self.use_global and fname[0] != '/':
                        fname = os.path.join(self.global_dir, fname)
                    try:
                        self.par.append(Source(
                            int(row[0]), float(row[1]), float(row[2]), fname, self, active=act,
                            animated=getcol(row, 5), mod_amp=getcol(row, 6), offset=getcol_float(row, 7),
                            looping=getcol(row, 8, z=True)
                        ))
                    except:
                        tkMessageBox.showwarning(
                            _("Load preset"),
                            _("Could not load sound file %s") % fname
                        )
        except:
            tkMessageBox.showerror(
                _("Load preset"),
                _("Could not read preset file %s") % mypath
            )
            return
        self.start_act()
        if self.par:
            self.par[0].sel()
        self.update_title()
        self.preset_dir = os.path.dirname(mypath)
        self.clean()

    def sort_all(self):
        """Arrange sources on screen by number"""
        xp, yp = 2 * self.cr, 2 * self.cr
        for p in self.par:
            p.moveto(xp, yp)
            xp += 3 * self.cr
            if xp > self.pix[0] - 2 * self.cr:
                xp = 2 * self.cr
                yp += 3 * self.cr

    def load_dir(self, mypath=None):
        """Open directory with sound files"""

        if not mypath and self.dirty_flag:
            if not tkMessageBox.askokcancel(_("Load sound directory"), _("You have unsaved changes.\nProceed?")):
                return
        if not mypath:
            mypath = askdirectory(initialdir=self.sound_dir)
            if not len(mypath):
                return
        if self.par:
            for p in self.par:
                n = p.n
                p.active = False
                p.play_or_stop()
                self.w.delete("C%u" % n)
                self.w.delete("T%u" % n)
        self.par = []
        self.update_title()
        try:
            fn = [x for x in os.listdir(mypath) if (
                x[0] != '.' and ".wav" in x)]
        except:
            tkMessageBox.showwarning(
                _("Load sound directory"),
                _("Directory %s could not be read") % mypath
            )
            return
        fn.sort()
        for n, f in enumerate(fn):
            self.par.append(Source(
                n + 1, .5, .5, os.path.join(mypath, f),
                self
            ))
        self.sort_all()
        if self.par:
            self.par[0].sel()
        else:
            tkMessageBox.showinfo(
                _("Load sound directory"),
                _("No sounds found in directory %s") % mypath
            )
        self.update_title()
        self.sound_dir = mypath
        self.clean()

    def rm_inact(self):
        """Delete all currently inactive sounds"""

        for p in self.par:
            if not p.active:
                self.w.delete("C%u" % p.n)
                self.w.delete("T%u" % p.n)
        par2 = []
        for p in self.par:
            if p.active:
                par2.append(p)
        self.par = par2
        self.update_title()

    def load_sounds(self, mypath=None):
        """Add one or more sounds to the current scene"""
        if not mypath:
            mypath = askopenfilenames(filetypes=[(_("WAV audio files"), ".wav"), (_(
                "All files"), ".*")], initialdir=self.sound_dir)
            if not len(mypath):
                return
        n = 0
        for p in self.par:
            if p.n >= n:
                n = p.n + 1
        for f in mypath:
            if len(mypath) > 1:
                xpos = r() / 2. + .25
            else:
                xpos = .5
            try:
                self.par.append(Source(n, xpos, .5, f, self, active=True))
            except:
                tkMessageBox.showerror(
                    _("Add sounds"),
                    _(
                        "There was a problem with the sound file %s\nFormats other than WAV probably will not work.") % f
                )
            self.w.tag_raise("C%u" % n)
            self.w.tag_raise("T%u" % n)
            self.par[-1].play_or_stop()
            n += 1
        self.update_title()
        self.sound_dir = os.path.dirname(mypath[0])
        self.dirty()

    def start_act(self):
        """Start performance"""
        self.stop_it = False
        self.do_ani = True
        self.but_on.config(state=DISABLED)
        self.but_off.config(state=NORMAL)
        for p in self.par:
            p.play_or_stop()

    def stop_act():
        """Pause performance"""
        self.stop_it = True
        self.do_ani = False
        self.but_off.config(state=DISABLED)
        self.but_on.config(state=NORMAL)
        for p in self.par:
            p.play_or_stop()

    def select_background(self):
        """Select a new background image"""
        mypath = askopenfilename(filetypes=[(_("JPEG images"), ".jpg"), (_(
            "PNG images"), "*.png"), (_("All files"), ".*")], initialdir=self.image_dir)
        if not len(mypath):
            return
        try:
            self.load_background(imfull=mypath)
        except:
            tkMessageBox.showerror(
                _("Change wallpaper"),
                _("Could not load image %s") % mypath
            )
        self.image_dir = os.path.dirname(mypath)
        self.dirty()

    def toggle_timer(self):
        """Turn the sleep timer on and off"""
        self.sleep_timer = not self.sleep_timer
        if self.sleep_timer:
            self.off_time = time() + 60 * self.sleep_time
        else:
            self.off_time = 0
            self.contextlistener.gain = 1.

    def update_all(self):
        """Move (or otherwise update) all sound sources regularly"""
        t = ''
        if self.sleep_timer:
            dofftime = self.off_time - time()
            t = _("Timer (%u min)") % int(dofftime / 60. + .5)
            # just in case the user suspends the system while the timer is
            # running...
            if dofftime < 0:
                self.stop_act()
                self.contextlistener.gain = 1.
                self.sleep_timer = False
                self.off_time = 0
            else:
                if dofftime < 60:
                    self.contextlistener.gain = (dofftime / 60.)**2.5
                if dofftime < 3:
                    self.stop_act()
                    self.contextlistener.gain = 1.
                    t = _("Timer (stopped)")
                    self.sleep_timer = False
                    if self.suspend_command:
                        os.system(self.suspend_command)
        else:
            if not self.off_time:
                t = _("Timer (off)")
        if t:
            self.but_timer.config(text=t)

        is_solo = False
        for p in self.par:
            if p.solo:
                is_solo = True
        for p in self.par:
            if p.mod_amp:
                p.source.gain = p.gain_pure * \
                    (.5 + .25 * (1 + math.sin(time() / 2 - p.offset)))**2
            else:
                p.source.gain = p.gain_pure
            if not p.source.looping and p.active and not stop_it:
                if p.source.state != openal._al.PLAYING:
                    if random.expovariate(1) > 4 and (not is_solo or p.solo):
                        pitch = random.normalvariate(1., .3)
                        pitch = min(2., max(pitch, .5))
                        p.source.pitch = pitch
                        p.source.play()
                        # print "triggering", p.n, "pitch", p.source.pitch
            if p.animated and self.do_ani:
                p.vx += (r() - .5) * p.speed
                p.vy += (r() - .5) * p.speed
                p.moveto(p.x + p.vx, p.y + p.vy)
                if p.x > self.pix[0]:
                    p.vx = -abs(p.vx)
                if p.y > self.pix[1]:
                    p.vy = -abs(p.vy)
                if p.x < 0:
                    p.vx = abs(p.vx)
                if p.y < 0:
                    p.vy = abs(p.vy)
                sp = (p.vx**2 + p.vy**2)
                if sp > p.speed**2:
                    p.vx *= .5
                    p.vy *= .5
                for q in self.par:
                    if q.animated:
                        dist = (q.x - p.x)**2 + (q.y - p.y)**2
                        if dist > 1:
                            p.vx += (p.x - q.x) / dist
                            p.vy += (p.y - q.y) / dist
        self.master.after(50, self.update_all)

def main():
    Main()

if __name__ == "__main__":
    main()
