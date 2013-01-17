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
par = []

def update_title():
	a = len(par)
	b = len([x for x in par if x.active])
	master.title("%u of %u sources active (LMB=toggle; MMB=drag; RMB=solo)" % (b, a))

w = Canvas(master, width=pix[0], height=pix[1], bg="white")
w.pack()

def save_file():
	mypath = asksaveasfilename()
	with open(mypath, 'wb') as csvfile:
		wr = csv.writer(csvfile)
		for p in par:
			wr.writerow(p.getdata())
			
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
				par.append(Source(int(row[0]), float(row[1]), float(row[2]), row[4], active = act))
	except:
		print "Cannot read file", mypath
	start_act()
	update_title()

Button(master, text = "Save", command = save_file).pack(side = RIGHT)
Button(master, text = "Load", command = load_file).pack(side = RIGHT)

def start_act():
	global stop_it
	stop_it = False
	but_on.config(state = DISABLED)
	but_off.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

stop_it = False

def stop_act():
	global stop_it
	stop_it = True
	but_off.config(state = DISABLED)
	but_on.config(state = NORMAL)
	for p in par:
		p.play_or_stop()

but_on = Button(master, text = "Start", command = start_act, state = DISABLED)
but_off = Button(master, text = "Stop", command = stop_act)

but_on.pack(side = LEFT)
but_off.pack(side = LEFT)

class Source():
	def __init__(s, n, x, y, fn, active = False):
		cx, cy = x*pix[0], y*pix[1]
		s.n = n
		s.fn = fn
		s.active = active
		s.solo = False
		s.circ = w.create_oval(cx-cr, cy-cr, cx+cr, cy+cr, fill="white", tags="C%u" % n)
		s.text = w.create_text(cx, cy, text = "%u" % n, tags="T%u" % n)
		w.tag_bind("C%u" % n, "<Button-1>", s.clicked)
		w.tag_bind("T%u" % n, "<Button-1>", s.clicked)
		w.tag_bind("C%u" % n, "<B2-Motion>", s.moved)
		w.tag_bind("T%u" % n, "<B2-Motion>", s.moved)
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
		s.update_color()
		s.play_or_stop()
		
	def play_or_stop(s):
		if s.active and not stop_it:
			s.source.play()
		else:
			s.source.stop()
			
	def makesolo(s, event = ""):
		s.solo = not s.solo
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
		return [s.n, 1.*s.x/pix[0], 1.*s.y/pix[1], s.active, s.fn]

if len(sys.argv) > 1:
	print "loading", sys.argv[1]
	load_file(mypath = sys.argv[1])
else:		
	for i in range(len(fn)):
		par.append(Source(i+1, r()*.9, r()*.9, os.path.join(wpath, fn[i])))

update_title()

mainloop()

