import numpy as np
import re
import sys
import os
from uncertainties import ufloat
from uncertainties.umath import *
from .output_motab import output_motab 

def process_raw_results(rawfile, savedir,rho_mirror,dni,verbose=False):
	"""Process the raw Solstice `simul` output into readable CSV files for central receiver systems

	``Arguments``

	  * rawfile (str): the directory of the `simul` file that generated by Solstice
	  * savedir (str): the directory for saving the organised results
	  * rho_mirror (float): mirror reflectivity (needed for reporting energy sums)
	  * dni (float): the direct normal irradiance (W/m2), required to obtain performance of individual heliostat
	  * verbose (bool), write results to disk or not

	``Returns``

	  * efficiency_total (float): the total optical efficiency
	  * performance_hst (numpy array): the breakdown of losses of each individual heliostat
	  * The simulation results are created and written in the `savedir`
		
	"""

	# FIXME this approach seems fundamentally a bit messy... we are carefully
	# load the text output from 'solppraw' and then assuming that we can
	# correctly find the right bits of data in the right place. Wouldn't it
	# be easier and more robust to modify solppraw to create output that can
	# be directly loaded, along with data labels, eg a YAML file? Or to
	# create 'result-raw.csv' directly?

	rows = []
	index = 0
	with open(rawfile) as f:
		for r in f.readlines():
			if index<20:
				pass #sys.stderr.write("Line %d: %s"%(index,r))

			if r[0] == "#":
				#sys.stderr.write("^------Comment\n")
				#comment line
				rows.append([r])
			else:
				rows.append(r.split())			
			index+=1

	# sun direction

	#sys.stderr.write("SUN DIRECTION?\n")
	#sys.stderr.write(rows[0][0]+"\n")
	sun=re.findall("[-+]?\d*\.\d+|\d+", rows[0][0])
	#sys.stderr.write("SUN = %s\n"%(repr(sun),))

	azimuth=sun[0]
	elevation=sun[1]

	def get_rc(row,col):
		return float(rows[row][col])

	# Global results

	num_res=int(get_rc(1,0)) # number of global results
	num_rec=int(get_rc(1,1))
	num_hst=get_rc(1,2)
	num_rays=get_rc(1,3)

	potential=get_rc(2,0) #W
	potential_err=get_rc(2,1)

	absorbed=get_rc(3,0)
	absorbed_err=get_rc(3,1)    

	Fcos=get_rc(4,0)
	Fcos_err=get_rc(4,1)  

	shadow_loss=get_rc(5,0)
	shadow_err=get_rc(5,1)    

	missing_loss=get_rc(6,0)
	missing_err=get_rc(6,1) 

	material_loss=get_rc(7,0)
	material_err=get_rc(7,1)    

	atmospheric_loss=get_rc(8,0)
	atmospheric_err=get_rc(8,1)  

	# Target (receiver)
	# 0 receiver name
	# 1 - 2 id and area
	# 3 - 24 (total 22) front
	# 25- 46 (total 22) back 
	rec_area=0. # m2  

	rec_front_income=0.
	rec_front_income_err=0.
	#rec_no_material_loss=get_rc(num_res+2,5)
	#rec_no_material_loss_err=get_rc(num_res+2,6)
	#rec_no_atmo_loss=get_rc(num_res+2,7)
	#rec_no_atmo_loss_err=get_rc(num_res+2,8)
	#rec_material_loss=get_rc(num_res+2,9)
	#rec_material_loss_err=get_rc(num_res+2,10)
	rec_front_absorbed=0.
	rec_front_absorbed_err=0.
	rec_front_eff=0.
	rec_front_eff_err=0.

	rec_back_income=0.
	rec_back_income_err=0.
	rec_back_absorbed=0.
	rec_back_absorbed_err=0.
	rec_back_eff=0.
	rec_back_eff_err=0.

	rec_id={}
	for i in range(num_rec-1): # -1 the virtual target
		rec_id[i]=get_rc(num_res+2+i,1) # the id number of the receiver
		rec_area+=get_rc(num_res+2+i,2) # m2  
	
		rec_front_income+=get_rc(num_res+2+i,3)
		rec_front_income_err+=get_rc(num_res+2+i,4)
		#rec_no_material_loss=get_rc(num_res+2,5)
		#rec_no_material_loss_err=get_rc(num_res+2,6)
		#rec_no_atmo_loss=get_rc(num_res+2,7)
		#rec_no_atmo_loss_err=get_rc(num_res+2,8)
		#rec_material_loss=get_rc(num_res+2,9)
		#rec_material_loss_err=get_rc(num_res+2,10)
		rec_front_absorbed+=get_rc(num_res+2+i,13)
		rec_front_absorbed_err+=get_rc(num_res+2+i,14)
		rec_front_eff+=get_rc(num_res+2+i,23)
		rec_front_eff_err+=get_rc(num_res+2+i,24)

		rec_back_income+=get_rc(num_res+2+i,25)
		rec_back_income_err+=get_rc(num_res+2+i,26)
		rec_back_absorbed+=get_rc(num_res+2+i,35)
		rec_back_absorbed_err+=get_rc(num_res+2+i,36)
		rec_back_eff+=get_rc(num_res+2+i,-2)
		rec_back_eff_err+=get_rc(num_res+2+i,-1)


	#Virtual target
	vir_area=get_rc(num_res+2+num_rec-1,2)
	vir_income=get_rc(num_res+2+num_rec-1,3)
	vir_income_err=get_rc(num_res+2+num_rec-1,4)
	
	raw_res=np.array([
		['name','value', 'error']
		,['sun_azimuth', azimuth,'']
		,['sun_elevation', elevation, '']
		,['num hst', num_hst,'']
		,['num rays',num_rays, '']
		,['potential flux', potential, potential_err]
		,['absorbed flux', absorbed, absorbed_err]
		,['Cosine factor', Fcos, Fcos_err]
		,['shadow loss', shadow_loss, shadow_err]
		,['Mising loss', missing_loss, missing_err]
		,['materials loss', material_loss, material_err]
		,['atomospheric loss', atmospheric_loss, atmospheric_err]
		,['','','']
		,['Target', '','']
		,['area', rec_area, '']
		,['front income flux', rec_front_income, rec_front_income_err]
		,['back income flux', rec_back_income, rec_back_income_err]
		,['front absorbed flux', rec_front_absorbed, rec_front_absorbed_err]
		,['back absorbed flux', rec_back_absorbed, rec_back_absorbed_err]
		,['front efficiency', rec_front_eff, rec_front_eff_err]
		,['back efficiency', rec_back_eff, rec_back_eff_err]
		,['','','']
		,['Virtual plane','','']
		,['area', vir_area, '']
		,['income flux', vir_income,vir_income_err]
	])

	#sys.stderr.write(repr(raw_res))
	#sys.stderr.write("SHAPE = %s" % (repr(raw_res.shape)))



	Qtotal=ufloat(potential, 0)
	Fcos=ufloat(Fcos,Fcos_err) 
	Qcos=Qtotal*(1.-Fcos)
	Qshade=ufloat(shadow_loss,shadow_err)
	Qfield_abs=(Qtotal-Qcos-Qshade)*(1.-float(rho_mirror))
	Qattn=ufloat(atmospheric_loss, atmospheric_err)
	Qabs=ufloat(absorbed, absorbed_err)
	Qspil=ufloat(vir_income,vir_income_err)-Qabs
	Qrefl=ufloat(rec_front_income,rec_front_income_err)+ufloat(rec_back_income,rec_back_income_err)-Qabs
	Qblock=Qtotal-Qcos-Qshade-Qfield_abs-Qspil-Qabs-Qrefl-Qattn

	organised=np.array([
		['Name', 'Value', '+/-Error']
		,['Qall (kW)', Qtotal.n/1000., Qtotal.s/1000.]
		,['Qcos (kW)', Qcos.n/1000.,Qcos.s/1000.]
		,['Qshad (kW)', Qshade.n/1000., Qshade.s/1000.]
		,['Qfield_abs (kW)', Qfield_abs.n/1000., Qfield_abs.s/1000.]
		,['Qblcok (kW)', Qblock.n/1000.,  Qblock.s/1000.]
		,['Qattn (kW)',Qattn.n/1000., Qattn.s/1000.]
		,['Qspil (kW)', Qspil.n/1000., Qspil.s/1000.]
		,['Qrefl (kW)', Qrefl.n/1000.,Qrefl.s/1000.]
		,['Qabs (kW)', Qabs.n/1000., Qabs.s/1000.]
		,['rays', num_rays,'-']
	])

	efficiency_total=Qabs/Qtotal

	# per heliostat results, and
	# per receiver per heliostat results
	num_hst=int(num_hst)    
	heliostats=np.zeros((num_hst,28))

	for i in range(num_hst):
		l1=2+num_res+num_rec+i # the line number of the per heliostat result
		per_hst=rows[l1]

		hst_idx=re.findall("[-+]?\d*\.\d+|\d+", per_hst[0] ) 
		hst_area=per_hst[2]
		hst_sample=per_hst[3]
		hst_cos=per_hst[4]
		hst_shad=per_hst[6]

		heliostats[i,0]=hst_idx[0]
		heliostats[i,1]=hst_area
		heliostats[i,2]=hst_sample
		heliostats[i,3]=hst_cos
		heliostats[i,4]=hst_shad

		# per heliostat per receiver
		for j in range(num_rec-1):
			l2=2+num_res+num_rec+num_hst*(j+1)+i  
			per_hst=rows[l2]   
			hst_in=float(per_hst[2])+float(per_hst[22]) # front+back
			hst_in_mat=float(per_hst[8])+float(per_hst[28])
			hst_in_atm=float(per_hst[10])+float(per_hst[30])
			hst_abs=float(per_hst[12])+float(per_hst[32])
			hst_abs_mat=float(per_hst[18])+float(per_hst[38])
			hst_abs_atm=float(per_hst[20])+float(per_hst[40])
			  
			heliostats[i,5]+=hst_in
			heliostats[i,6]+=hst_in_mat
			heliostats[i,7]+=hst_in_atm
			heliostats[i,8]+=hst_abs
			heliostats[i,9]+=hst_abs_mat
			heliostats[i,10]+=hst_abs_atm

		# per heliostat per virtual target
		l3=2+num_res+num_rec+(num_rec)*num_hst+i  
		per_hst=rows[l3] 
		hst_in=float(per_hst[2])+float(per_hst[22]) # front+back
		hst_in_mat=float(per_hst[8])+float(per_hst[28])
		hst_in_atm=float(per_hst[10])+float(per_hst[30])
		hst_abs=float(per_hst[12])+float(per_hst[32])
		hst_abs_mat=float(per_hst[18])+float(per_hst[38])
		hst_abs_atm=float(per_hst[20])+float(per_hst[40])
		  
		heliostats[i,11]=hst_in
		heliostats[i,12]=hst_in_mat
		heliostats[i,13]=hst_in_atm
		heliostats[i,14]=hst_abs
		heliostats[i,15]=hst_abs_mat
		heliostats[i,16]=hst_abs_atm


		hst_tot=float(hst_area)*1000.
		hst_cos=hst_tot*(1.-float(hst_cos))
		hst_shad=float(hst_shad)
		hst_abs=(hst_tot-hst_cos-hst_shad)*(1.-rho_mirror)

		hst_atm=float(heliostats[i,10])
		hst_rec_abs=float(heliostats[i,8])
		hst_spil=float(heliostats[i,11])-hst_rec_abs
		hst_rec_refl=float(heliostats[i,5])-float(heliostats[i,8])
		hst_block=hst_tot-hst_cos-hst_shad-hst_abs-hst_atm-hst_spil-hst_rec_abs-hst_rec_refl

		heliostats[i,19]=hst_tot
		heliostats[i,20]=hst_cos
		heliostats[i,21]=hst_shad
		heliostats[i,22]=hst_abs
		heliostats[i,23]=hst_block
		heliostats[i,24]=hst_atm
		heliostats[i,25]=hst_spil
		heliostats[i,26]=hst_rec_refl
		heliostats[i,27]=hst_rec_abs

	idx=heliostats[:, 0].argsort()
	heliostats=heliostats[idx]
	performance_hst=heliostats[:, 19:]

	heliostats_title=np.array(['hst_idx', 'area', 'sample', 'cos', 'shade', 'incoming', 'in-mat-loss','in-atm-loss', 'absorbed', 'abs-mat-loss', 'abs-atm-loss', 'vir_incoming', 'vir_in-mat-loss','vir_in-atm-loss', 'vir_absorbed', 'vir_abs-mat-loss', 'vir_abs-atm-loss', '', '', 'total', 'cos', 'shad', 'hst_abs', 'block', 'atm', 'spil', 'rec_refl', 'rec_abs' ]) 

	heliostats_details=np.vstack((heliostats_title, heliostats))


	if verbose:
		np.savetxt(savedir+'/result-formatted.csv', organised, fmt='%s', delimiter=',')
		np.savetxt(savedir+'/heliostats-raw.csv', heliostats_details, fmt='%s', delimiter=',')
		np.savetxt(savedir+'/result-raw.csv', raw_res, fmt='%s', delimiter=',')
	else:
		os.system('rm -rf %s'%savedir)
	return efficiency_total, performance_hst

