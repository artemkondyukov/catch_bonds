import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inp", type=str, required=True, help="path to xpm file obtained from Gromacs")
parser.add_argument("-o", "--hdr", type=int, required=True, help="number of lines preceding distance data")
parser.add_argument("-f", "--fst", type=int, required=True, help="length of the first chain")
parser.add_argument("-s", "--snd", type=int, required=True, help="length of the second chain")
args = parser.parse_args()

with open(args.inp, "r") as f:
    data_lines = f.readlines()
step = args.fst + args.snd + 1
    
data_lines = [list(d[1:step+1]) for d in data_lines]
data_chunks = [data_lines[i:i+step][::-1]
               for i in np.arange(args.hdr, len(data_lines), step + args.hdr)]

data_arrays = [np.array(d)[None, :, :] for d in data_chunks]
data_array = np.concatenate(data_arrays)
contacts_matrix = data_array <= 'N'

for f, s in zip(*np.where(contacts_matrix.mean(axis=0))):
    if f < args.fst <= s:
            print(f, s)
