#!/bin/bash
#SBATCH --job-name=prcp10
#SBATCH --time=0-6:00:00
#SBATCH --mem=20G
module load python/3.7.4
srun python -u s8_oimerge.py prcp 10