def process_raw_results_multi_aperture(rawfile, savedir,rho_mirror,dni,verbose=False):
	"""Process the raw Solstice `simul` output into readable CSV files for multi-aperture central receiver systems

	``Arguments``

	  * rawfile (str): the directory of the `simul` file that generated by Solstice
	  * savedir (str): the directory for saving the organised results
	  * rho_mirror (float): mirror reflectivity (needed for reporting energy sums)
	  * dni (float): the direct normal irradiance (W/m2), required to obtain performance of individual heliostat
	  * verbose (bool), write results to disk or not

	``Returns``

	  * efficiency_total (float): the total optical efficiency
	  * performance_hst (numpy array): the breakdown of losses of each individual heliostat
	  * The simulation results are created and written in the `savedir`
		
	"""

	# FIXME this approach seems fundamentally a bit messy... we are carefully
	# load the text output from 'solppraw' and then assuming that we can
	# correctly find the right bits of data in the right place. Wouldn't it
	# be easier and more robust to modify solppraw to create output that can
	# be directly loaded, along with data labels, eg a YAML file? Or to
	# create 'result-raw.csv' directly?

	rows = []
	index = 0
	with open(rawfile) as f:
		for r in f.readlines():
			if index<20:
				pass #sys.stderr.write("Line %d: %s"%(index,r))

			if r[0] == "#":
				#sys.stderr.write("^------Comment\n")
				#comment line
				rows.append([r])
			else:
				rows.append(r.split())			
			index+=1

	# sun direction

	#sys.stderr.write("SUN DIRECTION?\n")
	#sys.stderr.write(rows[0][0]+"\n")
	sun=re.findall("[-+]?\d*\.\d+|\d+", rows[0][0])
	#sys.stderr.write("SUN = %s\n"%(repr(sun),))

	azimuth=sun[0]
	elevation=sun[1]

	def get_rc(row,col):
		return float(rows[row][col])

	# Global results

	num_res=int(get_rc(1,0)) # number of global results
	num_rec=int(get_rc(1,1))
	num_hst=get_rc(1,2)
	num_rays=get_rc(1,3)

	potential=get_rc(2,0) #W
	potential_err=get_rc(2,1)

	absorbed=get_rc(3,0)
	absorbed_err=get_rc(3,1)    

	Fcos=get_rc(4,0)
	Fcos_err=get_rc(4,1)  

	shadow_loss=get_rc(5,0)
	shadow_err=get_rc(5,1)    

	missing_loss=get_rc(6,0)
	missing_err=get_rc(6,1) 

	material_loss=get_rc(7,0)
	material_err=get_rc(7,1)    

	atmospheric_loss=get_rc(8,0)
	atmospheric_err=get_rc(8,1)  

	# Target (receiver)
	# 0 receiver name
	# 1 - 2 id and area
	# 3 - 24 (total 22) front
	# 25- 46 (total 22) back 
	num_apertures=num_rec-1 # -1 the virtual target
	rec_id={}

	rec_area=[] # m2  
	rec_front_income=[]
	rec_front_income_err=[]

	rec_front_absorbed=[]
	rec_front_absorbed_err=[]
	rec_front_eff=[]
	rec_front_eff_err=[]

	rec_back_income=[]
	rec_back_income_err=[]
	rec_back_absorbed=[]
	rec_back_absorbed_err=[]
	rec_back_eff=[]
	rec_back_eff_err=[]

	for i in range(num_apertures): 
		rec_id[i]=get_rc(num_res+2+i,1) # the id number of the receiver
		rec_area.append(get_rc(num_res+2+i,2)) # m2  
	
		rec_front_income.append(get_rc(num_res+2+i,3))
		rec_front_income_err.append(get_rc(num_res+2+i,4))

		rec_front_absorbed.append(get_rc(num_res+2+i,13))
		rec_front_absorbed_err.append(get_rc(num_res+2+i,14))
		rec_front_eff.append(get_rc(num_res+2+i,23))
		rec_front_eff_err.append(get_rc(num_res+2+i,24))

		rec_back_income.append(get_rc(num_res+2+i,25))
		rec_back_income_err.append(get_rc(num_res+2+i,26))
		rec_back_absorbed.append(get_rc(num_res+2+i,35))
		rec_back_absorbed_err.append(get_rc(num_res+2+i,36))
		rec_back_eff.append(get_rc(num_res+2+i,-2))
		rec_back_eff_err.append(get_rc(num_res+2+i,-1))

	#Virtual target
	vir_area=get_rc(num_res+2+num_rec-1,2)
	vir_income=get_rc(num_res+2+num_rec-1,3)
	vir_income_err=get_rc(num_res+2+num_rec-1,4)
	
	raw_res=np.array([
		['name','value', 'error']
		,['sun_azimuth', azimuth,'']
		,['sun_elevation', elevation, '']
		,['num hst', num_hst,'']
		,['num rays',num_rays, '']
		,['potential flux', potential, potential_err]
		,['absorbed flux', absorbed, absorbed_err]
		,['Cosine factor', Fcos, Fcos_err]
		,['shadow loss', shadow_loss, shadow_err]
		,['Mising loss', missing_loss, missing_err]
		,['materials loss', material_loss, material_err]
		,['atomospheric loss', atmospheric_loss, atmospheric_err]
		,['','','']
		,['','','']
		,['Virtual plane','','']
		,['area', vir_area, '']
		,['income flux', vir_income,vir_income_err]])

	for i in range(num_apertures):
		aperture_i = np.array([
		 ['','','']
		,['Aperture', i,'']
		,['area', rec_area[i], '']
		,['front income flux', rec_front_income[i], rec_front_income_err[i]]
		,['back income flux', rec_back_income[i], rec_back_income_err[i]]
		,['front absorbed flux', rec_front_absorbed[i], rec_front_absorbed_err[i]]
		,['back absorbed flux', rec_back_absorbed[i], rec_back_absorbed_err[i]]
		,['front efficiency', rec_front_eff[i], rec_front_eff_err[i]]
		,['back efficiency', rec_back_eff[i], rec_back_eff_err[i]]])

		raw_res=np.vstack((raw_res, aperture_i))

	#sys.stderr.write(repr(raw_res))
	#sys.stderr.write("SHAPE = %s" % (repr(raw_res.shape)))

	Qtotal=ufloat(potential, 0)
	Fcos=ufloat(Fcos,Fcos_err) 
	Qcos=Qtotal*(1.-Fcos)
	Qshade=ufloat(shadow_loss,shadow_err)
	Qfield_abs=(Qtotal-Qcos-Qshade)*(1.-float(rho_mirror))
	Qattn=ufloat(atmospheric_loss, atmospheric_err)
	Qabs=ufloat(absorbed, absorbed_err)
	Qspil=ufloat(vir_income,vir_income_err)-Qabs
	Qrefl=ufloat(sum(rec_front_income),sum(rec_front_income_err))+ufloat(sum(rec_back_income),sum(rec_back_income_err))-Qabs
	Qblock=Qtotal-Qcos-Qshade-Qfield_abs-Qspil-Qabs-Qrefl-Qattn

	organised=np.array([
		['Name', 'Value', '+/-Error']
		,['Qall (kW)', Qtotal.n/1000., Qtotal.s/1000.]
		,['Qcos (kW)', Qcos.n/1000.,Qcos.s/1000.]
		,['Qshad (kW)', Qshade.n/1000., Qshade.s/1000.]
		,['Qfield_abs (kW)', Qfield_abs.n/1000., Qfield_abs.s/1000.]
		,['Qblcok (kW)', Qblock.n/1000.,  Qblock.s/1000.]
		,['Qattn (kW)',Qattn.n/1000., Qattn.s/1000.]
		,['Qspil (kW)', Qspil.n/1000., Qspil.s/1000.]
		,['Qrefl (kW)', Qrefl.n/1000.,Qrefl.s/1000.]
		,['Qabs (kW)', Qabs.n/1000., Qabs.s/1000.]
		,['rays', num_rays,'-']
	])

	efficiency_total=Qabs/Qtotal

	# per heliostat results, and
	# per receiver per heliostat results
	num_hst=int(num_hst)    
	heliostats=np.zeros((num_hst,28))

	for i in range(num_hst):
		l1=2+num_res+num_rec+i # the line number of the per heliostat result
		per_hst=rows[l1]

		hst_idx=re.findall("[-+]?\d*\.\d+|\d+", per_hst[0] ) 
		hst_area=per_hst[2]
		hst_sample=per_hst[3]
		hst_cos=per_hst[4]
		hst_shad=per_hst[6]

		heliostats[i,0]=hst_idx[0]
		heliostats[i,1]=hst_area
		heliostats[i,2]=hst_sample
		heliostats[i,3]=hst_cos
		heliostats[i,4]=hst_shad

		# per heliostat per receiver
		for j in range(num_rec-1):
			l2=2+num_res+num_rec+num_hst*(j+1)+i  
			per_hst=rows[l2]   
			hst_in=float(per_hst[2])+float(per_hst[22]) # front+back
			hst_in_mat=float(per_hst[8])+float(per_hst[28])
			hst_in_atm=float(per_hst[10])+float(per_hst[30])
			hst_abs=float(per_hst[12])+float(per_hst[32])
			hst_abs_mat=float(per_hst[18])+float(per_hst[38])
			hst_abs_atm=float(per_hst[20])+float(per_hst[40])
			  
			heliostats[i,5]+=hst_in
			heliostats[i,6]+=hst_in_mat
			heliostats[i,7]+=hst_in_atm
			heliostats[i,8]+=hst_abs
			heliostats[i,9]+=hst_abs_mat
			heliostats[i,10]+=hst_abs_atm

		# per heliostat per virtual target
		l3=2+num_res+num_rec+(num_rec)*num_hst+i  
		per_hst=rows[l3] 
		hst_in=float(per_hst[2])+float(per_hst[22]) # front+back
		hst_in_mat=float(per_hst[8])+float(per_hst[28])
		hst_in_atm=float(per_hst[10])+float(per_hst[30])
		hst_abs=float(per_hst[12])+float(per_hst[32])
		hst_abs_mat=float(per_hst[18])+float(per_hst[38])
		hst_abs_atm=float(per_hst[20])+float(per_hst[40])
		  
		heliostats[i,11]=hst_in
		heliostats[i,12]=hst_in_mat
		heliostats[i,13]=hst_in_atm
		heliostats[i,14]=hst_abs
		heliostats[i,15]=hst_abs_mat
		heliostats[i,16]=hst_abs_atm


		hst_tot=float(hst_area)*1000.
		hst_cos=hst_tot*(1.-float(hst_cos))
		hst_shad=float(hst_shad)
		hst_abs=(hst_tot-hst_cos-hst_shad)*(1.-rho_mirror)

		hst_atm=float(heliostats[i,10])
		hst_rec_abs=float(heliostats[i,8])
		hst_spil=float(heliostats[i,11])-hst_rec_abs
		hst_rec_refl=float(heliostats[i,5])-float(heliostats[i,8])
		hst_block=hst_tot-hst_cos-hst_shad-hst_abs-hst_atm-hst_spil-hst_rec_abs-hst_rec_refl

		heliostats[i,19]=hst_tot
		heliostats[i,20]=hst_cos
		heliostats[i,21]=hst_shad
		heliostats[i,22]=hst_abs
		heliostats[i,23]=hst_block
		heliostats[i,24]=hst_atm
		heliostats[i,25]=hst_spil
		heliostats[i,26]=hst_rec_refl
		heliostats[i,27]=hst_rec_abs

	idx=heliostats[:, 0].argsort()
	heliostats=heliostats[idx]
	performance_hst=heliostats[:, 19:]

	heliostats_title=np.array(['hst_idx', 'area', 'sample', 'cos', 'shade', 'incoming', 'in-mat-loss','in-atm-loss', 'absorbed', 'abs-mat-loss', 'abs-atm-loss', 'vir_incoming', 'vir_in-mat-loss','vir_in-atm-loss', 'vir_absorbed', 'vir_abs-mat-loss', 'vir_abs-atm-loss', '', '', 'total', 'cos', 'shad', 'hst_abs', 'block', 'atm', 'spil', 'rec_refl', 'rec_abs' ]) 

	heliostats_details=np.vstack((heliostats_title, heliostats))

	if verbose:
		np.savetxt(savedir+'/result-formatted.csv', organised, fmt='%s', delimiter=',')
		np.savetxt(savedir+'/heliostats-raw.csv', heliostats_details, fmt='%s', delimiter=',')
		np.savetxt(savedir+'/result-raw.csv', raw_res, fmt='%s', delimiter=',')
	else:
		os.system('rm -rf %s'%savedir)
	return efficiency_total, performance_hst


