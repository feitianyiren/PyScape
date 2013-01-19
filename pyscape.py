#!/usr/bin/env python2

"""
PyScape

A soundscape generation tool in Python

The sound files need to be mono, otherwise panning won't work!

Martin C. Doege
<mdoege@compuserve.com>

2013-01-19
"""

from Tkinter import *
import tkMessageBox
from tkFileDialog import *
import os, sys, random, math, csv, platform
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

random.seed()

device = openal.Device()
contextlistener = device.ContextListener()
contextlistener.position = 0, 0, 0
contextlistener.velocity = 0, 0, 0
contextlistener.orientation = 0, 1, 0, 0, 0, 1

master = Tk()

pix = 800, 600		# canvas size
cr = 20			# circle size
ps_ext = '.pyscape'	# file extension for presets
wpath = os.path.join("sounds", "fm3")	# initial path to WAV files
preset_path = "presets"		# initial path to presets
image_path = "backgrounds"	# initial path to background images

############################################################################

# Remember last directory used for images, sounds, and presets:
image_dir = image_path
sound_dir = wpath
preset_dir = preset_path

par = []

def update_title():
	"Update window title"
	for p in par:
		if p.solo:
			master.title("Playing %s; use RMB to quit solo mode" % basename(p.fn))
			return
	a = len(par)
	b = len([x for x in par if x.active])
	master.title("%u of %u sources active (LMB=select/drag; MMB=toggle on/off; RMB=solo)" % (b, a))

f1 = Frame(master)
f1.pack(side = LEFT)
w = Canvas(f1, width=pix[0], height=pix[1], bg="white")
w.pack()

def get_size(a, b):
	"Get image dimensions for resize"
	x1, y1, x2, y2 = [float(q) for q in a[0],a[1],b[0],b[1]]
	asp1 = x1/y1
	asp2 = x2/y2
	if asp1 > asp2:
		w = x2
		h = x2 / asp1
	else:
		h = y2
		w = y2 * asp1
	return int(w+.5), int(h+.5)

imfullpath = None
def load_background(f = None, imfull = None):
	"Load background image"
	global photo, imfullpath

	images = (
		("jungle.pyscape",     "Poco_azul_800x600.jpg"),
		("sea.pyscape",        "Cabo_Espichel,_Portugal,_2012-08-18,_DD_08_800x600.jpg"),
		("water.pyscape",      "Elakala_Waterfalls_pub5_-_West_Virginia_-_ForestWander_800x600.jpg"),
		("explosions.pyscape", "USAF_EOD_explosion_800x600.jpg"),
	)
	if Image == None:
		return
	i = "Buddha_in_shilparamam_800x600.jpg"
	if f:
		for a,b in images:
			if a in f:
				i = b
	im = os.path.join("backgrounds", i)
	xa, ya = 0, 0
	if imfull:
		imfile = Image.open(imfull)
		imfullpath = imfull
		if imfile.size[0] > pix[0] or imfile.size[1] > pix[1]:
			xd, yd = get_size(imfile.size, pix)
			imfile = imfile.resize((xd, yd), Image.ANTIALIAS)
			xa = (pix[0]-xd)/2
			ya = (pix[1]-yd)/2
	else:
		imfile = Image.open(im)
		imfullpath = im
	photo = ImageTk.PhotoImage(imfile)
	w.create_image(xa, ya, image = photo, anchor = NW, tags = "BACK")
	w.tag_lower("BACK")
	cc = imfile.getpixel((0,0))
	w.config(bg = "#%02x%02x%02x" % (cc[0], cc[1], cc[2]))
load_background()

f2 = Frame(master)
f2.pack(side = RIGHT, fill = BOTH)
gitem = LabelFrame(f2, text="Item properties", padx=5, pady=5)
gitem.pack(side = TOP, padx=10, pady=10, fill = BOTH)

titem = LabelFrame(f2, text="Item time behavior", padx=5, pady=5)
titem.pack(side = TOP, padx=10, pady=10, fill = BOTH)
lab = Entry(gitem)
lab.grid(row=0, pady=10)
lab.delete(0, END)
lab.insert(0, "(no selection)")

def tog_act():
	"Toggle sound active flag"
	for p in par:
		if p.selected:
			p.active = not p.active
			p.play_or_stop()
			p.update_color()

but_act = Checkbutton(gitem, text = "Active", command = tog_act)
but_act.grid(row=1, pady=10, sticky=W)

def tog_sol():
	"Toggle sound solo flag"
	for p in par:
		if p.selected:
			p.makesolo()

but_sol = Checkbutton(gitem, text = "Solo", command = tog_sol)
but_sol.grid(row=2, pady=10, sticky=W)

do_ani = True
def tog_ani():
	"Toggle sound animated flag"
	for p in par:
		if p.selected:
			p.animated = not p.animated

