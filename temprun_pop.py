# pop estimation using logistic regression
# computation time:
# pop estimation for all stations: 74 jobs. ~7 to 18 hours per job

import numpy as np
import regression as reg
from scipy import io
import os, sys
from bma_merge import bma
from auxiliary_merge import extrapolation
import netCDF4 as nc

########### other choices for logistic regression
# LogisticRegression with solver='lbfgs' is two times faster than the least-square iterations
# SGDClassifier with default setting is sevent times faster, but not as accurate
# more testing would be needed
from sklearn.linear_model import LogisticRegression, SGDClassifier
########### other choices for logistic regression

# read from inputs
# time1 = int(sys.argv[1])
# time2 = int(sys.argv[2])
# print(time1,time2)

yearin = int(sys.argv[1])
monthin = int(sys.argv[2])
print(yearin,monthin)

prefix = ['ERA5_', 'MERRA2_', 'JRA55_']

# ### Local Mac settings
# # input files/paths
# gmet_stnfile = '/Users/localuser/Research/EMDNA/basicinfo/stnlist_whole.txt'
# gmet_stndatafile = '/Users/localuser/Research/EMDNA/stndata_whole.npz'
# file_mask = './DEM/NA_DEM_010deg_trim.mat'
# near_file_GMET = '/Users/localuser/Research/EMDNA/regression/weight_nearstn.npz' # near station of stations/grids
# path_readowngrid = ['/Users/localuser/Research/EMDNA/downscale/ERA5',  # downscaled gridded data
#                     '/Users/localuser/Research/EMDNA/downscale/MERRA2',
#                     '/Users/localuser/Research/EMDNA/downscale/JRA55']
# file_readownstn = ['/Users/localuser/Research/EMDNA/downscale/ERA5_downto_stn_nearest.npz', # downscaled to stn points
#                    '/Users/localuser/Research/EMDNA/downscale/MERRA2_downto_stn_nearest.npz',
#                    '/Users/localuser/Research/EMDNA/downscale/JRA55_downto_stn_nearest.npz']
#
# # output files/paths (can also be used as inputs once generated)
# path_pop = '/Users/localuser/Research/EMDNA/pop'
# ### Local Mac settings


### Plato settings
FileGridInfo = '/datastore/GLOBALWATER/CommonData/EMDNA_new/StnGridInfo/gridinfo_whole.nc'
gmet_stnfile = '/datastore/GLOBALWATER/CommonData/EMDNA_new/StnGridInfo/stnlist_whole.txt'
gmet_stndatafile = '/datastore/GLOBALWATER/CommonData/EMDNA_new/stndata_aftercheck.npz'
file_mask = '/datastore/GLOBALWATER/CommonData/EMDNA_new/DEM/NA_DEM_010deg_trim.mat'
near_file_GMET = '/datastore/GLOBALWATER/CommonData/EMDNA_new/stn_reg_aftercheck/nearstn_catalog.npz'
path_readowngrid = ['/datastore/GLOBALWATER/CommonData/EMDNA_new/ERA5_day_ds',  # downscaled gridded data
                   '/datastore/GLOBALWATER/CommonData/EMDNA_new/MERRA2_day_ds',
                   '/datastore/GLOBALWATER/CommonData/EMDNA_new/JRA55_day_ds']
file_readownstn = ['/datastore/GLOBALWATER/CommonData/EMDNA_new/ERA5_day_ds/ERA5_downto_stn_GWR.npz', # downscaled to stn points
                   '/datastore/GLOBALWATER/CommonData/EMDNA_new/MERRA2_day_ds/MERRA2_downto_stn_GWR.npz',
                   '/datastore/GLOBALWATER/CommonData/EMDNA_new/JRA55_day_ds/JRA55_downto_stn_GWR.npz']
path_pop = '/home/gut428/ReanalysisCorrMerge/pop'
### Plato settings

file_reapop_stn = path_pop + '/reanalysis_pop_stn.npz'
file_popmerge_stn = path_pop + '/merge_stn_pop_GWR_BMA.npz'

########################################################################################################################

# basic processing
print('start basic processing')

reanum = len(prefix)

# mask
mask = io.loadmat(file_mask)
mask = mask['DEM']
mask[~np.isnan(mask)] = 1  # 1: valid pixels
nrows, ncols = np.shape(mask)

# meshed lat/lon of the target region
ncfid = nc.Dataset(FileGridInfo)
lattarm = ncfid.variables['latitude'][:].data
lattarm = np.flipud(lattarm)
lontarm = ncfid.variables['longitude'][:].data
ncfid.close()
lontarm[np.isnan(mask)] = np.nan
lattarm[np.isnan(mask)] = np.nan
lontar = lontarm[0, :]
lattar = lattarm[:, 0]

# load observations for all stations
datatemp = np.load(gmet_stndatafile)
stndata = datatemp['prcp_stn']
stninfo = datatemp['stninfo']
stnID = datatemp['stnID']
date_ymd = datatemp['date_ymd']
nstn, ntimes = np.shape(stndata)
del datatemp
date_yyyy = (date_ymd/10000).astype(int)
date_mm = (np.mod(date_ymd, 10000)/100).astype(int)

