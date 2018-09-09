import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--conf", type=str, required=True,
                    help="path to conf.json with number of dummy atom and atoms to pull")
parser.add_argument("-o", "--out", type=str, required=True, help="path to out constraints file")
parser.add_argument("-n", "--min", type=int, required=True, help="max distance with the lowest potential energy")
parser.add_argument("-x", "--max", type=int, required=True, help="min distance with 0 potential energy")
parser.add_argument("-s", "--step", type=float, required=True, help="potential step, in reduced piDMD units")
args = parser.parse_args()

atmfile = args.conf
outfile = args.out
mindist = args.min
maxdist = args.max
nrgstep = args.step

dummies = json.load(open(atmfile))
with open(outfile, "w") as f:
    for dummy in dummies:
        dm = dummy["pattern"]
        print(dm)
        for atom in dummy["atoms"]:
            at = atom["pattern"]
            cur_line = "{} {} 2.4 ".format(dm, at)
            string = ""
            for i in range(mindist, maxdist + 1):
                string += "{} {} ".format(i, -nrgstep)
            f.write(cur_line + string + "\n")