but_ani = Checkbutton(titem, text = "Animate", command = tog_ani)
but_ani.grid(row=0, pady=10, sticky=W)

def tog_modamp():
	"Toggle sound amplitude modulation flag"
	for p in par:
		if p.selected:
			p.mod_amp = not p.mod_amp

but_modamp = Checkbutton(titem, text = "Modulate amplitude", command = tog_modamp)
but_modamp.grid(row=1, pady=10, sticky=W)

def tog_trigger():
	"Toggle sound triggered flag"
	for p in par:
		if p.selected:
			p.source.looping = not p.source.looping
			if p.source.looping:
				p.source.play()
			else:
				p.source.stop()

but_trig = Checkbutton(titem, text = "Trigger", command = tog_trigger)
but_trig.grid(row=2, pady=10, sticky=W)

def save_file():
	"Save as preset"
	global preset_dir

	mypath = asksaveasfilename(filetypes = [("PyScape presets", ps_ext),("All files",".*")], defaultextension = ps_ext, initialdir = preset_dir)
	if not len(mypath):
		return
	with open(mypath, 'wb') as csvfile:
		wr = csv.writer(csvfile)
		for p in par:
			wr.writerow(p.getdata())
		if imfullpath:
			wr.writerow(("background", imfullpath))
	preset_dir = os.path.dirname(mypath)

def getcol(r, n, z = False):
	"Attempt to read boolean from file"
	try:
		return r[n] == "True"
	except:
		return z

def getcol_float(r, n, z = 0.):
	"Attempt to read float from file"
	try:
		return float(r[n])
	except:
		return z

def load_file(mypath = None):
	"Load preset"
	global par, preset_dir

	for p in par:
		n = p.n
		p.active = False
		p.play_or_stop()
		w.delete("C%u" % n)
		w.delete("T%u" % n)
	par = []
	update_title()
	if not mypath:
		mypath = askopenfilename(filetypes = [("PyScape presets", ps_ext),("All files",".*")], initialdir = preset_dir)
		if not len(mypath):
			return
	load_background(f = mypath)
	try:
		with open(mypath, 'rb') as csvfile:
			wr = csv.reader(csvfile)
			for row in wr:
				if row[0] == "background":
					try:
						load_background(imfull = row[1])
					except:
						tkMessageBox.showwarning(
							"Load preset",
							"Could not load background image %s." % row[1]
						)
					continue
				act = (row[3] == 'True')
				fname = row[4]
				if platform.system() == "Windows" and '/' in fname:
					fname = fname.split('/')
					fname = os.path.join(fname)
				try:
					par.append(Source(
					int(row[0]), float(row[1]), float(row[2]), fname, active = act,
					animated = getcol(row, 5), mod_amp = getcol(row, 6), offset = getcol_float(row, 7),
					looping = getcol(row, 8, z = True)
					))
				except:
					tkMessageBox.showwarning(
						"Load preset",
						"Could not load sound file %s." % fname
					)
	except:
		tkMessageBox.showerror(
			"Load preset",
			"Could not read preset file %s." % mypath
		)
		return
	start_act()
	if par:
		par[0].sel()
	update_title()
	preset_dir = os.path.dirname(mypath)

def sort_all():
	"Arrange sources on screen by number"
	xp, yp = 2*cr, 2*cr
	for p in par:
		p.moveto(xp, yp)
		xp += 3*cr
		if xp > pix[0] - 2*cr:
			xp = 2*cr
			yp += 3*cr

def load_dir(mypath = None):
	"Open directory with sound files"
	global par, sound_dir

	if par:
		for p in par:
			n = p.n
			p.active = False
			p.play_or_stop()
			w.delete("C%u" % n)
			w.delete("T%u" % n)
	par = []
	update_title()
	if not mypath:
		mypath = askdirectory(initialdir = sound_dir)
		if not len(mypath):
			return
	try:
		fn = [x for x in os.listdir(mypath) if (x[0] != '.' and ".wav" in x)]
	except:
		tkMessageBox.showwarning(
			"Load sound directory",
			"Directory %s could not be read." % mypath
		)
		return
	fn.sort()
	for n,f in enumerate(fn):
		par.append(Source(
		n+1, .5, .5, os.path.join(mypath, f)
		))
	sort_all()
	if par:
		par[0].sel()
	else:
		tkMessageBox.showinfo(
			"Load sound directory",
			"No sounds found in directory %s." % mypath
		)
	update_title()
	sound_dir = mypath

def rm_inact():
	"Delete all currently inactive sounds"
	global par

	for p in par:
		if not p.active:
			w.delete("C%u" % p.n)
			w.delete("T%u" % p.n)
	par2 = []
	for p in par:
		if p.active:
			par2.append(p)
	par = par2
	update_title()

