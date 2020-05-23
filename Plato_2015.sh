#!/bin/bash
#SBATCH --job-name=err_2015
#SBATCH --time=0-4:00:00
#SBATCH --mem=10G
module load python/3.7.4
srun python -u reanalysis_downscale.py 2015 2016 GWR
