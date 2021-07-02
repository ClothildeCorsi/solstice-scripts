#
# This is an example script to simulate a central receiver system (CRS)
# using Solstice via solsticepy
#
import solsticepy
from solsticepy.design_bd import *
import numpy as np
import os

#==================================================
# INPUT PARAMETERS

# define a unique case folder for the user
# =========

snum = 0
suffix = ""
while 1:
    import datetime,time
    dt = datetime.datetime.now()
    ds = dt.strftime("%a-%H-%M")
    casefolder = os.path.join(os.getcwd(),'case-%s-%s%s'%(os.path.basename(__file__),ds,suffix))
    if os.path.exists(casefolder):
        snum+=1
        suffix = "-%d"%(snum,)
        if snum > 200:
            raise RuntimeError("Some problem with creating casefolder")
    else:
        # good, we have a new case dir
        break

pm=Parameters()

# Variables
pm.H_tower=75. # 80. # tower height or vertical distance to aiming point (located at the center of xOy plan)
pm.theta_deg=20.   # acceptance half angle of the CPC in degree
pm.field_rim_angle = 80. # rim angle of the heliostat field in the xOz plan in degree
pm.secref_fratio = 0.6 # ratio of the foci distance and apex distance to the origin [1/2,1]
pm.ratio_cpc_h=1. # must be inferior to 1
pm.rec_z=0.
# fixed parameters
# =========

pm.Q_in_rcv=40e6
num_hst = 300
pm.nd=9
pm.nh=9
pm.H_rcv=10.
pm.W_rcv=1.2
pm.W_helio=6.1 #1.84 # ASTRI helio size
pm.H_helio=6.1 # 2.44
pm.dependent_par()
print(pm.fb)
print(pm.H_tower)
pm.field_type = 'surround'
pm.Z_helio = 0.
pm.R1 = 30.
pm.lat = -27.16 #degree
pm.fb
pm.dsep

# enter the parameters for the beam-down components
receiver='beam_down'
# Polygon receiver
rec_w=pm.W_rcv
rec_l=pm.H_rcv
# 2D-crossed cpc with n faces
n_CPC_faces=4
rec_grid=20
n_Z=30
# Secondary refector 'hyperboloid'
refl_sec = 0.95
slope_error = 1.e-3 # radian

# parameters recalculated (pre-optimized before optimization)
secref_vert=None # np.array([[-15,25],[-15,-25],[15,-25],[15,25]])

pm.saveparam(casefolder)
# create the environment and scene
# =========
tablefile=casefolder+'/OELT_Solstice.motab'
weafile='./demo_TMY3_weather.motab'

bd=BD(latitude=pm.lat, casedir=casefolder)

bd.receiversystem(receiver=receiver, rec_abs=float(pm.alpha_rcv), rec_w=float(rec_w), rec_l=float(rec_l), rec_z=float(pm.rec_z), rec_grid=int(rec_grid), cpc_nfaces=int(n_CPC_faces), cpc_theta_deg=float(pm.theta_deg), ratio_cpc_h=float(pm.ratio_cpc_h), cpc_nZ=float(n_Z), field_rim_angle=float(pm.field_rim_angle), aim_z=float(pm.H_tower), secref_fratio=pm.secref_fratio, refl_sec=float(refl_sec), slope_error=float(slope_error),	secref_vert = secref_vert)

bd.heliostatfield(field=pm.field_type, hst_rho=pm.rho_helio, slope=slope_error, hst_w=pm.W_helio, hst_h=pm.H_helio, tower_h=pm.H_tower, tower_r=pm.R_tower, hst_z=pm.Z_helio, num_hst=num_hst, R1=pm.R1, fb=pm.fb, dsep=pm.dsep, x_max=300., y_max=300.)

bd.yaml(sunshape=pm.sunshape,csr=pm.crs,half_angle_deg=pm.half_angle_deg,std_dev=pm.std_dev)

oelt, A_land=bd.field_design_annual(dni_des=900., num_rays=int(1e7), nd=pm.nd, nh=pm.nh, weafile=weafile, method=1, Q_in_des=pm.Q_in_rcv, n_helios=None, zipfiles=False, gen_vtk=False, plot=False)


if (A_land==0):
    tablefile=None
else:
    A_helio=pm.H_helio*pm.W_helio
    output_matadata_motab(table=oelt, field_type=pm.field_type, aiming='single', n_helios=num_hst, A_helio=A_helio, eff_design=bd.eff_des, H_rcv=pm.H_rcv, W_rcv=pm.W_rcv, H_tower=pm.H_tower, Q_in_rcv=bd.Q_in_rcv, A_land=A_land, savedir=tablefile)

bd.yaml(sunshape=pm.sunshape,csr=pm.crs,half_angle_deg=pm.half_angle_deg,std_dev=pm.std_dev)

bd.annual_oelt(dni_des=900., num_rays=int(1e7), nd=pm.nd, nh=pm.nh, zipfiles=False, gen_vtk=False, plot=False)