def load_sounds(mypath = None):
	"Add one or more sounds to the current scene"
	global sound_dir

	if not mypath:
		mypath = askopenfilenames(filetypes = [("WAV audio files", ".wav"),("All files",".*")], initialdir = sound_dir)
		if not len(mypath):
			return
	n = 0
	for p in par:
		if p.n >= n:
			n = p.n + 1
	for f in mypath:
		if len(mypath) > 1:
			xpos = r()/2.+.25
		else:
			xpos = .5
		try:
			par.append(Source(n, xpos, .5, f, active = True))
		except:
			tkMessageBox.showerror(
				"Add sounds",
				"There was a problem with the sound file %s.\nFormats other than WAV probably will not work." % f
			)
		w.tag_raise("C%u" % n)
		w.tag_raise("T%u" % n)
		par[-1].play_or_stop()
		n += 1
	update_title()
	sound_dir = os.path.dirname(mypath[0])

Button(f1, text = "Save preset", command = save_file).pack(side = RIGHT)
Button(f1, text = "Load preset", command = load_file).pack(side = RIGHT)

Button(f1, text = "Load sound directory", command = load_dir).pack(side = LEFT)
Button(f1, text = "Add sounds", command = load_sounds).pack(side = LEFT)
Button(f1, text = "Remove unused sounds", command = rm_inact).pack(side = LEFT)
Button(f1, text = "Arrange sounds", command = sort_all).pack(side = LEFT)

def start_act():
	"Start performance"
	global stop_it, do_ani

	stop_it = False
	do_ani = True
	but_on.config(state = DISABLED)
	but_off.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

stop_it = False

def stop_act():
	"Pause performance"
	global stop_it, do_ani

	stop_it = True
	do_ani = False
	but_off.config(state = DISABLED)
	but_on.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

def select_background():
	"Select a new background image"
	global image_dir

	mypath = askopenfilename(filetypes = [("JPEG images", ".jpg"),("PNG images", "*.png"),("All files",".*")], initialdir = image_dir)
	if not len(mypath):
		return
	try:
		load_background(imfull = mypath)
	except:
		tkMessageBox.showerror(
			"Change wallpaper",
			"Could not load image %s." % mypath
		)
	image_dir = os.path.dirname(mypath)

but_on = Button(f2, text = "Play", command = start_act, state = DISABLED, pady = 20)
but_off = Button(f2, text = "Pause", command = stop_act, pady = 20)
but_back = Button(f2, text = "Change wallpaper", command = select_background, pady = 20)

but_back.pack(side = BOTTOM, fill = X)
but_off.pack(side = BOTTOM, fill = X, pady = 20)
but_on.pack(side = BOTTOM, fill = X)

