#!/bin/bash
#SBATCH --job-name=prcp2014
#SBATCH --time=0-6:00:00
#SBATCH --mem=20G
module load python/3.7.4
srun python -u s6_rea_corrmerge_LS.py prcp BMA Mul_Climo 2014 2014