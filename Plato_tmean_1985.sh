#!/bin/bash
#SBATCH --job-name=tmean1985
#SBATCH --time=0-3:00:00
#SBATCH --mem=20G
module load python/3.7.4
srun python -u s6_rea_corrmerge_No.py tmean BMA zz 1985 1985