class Source():
	"A sound source"
	def __init__(s, n, x, y, fn, active = False, animated = False, mod_amp = False, offset = None, looping = True):
		cx, cy = x*pix[0], y*pix[1]
		s.n = n
		s.fn = fn
		s.active = active
		s.solo = False
		s.selected = False
		s.animated = animated
		s.vx, s.vy = 0, 0
		s.speed = 5
		s.mod_amp = mod_amp
		if offset == None or offset == 0.:
			s.offset = r()*30.
		else:
			s.offset = offset
		s.circ = w.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill = "white", tags = "C%u" % n)
		s.text = w.create_text(cx, cy, text = "%u" % n, tags = "T%u" % n)
		w.tag_bind("C%u" % n, "<Button-2>", s.clicked)
		w.tag_bind("T%u" % n, "<Button-2>", s.clicked)
		w.tag_bind("C%u" % n, "<Button-1>", s.sel)
		w.tag_bind("T%u" % n, "<Button-1>", s.sel)
		w.tag_bind("C%u" % n, "<B1-Motion>", s.moved)
		w.tag_bind("T%u" % n, "<B1-Motion>", s.moved)
		w.tag_bind("C%u" % n, "<Button-3>", s.makesolo)
		w.tag_bind("T%u" % n, "<Button-3>", s.makesolo)
		s.update_color()
		s.x, s.y = cx, cy
		s.source = contextlistener.get_source()
		s.source.buffer = openal.Buffer(fn)
		s.source.looping = looping
		s.update_parameters()

	def clicked(s, event = ""):
		"Turn active on/off"
		w.tag_raise("C%u" % s.n)
		w.tag_raise("T%u" % s.n)
		s.active = not s.active
		if s.active:
			but_act.select()
		else:
			but_act.deselect()
		s.update_color()
		s.play_or_stop()
		
	def play_or_stop(s):
		"Play (if active) or stop the sound"
		if s.active and not stop_it:
			s.source.play()
		else:
			s.source.stop()
			
	def makesolo(s, event = ""):
		"Make sound solo"
		s.solo = not s.solo
		if s.solo and s.selected:
			but_sol.select()
		else:
			but_sol.deselect()
		if s.solo:
			for p in par:
				if p.n != s.n:
					p.solo = False
					p.source.stop()
					p.update_color()
			s.source.play()
		else:
			for p in par:
				p.play_or_stop()
				p.update_color()
		s.update_color()	
		
	def moved(s, event = ""):
		"Source has been dragged by the mouse"
		x, y = event.x, event.y
		s.moveto(x, y)
		
	def moveto(s, x, y):
		"Move source to new position and update"
		dx, dy = x-s.x, y-s.y
		w.move("C%u" % s.n, dx, dy)
		w.move("T%u" % s.n, dx, dy)
		s.x, s.y = x, y
		s.update_parameters()
		
	def update_parameters(s):
		"Calculate new position and gain"
		sx = (math.pi*s.x/pix[0])-math.pi/2
		vol = 3.*(1.-(1.*s.y/pix[1]))**2
		x2 = math.sin(sx)
		y2 = math.cos(sx)
		s.source.position = [x2, y2, 0]
		s.gain_pure = max(0, vol)
		
	def sel(s, event = ""):
		"Source has been selected, update properties area"
		for p in par:
			p.selected = False
		s.selected = True
		if s.active:
			but_act.select()
		else:
			but_act.deselect()
		if s.solo:
			but_sol.select()
		else:
			but_sol.deselect()
		if s.animated:
			but_ani.select()
		else:
			but_ani.deselect()
		if s.mod_amp:
			but_modamp.select()
		else:
			but_modamp.deselect()
		if s.source.looping:
			but_trig.deselect()
		else:
			but_trig.select()
		lab.delete(0, END)
		lab.insert(0, basename(s.fn))
		for p in par:
			p.update_sel()
	
	def update_sel(s):
		"Change circle outline when selected"
		if s.selected:
			w.itemconfig("C%u" % s.n, width = 3, outline = "turquoise")
		else:
			w.itemconfig("C%u" % s.n, width = 1, outline = "black")
		
	def update_color(s):
		"Change circle fill color"
		if s.solo:
			cc = "blue"
			tc = "white"
		elif s.active:
			cc = "yellow"
			tc = "black"
		else:
			cc = "gray"
			tc = "white"
		w.itemconfig("C%u" % s.n, fill=cc)
		w.itemconfig("T%u" % s.n, fill=tc)
		update_title()

	def getdata(s):
		"Dump this source's parameters for saving"
		return [s.n, "%.5f" % (1.*s.x/pix[0]), "%.5f" % (1.*s.y/pix[1]), s.active, s.fn, s.animated, s.mod_amp, "%.3f" % s.offset, s.source.looping>0]

demos = ((10, 11, 13, 14, 15, 16), (3, 7), (6, 11), (7, 16), (4, 10, 17))

if len(sys.argv) > 1:
	print "Loading", sys.argv[1]
	load_file(mypath = sys.argv[1])
else:
	load_dir(mypath = wpath)
	if len(par) > 16:
		for j in random.choice(demos):
			par[j-1].clicked()
			par[j-1].animated = True
			if r() < .25:
				par[j-1].mod_amp = True

def update_all():
	"Move (or otherwise update) all sound sources regularly"
	is_solo = False
	for p in par:
		if p.solo:
			is_solo = True
	for p in par:
		if p.mod_amp:
			p.source.gain = p.gain_pure * (.5+.25*(1+math.sin(time()/2-p.offset)))**2
		else:
			p.source.gain = p.gain_pure
		if not p.source.looping and p.active:
			if p.source.state != openal._al.PLAYING:
				if random.expovariate(1) > 4 and (not is_solo or p.solo):
					pitch = random.normalvariate(1., .3)
					pitch = min(2., max(pitch, .5))
					p.source.pitch = pitch
					p.source.play()
					#print "triggering", p.n, "pitch", p.source.pitch
		if p.animated and do_ani:
			p.vx += (r()-.5)*p.speed
			p.vy += (r()-.5)*p.speed
			p.moveto(p.x+p.vx, p.y+p.vy)
			if p.x > pix[0]:
				p.vx = -abs(p.vx)
			if p.y > pix[1]:
				p.vy = -abs(p.vy)
			if p.x < 0:
				p.vx = abs(p.vx)
			if p.y < 0:
				p.vy = abs(p.vy)
			sp = (p.vx**2 + p.vy**2)
			if sp > p.speed**2:
				p.vx *= .5
				p.vy *= .5
			for q in par:
				if q.animated:
					dist = (q.x-p.x)**2+(q.y-p.y)**2
					if dist > 1:
						p.vx += (p.x-q.x)/dist
						p.vy += (p.y-q.y)/dist
	master.after(50, update_all)

master.after(50, update_all)

mainloop()

