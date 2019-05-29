from srcPy.gen_YAML import gen_YAML

import numpy as N
import os

solstice_dir='/home/yewang/Solstice-0.8.1-GNU-Linux64'
casefolder='./example'
if not os.path.exists(casefolder):
    os.makedirs(casefolder)


#
# the sun
#
# e.g. spring equinox, solar noon
azimuth=270. # from East to North
elevation =78.  # 0 is horizontal

sunshape='pillbox' # or 'buie'
sunsize=4.65e-3*180./N.pi#deg or CSR value
DNI=1000 # W/m2
num_rays=2000000
#
# the field
#
layout=N.loadtxt('./demo_layout.csv', delimiter=',', skiprows=2)
hst_pos=layout[:,:3]
hst_foc=layout[:,3]
hst_aims=layout[:,4:]
hst_w=10.
hst_h=10.
rho_refl=0.95 # mirror reflectivity
slope_error=2.e-3 # rad
tower_h=0.01
tower_r=3.
#
# the receiver
#
receiver='flat'
rec_abs=0.9
rec_w=8.
rec_h=6.
rec_mesh=100
loc_x=0.
loc_y=0.
loc_z=62.
tilt=0. # deg
#
#
#
#
rec_param=N.r_[rec_w, rec_h, rec_mesh, loc_x, loc_y, loc_z, tilt]
gen_YAML(DNI, sunshape, sunsize, hst_pos, hst_foc, hst_aims,hst_w, hst_h, rho_refl, slope_error, tower_h, tower_r, receiver, rec_param, rec_abs, casefolder, spectral=False, medium=0 )
#
N.savetxt(casefolder+'/azimuth.input', [azimuth])
N.savetxt(casefolder+'/elevation.input', [elevation])
N.savetxt(casefolder+'/rays.input', [num_rays],fmt="%s")
N.savetxt(solstice_dir+'/casedir.input', [casefolder], fmt='%s')