def get_breakdown(casedir):
	"""Postprocess the .csv output files (heliostats-raw.csv, before trimming), to obtain the breakdown of total energy losses of the designed field (after trimming) for central receiver systems

	``Argument``
		* casedir (str): the directory of the case that contains the folder of sunpos_1, sunpos_2, ..., and all the other case-related details
	    * verbose (bool), write results to disk or not

	``Outputs``
		* output file: OELT_Solstice_breakdown.motab, it contains the annual lookup tables of each breakdown of energy  
		* output files: result-formatted-designed.csv file in each sunpos folder, each of them is a list of the breakdown of energy at this sun position
	
	"""
	table=np.loadtxt(casedir+'/table_view.csv', dtype=str, delimiter=',')
	idx=np.loadtxt(casedir+'/selected_hst.csv', dtype=int, delimiter=',') #index of the selected heliostats

	cosn=table
	shad=table
	hsta=table
	blck=table
	attn=table
	spil=table
	refl=table
	absr=table
	breakdown=np.array([absr, cosn, shad, hsta, blck, attn, spil, refl])
	title_breakdown=['eta_rcv_absorption','eta_cosine', 'eta_shading', 'eta_helios_absorption', 'eta_blocking', 'eta_attenuation', 'eta_spillage', 'eta_rcv_reflection']
	tot=len(title_breakdown)

	for a in range(len(table[3:])):
		for b in range(len(table[0,3:])):
			val=re.findall(r'\d+',table[a+3,b+3])
			if len(val)==0:
				for i in range(tot):
					breakdown[i][a+3,b+3]=0
			else:
				c=val[0]
				resfile=casedir+'/sunpos_%s/result-formatted-designed.csv'%c
				if os.path.exists(resfile):
					res=np.loadtxt(resfile, dtype=str, delimiter=',')
					eta_cos=res[2,2].astype(float)
					eta_shad=res[3,2].astype(float)
					eta_hst=res[4,2].astype(float)
					eta_block=res[5,2].astype(float)
					eta_attn=res[6,2].astype(float)
					eta_spil=res[7,2].astype(float)
					eta_refl=res[8,2].astype(float)
					eta_abs=res[9,2].astype(float)

				else:
					raw=np.loadtxt(casedir+'/sunpos_%s/heliostats-raw.csv'%c, delimiter=',', skiprows=1)
					data=raw[:, -9:]
					res_selected=data[idx]
					Qtot=np.sum(res_selected[:,0])
					Qcos=np.sum(res_selected[:,1])
					Qshad=np.sum(res_selected[:,2])
					Qhst=np.sum(res_selected[:,3])
					Qblock=np.sum(res_selected[:,4])
					Qattn=np.sum(res_selected[:,5])
					Qspil=np.sum(res_selected[:,6])
					Qrefl=np.sum(res_selected[:,7])
					Qabs=np.sum(res_selected[:,8])

					eta_cos=Qcos/Qtot
					eta_shad=Qshad/Qtot
					eta_hst=Qhst/Qtot
					eta_block=Qblock/Qtot
					eta_attn=Qattn/Qtot
					eta_spil=Qspil/Qtot
					eta_refl=Qrefl/Qtot
					eta_abs=Qabs/Qtot	

					res=np.array([
					 ['Name', 'Value (kW)', 'eta Ratio']
				    ,['Qall', Qtot,   1]
					,['Qcos', Qcos,   eta_cos]
					,['Qshad', Qshad, eta_shad]
					,['Qfield_abs', Qhst, eta_hst]
					,['Qblcok', Qblock, eta_block]
					,['Qattn',Qattn,  eta_attn]
					,['Qspil ', Qspil,eta_spil]
					,['Qrefl', Qrefl, eta_refl]
					,['Qabs ', Qabs,  eta_abs]
					,['After trimming', 'postprocessed results','-']
					])
					np.savetxt(casedir+'/sunpos_%s/result-formatted-designed.csv'%c, res, fmt='%s', delimiter=',')

				eta_all=[eta_abs, eta_cos, eta_shad, eta_hst, eta_block, eta_attn, eta_spil, eta_refl]
				for i in range(tot):
					if eta_all[i]<1e-8:
						breakdown[i][a+3,b+3]=0.
					else:
						breakdown[i][a+3,b+3]=eta_all[i]
	output_motab(table=breakdown, savedir=casedir+'/OELT_Solstice_breakdown.motab', title=title_breakdown)
	
	# at design point
	raw=np.loadtxt(casedir+'/des_point/heliostats-raw.csv', delimiter=',', skiprows=1)
	data=raw[:, -9:]
	res_selected=data[idx]
	Qtot=np.sum(res_selected[:,0])
	Qcos=np.sum(res_selected[:,1])
	Qshad=np.sum(res_selected[:,2])
	Qhst=np.sum(res_selected[:,3])
	Qblock=np.sum(res_selected[:,4])
	Qattn=np.sum(res_selected[:,5])
	Qspil=np.sum(res_selected[:,6])
	Qrefl=np.sum(res_selected[:,7])
	Qabs=np.sum(res_selected[:,8])

	eta_cos=Qcos/Qtot
	eta_shad=Qshad/Qtot
	eta_hst=Qhst/Qtot
	eta_block=Qblock/Qtot
	eta_attn=Qattn/Qtot
	eta_spil=Qspil/Qtot
	eta_refl=Qrefl/Qtot
	eta_abs=Qabs/Qtot	

	res=np.array([
	 ['Name', 'Value (kW)', 'eta Ratio']
    ,['Qall', Qtot,   1]
	,['Qcos', Qcos,   eta_cos]
	,['Qshad', Qshad, eta_shad]
	,['Qfield_abs', Qhst, eta_hst]
	,['Qblcok', Qblock, eta_block]
	,['Qattn',Qattn,  eta_attn]
	,['Qspil ', Qspil,eta_spil]
	,['Qrefl', Qrefl, eta_refl]
	,['Qabs ', Qabs,  eta_abs]
	,['After trimming', 'postprocessed results','-']
	])
	np.savetxt(casedir+'/des_point/result-formatted-designed.csv', res, fmt='%s', delimiter=',')	

