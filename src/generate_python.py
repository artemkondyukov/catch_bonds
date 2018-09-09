import argparse


def process_constraints_template(constraints_filename,
                                 processed_constraints_filename,
                                 min_dist,
                                 max_dist,
                                 energy_step):
    with open(constraints_filename, "r") as f_in, open(processed_constraints_filename, "w") as f_out:
        for line in f_in:
            constraint = line.split()
            first, second = constraint[0], constraint[1]

            cur_line = "{} {} 2.4".format(first, second)
            for i in range(min_dist, max_dist + 1):
                cur_line += "{} {} ".format(i, -energy_step)
            f_out.write(cur_line + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--conf", type=str, required=True, help="path to file with atom pair constraints")
    parser.add_argument("-o", "--out", type=str, required=True, help="path to out constraints file")
    parser.add_argument("-n", "--min", type=int, required=True, help="max distance with the lowest potential energy")
    parser.add_argument("-x", "--max", type=int, required=True, help="min distance with 0 potential energy")
    parser.add_argument("-s", "--step", type=float, required=True, help="potential step, in reduced piDMD units")
    args = parser.parse_args()
    process_constraints_template(args.conf, args.out, args.min, args.max, args.step)
