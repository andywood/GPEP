#!/bin/bash
#SBATCH --job-name=PG_199012
#SBATCH --time=2-00:00:00
#SBATCH --mem=20G
module load python/3.7.4
srun python main_CAI.py 19901201 19901231
