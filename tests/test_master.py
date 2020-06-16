#! /bin/env python3

from __future__ import division
import unittest

import solsticepy
from solsticepy.master import Master
from solsticepy.cal_layout import radial_stagger
import os
import numpy as np

class TestMaster(unittest.TestCase):
	def setUp(self):

		DNI = 1000 # W/m2
		sunshape = 'pillbox'
		half_angle_deg = 0.2664
		sun = solsticepy.Sun(dni=DNI, sunshape=sunshape, half_angle_deg=half_angle_deg)

		# S3. sun position
		# e.g. summer solstice, solar noon
		azimuth=270.   # from East to North, deg
		elevation =78. # 0 is horizontal, deg
		latitude=34.   # latitude of the crs plant
		# S4. number of rays for the ray-tracing simulation
		num_rays=2000000

		# F2. Heliostat
		hst_w=10. # m
		hst_h=10. # m
		rho_refl=0.95 # mirror reflectivity
		slope_error=2.e-3 # radians
		tower_h=80. # tower height
		tower_r=0.01 # tower radius

		field=radial_stagger(latitude=latitude, num_hst=1000, width=hst_w, height=hst_h, hst_z=3., towerheight=tower_h, R1=50., fb=0.5, dsep=0., field='polar', savedir='.', plot=False)
		hst_pos=field[2:,:3]
		hst_foc=field[2:,3] 
		hst_aims=field[2:,4:]

		#
		# the receiver
		# ============
		# R1. shape
		receiver='flat' # 'flat' or 'stl'
		# R2. Size
		rec_w=8. # width, m
		rec_h=6. # height, m
		# R3. tilt angle
		tilt=0.  # deg
		# R4. position
		loc_x=0. # m
		loc_y=0. # m
		loc_z=tower_h# m
		# R5. Abosrptivity
		rec_abs=0.9
		rec_mesh=100
		rec_param=np.r_[rec_w, rec_h, rec_mesh, loc_x, loc_y, loc_z, tilt]

		master=Master(casedir='.')
		outfile_yaml = master.in_case('input.yaml')
		outfile_recv = master.in_case('input-rcv.yaml')

		solsticepy.gen_yaml(sun, hst_pos, hst_foc, hst_aims, hst_w, hst_h
		, rho_refl, slope_error, receiver, rec_param, rec_abs
		, outfile_yaml=outfile_yaml, outfile_recv=outfile_recv
		, hemisphere='North', tower_h=tower_h, tower_r=tower_r,  spectral=False
		, medium=0, one_heliostat=False)

		self.eta, self.performance_hst=master.run(azimuth, elevation, num_rays, rho_refl,sun.dni, gen_vtk=False)

		self.table, self.ANNUAL=master.run_annual(nd=5, nh=5, latitude=latitude, num_rays=num_rays, num_hst=len(hst_pos),rho_mirror=rho_refl, dni=DNI)

	def test_touching(self):
		self.assertEqual(round(self.eta.n, 5), 0.47143)
		os.system('rm *.csv')
		os.system('rm *.yaml')
		os.system('rm simul')
		os.system('rm -rf sunpos*')


if __name__ == '__main__':
	unittest.main()
