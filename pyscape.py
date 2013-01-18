#!/usr/bin/env python2

"""
PyScape

A soundscape generation tool in Python

The sound files need to be mono, otherwise panning won't work!
"""

from Tkinter import *
from tkFileDialog import *
import os, sys, random, math, csv
from random import random as r
from os.path import basename

import openal

device = openal.Device()
contextlistener = device.ContextListener()
contextlistener.position = 0, 0, 0
contextlistener.velocity = 0, 0, 0
contextlistener.orientation = 0, 1, 0, 0, 0, 1

master = Tk()

pix = 800, 600
cr = 20
wpath = "/home/martin/.boodler/Collection/com.azulebanana.buddhamachine/1.5.1/mono"
fn = [x for x in os.listdir(wpath) if (x[0] != '.' and ".wav" in x)]
fn.sort()
par = []

def update_title():
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

f2 = Frame(master)
f2.pack(side = RIGHT)
gitem = LabelFrame(f2, text="Selected item", padx=5, pady=5)
gitem.pack(side = TOP, padx=10, pady=10)
Label(gitem, text = 50*' ').pack()
lab = Entry(gitem)
lab.pack(side = TOP, pady=30)
lab.delete(0, END)
lab.insert(0, "(no selection)")

def tog_act():
	for p in par:
		if p.selected:
			p.active = not p.active
			p.play_or_stop()
			p.update_color()

but_act = Checkbutton(gitem, text = "Active", command = tog_act)
but_act.pack(pady=20)

def tog_sol():
	for p in par:
		if p.selected:
			p.makesolo()

but_sol = Checkbutton(gitem, text = "Solo", command = tog_sol)
but_sol.pack(pady=20)

do_ani = True
def tog_ani():
	for p in par:
		if p.selected:
			p.animated = not p.animated

but_ani = Checkbutton(gitem, text = "Animate", command = tog_ani)
but_ani.pack(pady=20)

def save_file():
	mypath = asksaveasfilename()
	with open(mypath, 'wb') as csvfile:
		wr = csv.writer(csvfile)
		for p in par:
			wr.writerow(p.getdata())

def getcol(r, n, z = False):
	try:
		return r[n] == "True"
	except:
		return z
			
def load_file(mypath = None):
	global par

	for p in par:
		n = p.n
		p.active = False
		p.play_or_stop()
		w.delete("C%u" % n)
		w.delete("T%u" % n)
	par = []
	update_title()
	if not mypath:
		mypath = askopenfilename()
	try:
		with open(mypath, 'rb') as csvfile:
			wr = csv.reader(csvfile)
			for row in wr:
				act = (row[3] == 'True')
				par.append(Source(int(row[0]), float(row[1]), float(row[2]), row[4], active = act, animated = getcol(row, 5)))
	except:
		print "Cannot read file", mypath
	start_act()
	update_title()

Button(f1, text = "Save", command = save_file).pack(side = RIGHT)
Button(f1, text = "Load", command = load_file).pack(side = RIGHT)

def start_act():
	global stop_it, do_ani
	stop_it = False
	do_ani = True
	but_on.config(state = DISABLED)
	but_off.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

stop_it = False

def stop_act():
	global stop_it, do_ani
	stop_it = True
	do_ani = False
	but_off.config(state = DISABLED)
	but_on.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

but_on = Button(f1, text = "Play", command = start_act, state = DISABLED)
but_off = Button(f1, text = "Pause", command = stop_act)

but_on.pack(side = LEFT)
but_off.pack(side = LEFT)

class Source():
	def __init__(s, n, x, y, fn, active = False, animated = False):
		cx, cy = x*pix[0], y*pix[1]
		s.n = n
		s.fn = fn
		s.active = active
		s.solo = False
		s.selected = False
		s.animated = animated
		s.vx, s.vy = 0, 0
		s.speed = 5
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
		s.source.looping = True
		s.update_parameters()

	def clicked(s, event = ""):
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
		if s.active and not stop_it:
			s.source.play()
		else:
			s.source.stop()
			
	def makesolo(s, event = ""):
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
		x, y = event.x, event.y
		s.moveto(x, y)
		
	def moveto(s, x, y):
		dx, dy = x-s.x, y-s.y
		w.move("C%u" % s.n, dx, dy)
		w.move("T%u" % s.n, dx, dy)
		s.x, s.y = x, y
		s.update_parameters()
		
	def update_parameters(s):
		sx = (math.pi*s.x/pix[0])-math.pi/2
		vol = 3.*(1.-(1.*s.y/pix[1]))**2
		x2 = math.sin(sx)
		y2 = math.cos(sx)
		s.source.position = [x2, y2, 0]
		s.source.gain = max(0, vol)
		
	def sel(s, event = ""):
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
		lab.delete(0, END)
		lab.insert(0, basename(s.fn))
		for p in par:
			p.update_sel()
	
	def update_sel(s):
		if s.selected:
			w.itemconfig("C%u" % s.n, width = 3, outline = "turquoise")
		else:
			w.itemconfig("C%u" % s.n, width = 1, outline = "black")
		
	def update_color(s):
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
		return [s.n, "%.5f" % (1.*s.x/pix[0]), "%.5f" % (1.*s.y/pix[1]), s.active, s.fn, s.animated]

if len(sys.argv) > 1:
	print "Loading", sys.argv[1]
	load_file(mypath = sys.argv[1])
else:		
	for i in range(len(fn)):
		par.append(Source(i+1, r()*.8+.1, r()*.8+.1, os.path.join(wpath, fn[i])))
	if len(par) > 16:
		for j in 10, 11, 13, 14, 15, 16:
			par[j-1].clicked()
			par[j-1].animated = True

update_title()

def move_ani():
	for p in par:
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
	master.after(50, move_ani)

master.after(50, move_ani)

mainloop()