# load near station information
datatemp = np.load(near_file_GMET)
near_loc_stn = datatemp['near_stn_prcpLoc']
near_weight_stn = datatemp['near_stn_prcpWeight']
near_dist_stn = datatemp['near_stn_prcpDist']
near_loc_grid = datatemp['near_grid_prcpLoc']
near_weight_grid = datatemp['near_grid_prcpWeight']
near_dist_grid = datatemp['near_grid_prcpDist']
near_loc_grid = np.flipud(near_loc_grid)
near_weight_grid = np.flipud(near_weight_grid)
near_dist_grid = np.flipud(near_dist_grid)
del datatemp

# # probability bins for QM # used in method 2
# binprob = 500
# ecdf_prob = np.arange(0, 1 + 1 / binprob, 1 / binprob)

########################################################################################################################

# load downscaled reanalysis at station points
print('load downscaled reanalysis data at station points')
readata_stn = np.nan * np.zeros([reanum, nstn, ntimes], dtype=np.float32)
for rr in range(reanum):
    dr = np.load(file_readownstn[rr])
    temp = dr['prcp_readown']
    readata_stn[rr, :, :] = temp
    del dr, temp
readata_stn[readata_stn < 0] = 0


########################################################################################################################

for y in range(yearin, yearin + 1):
    for m in range(monthin-1, monthin):
        print('year,month',y,m+1)
        file_reapop = path_pop + '/rea_pop_' + str(y * 100 + m + 1) + '.npz'
        file_bmapop = path_pop + '/bmamerge_pop_' + str(y * 100 + m + 1) + '.npz'
        if os.path.isfile(file_bmapop):
            print('file exists ... continue')
            continue

        # date processing
        indmy = (date_yyyy == y) & (date_mm == m + 1)
        mmdays = np.sum(indmy)

        # read raw gridded reanalysis data
        readata_raw = np.nan * np.zeros([reanum, nrows, ncols, mmdays], dtype=np.float32)
        for rr in range(reanum):
            if not (prefix[rr] == 'MERRA2_' and y == 1979):
                filer = path_readowngrid[rr] + '/' + prefix[rr] + 'ds_prcp_' + str(y*100 +m+1) + '.npz'
                d = np.load(filer)
                readata_raw[rr, :, :, :] = d['data']
                del d

        readata_stnym = readata_stn[:, :, indmy].copy()
        stndataym = stndata[:, indmy].copy()

        ################################################################################################################
        print('estimate pop for all grids')
        reapop_grid = np.nan * np.zeros([reanum, nrows, ncols, mmdays], dtype=np.float32)
        if os.path.isfile(file_reapop):
            datatemp = np.load(file_reapop)
            reapop_grid = datatemp['reapop_grid']
            del datatemp
        else:
            for r in range(nrows):
                if np.mod(r, 10) == 0:
                    print(r, nrows)
                for c in range(ncols):
                    if np.isnan(mask[r, c]):
                        continue
                    nearloc = near_loc_grid[r, c, :]
                    neardist = near_dist_grid[r, c, :]
                    nearweight = near_weight_grid[r, c, :]
                    neardist = neardist[nearloc > -1]
                    nearweight = nearweight[nearloc > -1]
                    nearweight = nearweight / np.sum(nearweight)
                    nearloc = nearloc[nearloc > -1]

                    nstn_prcp = len(nearloc)
                    w_pcp_red = np.zeros([nstn_prcp, nstn_prcp])
                    for i in range(nstn_prcp):
                        w_pcp_red[i, i] = nearweight[i]  # eye matrix: stn weight in one-one lien

                    x_red = np.ones([nstn_prcp, 2])
                    for rr in range(reanum):
                        for tt in range(mmdays):
                            prea_tar = readata_raw[rr, r, c, tt]
                            if np.isnan(prea_tar):
                                continue
                            prea_near = readata_stnym[rr, nearloc, tt]
                            pstn_near = stndataym[nearloc, tt]
                            pstn_near[pstn_near > 0] = 1

                            # logistic regression
                            if np.all(pstn_near == 1):
                                reapop_grid[rr, r, c, tt] = 1
                            elif np.all(pstn_near == 0) or np.all(prea_near < 0.01):
                                reapop_grid[rr, r, c, tt] = 0
                            else:
                                x_red[:, 1] = prea_near
                                tx_red = np.transpose(x_red)
                                twx_red = np.matmul(tx_red, w_pcp_red)
                                b = reg.logistic_regression(x_red, twx_red, pstn_near)
                                if np.all(b == 0) or np.any(np.isnan(b)):
                                    reapop_grid[rr, r, c, tt] = np.dot(nearweight, pstn_near)
                                else:
                                    zb = - np.dot(np.array([1, prea_tar]), b)
                                    reapop_grid[rr, r, c, tt] = 1 / (1 + np.exp(zb))

                                # # another choice for logistic regression
                                # # model=SGDClassifier(loss='log')
                                # model = LogisticRegression(solver='lbfgs')
                                # model.fit(np.reshape(prea_near, [-1, 1]), pstn_near, sample_weight=nearweight)
                                # reapop_grid[rr, r, c, tt] = model.predict_proba(np.reshape(prea_tar, [-1, 1]))[0][1]

            np.savez_compressed(file_reapop, reapop_grid=reapop_grid, latitude=lattar, longitude=lontar, prefix=prefix)