"""Area-weighted share of pine that is stranded, and the carbon it represents."""
import netCDF4 as nc, numpy as np
B=('/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/'
   '20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup/run/'
   '20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup.elm.h1.0001-01-01-00000.nc')
g=lambda d,n,t=None: np.ma.filled(np.asarray(d.variables[n][t] if t is not None else d.variables[n][:],dtype=float),np.nan)
d=nc.Dataset(B)
mc=np.asarray(d.variables['mcdate'][:],dtype=int); yrs=mc//10000-1
tb=np.ma.filled(np.asarray(d.variables['time_bounds'][:],dtype=float),np.nan)
full=np.flatnonzero(np.abs((tb[:,1]-tb[:,0])-365.0)<=0.5)
sel=[i for i in full if yrs[i]>=41]
nlon=len(g(d,'lon')); lat=g(d,'lat'); lon=g(d,'lon')
ix=g(d,'pfts1d_ixy').astype(int)-1; jy=g(d,'pfts1d_jxy').astype(int)-1
key=jy*nlon+ix; veg=g(d,'pfts1d_itype_veg').astype(int); lun=g(d,'pfts1d_itype_lunit').astype(int)
wt=g(d,'pfts1d_wtgcell')
lai=np.zeros(len(key)); lc=np.zeros(len(key)); vc=np.zeros(len(key))
for i in sel:
    lai+=np.nan_to_num(g(d,'TLAI',i)); lc+=np.nan_to_num(g(d,'LEAFC',i)); vc+=np.nan_to_num(g(d,'TOTVEGC',i))
lai/=len(sel); lc/=len(sel); vc/=len(sel)
d.close()
plat=lat[key//nlon]; plon=lon[key%nlon]
pine=(veg==1)&(lun==1)&(wt>0)
regions={'whole domain':pine,'Florida box':pine&(plat<=31.0)&(plon>=-87.6),
         'south of 26N':pine&(plat<26.0),'the 405 cluster band (25-27N)':pine&(plat>=25)&(plat<27)}
print(f"{'region':32s} {'pine area wt':>12} {'stranded wt%':>12} {'vegC lost%':>11} {'healthy vegC':>13}")
for nm,m in regions.items():
    w=wt[m]; bad=(lai[m]<0.5)
    tot=w.sum(); badw=w[bad].sum()
    hv=np.average(vc[m][~bad],weights=w[~bad]) if (~bad).any() else np.nan
    lost=badw*hv - (w[bad]*vc[m][bad]).sum()
    total_if_healthy=(w*vc[m]).sum()+lost
    print(f"{nm:32s} {tot:12.1f} {100*badw/tot:11.2f}% {100*lost/total_if_healthy:10.2f}% {hv:13.1f}")