def process_raw_results_dish(rawfile, savedir,rho_mirror,dni,verbose=False):
	"""Process the raw Solstice `simul` output into readable CSV files for dish systems

	``Arguments``

	  * rawfile (str): the directory of the `simul` file that generated by Solstice
	  * savedir (str): the directory for saving the organised results
	  * rho_mirror (float): mirror reflectivity (needed for reporting energy sums)
	  * dni (float): the direct normal irradiance (W/m2), required to obtain performance of individual heliostat

	``Returns``

	  * efficiency_total (float): the total optical efficiency
	  * The simulation results are created and written in the `savedir`
		
	"""

	# FIXME this approach seems fundamentally a bit messy... we are carefully
	# load the text output from 'solppraw' and then assuming that we can
	# correctly find the right bits of data in the right place. Wouldn't it
	# be easier and more robust to modify solppraw to create output that can
	# be directly loaded, along with data labels, eg a YAML file? Or to
	# create 'result-raw.csv' directly?

	rows = []
	index = 0
	with open(rawfile) as f:
		for r in f.readlines():
			if index<20:
				pass #sys.stderr.write("Line %d: %s"%(index,r))

			if r[0] == "#":
				#sys.stderr.write("^------Comment\n")
				#comment line
				rows.append([r])
			else:
				rows.append(r.split())			
			index+=1

	results=np.array([])

	# sun direction

	#sys.stderr.write("SUN DIRECTION?\n")
	#sys.stderr.write(rows[0][0]+"\n")
	sun=re.findall("[-+]?\d*\.\d+|\d+", rows[0][0])
	#sys.stderr.write("SUN = %s\n"%(repr(sun),))

	azimuth=sun[0]
	elevation=sun[1]

	def get_rc(row,col):
		return float(rows[row][col])

	# Global results

	num_res=int(get_rc(1,0)) # number of global results
	num_rec=int(get_rc(1,1))
	num_hst=get_rc(1,2)
	num_rays=get_rc(1,3)

	potential=get_rc(2,0) #W
	potential_err=get_rc(2,1)

	absorbed=get_rc(3,0)
	absorbed_err=get_rc(3,1)    

	Fcos=get_rc(4,0)
	Fcos_err=get_rc(4,1)  

	shadow_loss=get_rc(5,0)
	shadow_err=get_rc(5,1)    

	missing_loss=get_rc(6,0)
	missing_err=get_rc(6,1) 

	material_loss=get_rc(7,0)
	material_err=get_rc(7,1)    

	atmospheric_loss=get_rc(8,0)
	atmospheric_err=get_rc(8,1)  

	# Target (receiver)
	# 0 receiver name
	# 1 - 2 id and area
	# 3 - 24 (total 22) front
	# 25- 46 (total 22) back 
	rec_area=get_rc(num_res+2,2) # m2  
	
	rec_front_income=get_rc(num_res+2,3)
	rec_front_income_err=get_rc(num_res+2,4)

	rec_front_absorbed=get_rc(num_res+2,5)
	rec_front_absorbed_err=get_rc(num_res+2,6)
	rec_front_eff=get_rc(num_res+2,23)
	rec_front_eff_err=get_rc(num_res+2,24)

	rec_back_income=get_rc(num_res+2,25)
	rec_back_income_err=get_rc(num_res+2,26)
	rec_back_absorbed=get_rc(num_res+2,35)
	rec_back_absorbed_err=get_rc(num_res+2,36)
	rec_back_eff=get_rc(num_res+2,-2)
	rec_back_eff_err=get_rc(num_res+2,-1)


		
	raw_res=np.array([
		['name','value', 'error']
		,['sun_azimuth', azimuth,'']
		,['sun_elevation', elevation, '']
		,['num hst', num_hst,'']
		,['num rays',num_rays, '']
		,['potential flux', potential, potential_err]
		,['absorbed flux', absorbed, absorbed_err]
		,['Cosine factor', Fcos, Fcos_err]
		,['shadow loss', shadow_loss, shadow_err]
		,['Mising loss', missing_loss, missing_err]
		,['materials loss', material_loss, material_err]
		,['atomospheric loss', atmospheric_loss, atmospheric_err]
		,['','','']
		,['Target', '','']
		,['area', rec_area, '']
		,['front income flux', rec_front_income, rec_front_income_err]
		,['back income flux', rec_back_income, rec_back_income_err]
		,['front absorbed flux', rec_front_absorbed, rec_front_absorbed_err]
		,['back absorbed flux', rec_back_absorbed, rec_back_absorbed_err]
		,['front efficiency', rec_front_eff, rec_front_eff_err]
		,['back efficiency', rec_back_eff, rec_back_eff_err]
	])

	#sys.stderr.write(repr(raw_res))
	#sys.stderr.write("SHAPE = %s" % (repr(raw_res.shape)))


	Qtotal=ufloat(potential, 0)
	Qshad=ufloat(shadow_loss, shadow_err)
	Qdish=(Qtotal-Qshad)*(1.-rho_mirror)
	Qabs=ufloat(absorbed, absorbed_err)
	Qrefl=ufloat(rec_front_income,rec_front_income_err)+ufloat(rec_back_income,rec_back_income_err)-Qabs
	Qspil=Qtotal-Qshad-Qdish-Qabs-Qrefl


	organised=np.array([
		['Name', 'Value', '+/-Error']
		,['Qall (kW)', Qtotal.n/1000., Qtotal.s/1000.]
		,['Qshad (kW)', Qshad.n/1000., Qshad.s/1000.]
		,['Qdish_abs (kW)', Qdish.n/1000., Qdish.s/1000.]
		,['Qspil (kW)', Qspil.n/1000., Qspil.s/1000.]
		,['Qrefl (kW)', Qrefl.n/1000.,Qrefl.s/1000.]
		,['Qabs (kW)', Qabs.n/1000., Qabs.s/1000.]
		,['rays', num_rays,'-']
	])

	efficiency_total=Qabs/Qtotal

	if verbose:
		np.savetxt(savedir+'/result-formatted.csv', organised, fmt='%s', delimiter=',')
		np.savetxt(savedir+'/result-raw.csv', raw_res, fmt='%s', delimiter=',')



	return efficiency_total
		

if __name__=='__main__':
    eta,pf_hst = proces_raw_results(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.stderr.write('\nTotal efficiency: %s\n'%(repr(eta),))


