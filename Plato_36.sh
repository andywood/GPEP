#!/bin/bash
#SBATCH --job-name=pop36
#SBATCH --time=1-00:00:00
#SBATCH --mem=10G
module load python/3.7.4
srun python -u reanalysis_pop.py 10501 10801
