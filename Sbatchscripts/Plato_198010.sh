#!/bin/bash
#SBATCH --job-name=PG_198010
#SBATCH --time=2-00:00:00
#SBATCH --mem=20G
module load python/3.7.4
srun python main_CAI.py 19801001 19801031
