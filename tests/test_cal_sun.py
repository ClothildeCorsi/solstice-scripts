#! /bin/env python3

from __future__ import division
import unittest

from solsticepy.cal_sun import *
import os
import numpy as np

class TestOneSunPosition(unittest.TestCase):
	def setUp(self):
		latitude=37.44
		time='morning'
		sun=SunPosition()
		day=sun.days(21, 'Jun')
		self.delta=sun.declination(day)
		daytime, sunrise=sun.solarhour(self.delta, latitude)

		if time=='solarnoon':
			self.omega=0. # solar noon
		elif time=='morning':
			self.omega=sunrise+30. # one hour is 15 deg, two hours is 30 deg

		theta=sun.zenith(latitude, self.delta, self.omega) # 0 is vertical
		phi=sun.azimuth(latitude, theta, self.delta, self.omega) # from South to West
		
		# convert to solstice convention
		self.sol_azi, self.sol_ele=sun.convert_convention(tool='solstice', azimuth=phi, zenith=theta)
		# convert back to declination and hour angle
		self.dec, self.ha =sun.convert_AZEL_to_declination_hour(theta, phi, latitude)

	def test_touching(self):
		self.assertEqual(round(self.dec,4), round(self.delta,4))
		self.assertEqual(round(self.ha,4), round(self.omega,4))
		self.assertEqual(round(self.sol_azi,2), 13.31)
		self.assertEqual(round(self.sol_ele,2), 22.08)


class TestAnnualSunPositions(unittest.TestCase):
	def setUp(self):
		latitude=37.44
		self.nd=5
		self.nh=9
		sun=SunPosition()
		self.AZI, self.ZENITH, self.table, self.case_list=sun.annual_angles(latitude, casefolder='.',nd=self.nd, nh=self.nh)

	def test_touching(self):
		self.assertEqual(np.shape(self.table)[0], self.nd+3)
		self.assertEqual(np.shape(self.table)[1], self.nh+3)
		self.assertEqual(len(self.AZI), self.case_list[-1,0].astype(float))
		os.system('rm *.csv')


if __name__ == '__main__':
	unittest.main()

