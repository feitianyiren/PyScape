#!/usr/bin/env python2

"""
PyScape

A soundscape generation tool in Python

The sound files need to be mono, otherwise panning won't work!
"""

from Tkinter import *
import os, random, math
from random import random as r

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

def update_title():
	a = len(par)
	b = len([x for x in par if x.active])
	master.title("%u of %u sources active (LMB=toggle; MMB=drag; RMB=edit)" % (b, a))

w = Canvas(master, width=pix[0], height=pix[1], bg="white")
w.pack()

par = []

class Source():
	def __init__(s, n, x, y, fn):
		cx, cy = x*pix[0], y*pix[1]
		s.n = n
		s.active = False
		s.circ = w.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill="white", tags="C%u" % n)
		s.text = w.create_text(cx, cy, text = "%u" % n, tags="T%u" % n)
		w.tag_bind("C%u" % n, "<Button-1>", s.clicked)
		w.tag_bind("T%u" % n, "<Button-1>", s.clicked)
		w.tag_bind("C%u" % n, "<B2-Motion>", s.moved)
		w.tag_bind("T%u" % n, "<B2-Motion>", s.moved)
		s.update_color()
		s.x, s.y = cx, cy
		s.source = contextlistener.get_source()
		s.source.buffer = openal.Buffer(fn)
		s.source.looping = True
		s.source.gain = 1.

	def clicked(s, event = ""):
		w.tag_raise("C%u" % s.n)
		w.tag_raise("T%u" % s.n)
		s.active = not s.active
		s.update_color()
		if s.active:
			s.source.play()
		else:
			s.source.stop()
		
	def moved(s, event = ""):
		x, y = event.x, event.y
		dx, dy = x-s.x, y-s.y
		w.move("C%u" % s.n, dx, dy)
		w.move("T%u" % s.n, dx, dy)
		s.x, s.y = x, y
		sx = (math.pi*s.x/pix[0])-math.pi/2
		vol = 3.*(1.-(1.*s.y/pix[1]))**2
		#print s.source.position, vol
		x2 = math.sin(sx)
		y2 = math.cos(sx)
		s.source.position = [x2, y2, 0]
		s.source.gain = max(0, vol)
		
	def update_color(s):
		if s.active:
			cc = "yellow"
			tc = "black"
		else:
			cc = "gray"
			tc = "white"
		w.itemconfig("C%u" % s.n, fill=cc)
		w.itemconfig("T%u" % s.n, fill=tc)
		update_title()

for i in range(1, 8):
	f = random.choice(fn)
	par.append(Source(i, r()*.9, r()*.9, os.path.join(wpath, f)))

update_title()

mainloop()

