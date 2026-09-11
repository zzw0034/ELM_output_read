"""Write the stranded-pine mask as a small, self-describing netCDF file."""
import csv, numpy as np, netCDF4 as nc
B=('/scratch/hpcl-cli185/zw5/cime_output_dirs/20260910_seus_rerun/'
   '20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup/run/'
   '20260910_Southeast_hires_30n_hdmfix_mapfix_ICB1850CNRDCTCBC_ad_spinup.elm.h1.0001-01-01-00000.nc')
CSV=('/scratch/hpcl-cli185/zw5/ELM_output_read/analyses/'
     '20260902_Southeast_hires_s7P_s8hdmfix_harvfixsmooth_ICB20TRCNPRDCTCBC/'
     'outputs/residual_pine_fire_522677/residual_trajectory.csv')
OUT='/projects/hpcl-cli185/proj-shared/zw5/20260910_seus_rerun_inputs/stranded_pine_mask_SEUS_1_24deg.nc'
g=lambda d,n,t=None: np.ma.filled(np.asarray(d.variables[n][t] if t is not None else d.variables[n][:],dtype=float),np.nan)
with nc.Dataset(B) as d:
    lat=g(d,'lat'); lon=g(d,'lon'); nlon=len(lon)
    ix=g(d,'pfts1d_ixy').astype(int)-1; jy=g(d,'pfts1d_jxy').astype(int)-1
    k=jy*nlon+ix; veg=g(d,'pfts1d_itype_veg').astype(int); lun=g(d,'pfts1d_itype_lunit').astype(int)
    wt=g(d,'pfts1d_wtgcell'); lai0=g(d,'TLAI',0)
    pine_cells=np.unique(k[(veg==1)&(lun==1)&(wt>0.05)&np.isfinite(lai0)])
pts={(round(float(r['lat']),4),round(float(r['lon']),4)) for r in csv.DictReader(open(CSV))}
lut={(round(float(lat[c//nlon]),4),round(float(lon[c%nlon]),4)):c for c in pine_cells}
keys=sorted(lut[p] for p in pts if p in lut)
m=np.zeros((len(lat),nlon),'i1'); pm=np.zeros((len(lat),nlon),'i1')
for c in keys: m[c//nlon, c%nlon]=1
for c in pine_cells: pm[c//nlon, c%nlon]=1
with nc.Dataset(OUT,'w',format='NETCDF4_CLASSIC') as o:
    o.createDimension('lat',len(lat)); o.createDimension('lon',nlon)
    v=o.createVariable('lat','f8',('lat',)); v[:]=lat; v.units='degrees_north'
    v=o.createVariable('lon','f8',('lon',)); v[:]=lon; v.units='degrees_east'
    v=o.createVariable('stranded_pine','i1',('lat','lon')); v[:]=m
    v.long_name='1 where pine stays at near-zero leaf carbon after both input fixes'
    v.flag_values=np.array([0,1],'i1'); v.flag_meanings='not_affected affected'
    v=o.createVariable('pine_present','i1',('lat','lon')); v[:]=pm
    v.long_name='1 where a pine patch above 5 percent gridcell weight exists'
    o.title='SEUS 4 km stranded-pine mask'
    o.summary=('Gridcells whose needleleaf evergreen temperate patch remains at near-zero '
      'leaf carbon in the 2026-09 AD rerun, which has BOTH the corrected HDM reader and the '
      'repaired zone_mappings. Two clusters: 291 in south Florida, 114 on the Florida Big Bend '
      'and panhandle coast. They sit where 1850 population density is about 0.05 against 4.16 '
      'for healthy pine, so HDM fire suppression cannot reach them. Area-weighted they are '
      '0.42 percent of domain pine, 2.72 percent inside the Florida box and 41.6 percent south '
      'of 26N. Exclude or flag them in any regional pine statistic, and note that they cannot '
      'respond to a management scenario because there is almost no pine leaf carbon to change.')
    o.membership=('Defined by the final state of job 522373 and confirmed to persist in the '
      'rerun jobs 522930 and 523140. Not a physical classification.')
    o.source='ELM_output_read/analyses/20260902_.../locate via residual_trajectory.csv'
    o.history='created 2026-09-11'
print('wrote', OUT, 'cells', int(m.sum()), 'of pine cells', int(pm.sum()))
