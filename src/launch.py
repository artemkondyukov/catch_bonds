import argparse
import os
import subprocess

from generate_python import process_constraints_template


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--repetitions", type=int, required=True,
                        help="Number of repetitions of MD simulation for each force")
    parser.add_argument("-f", "--force_levels", type=int, required=True, help="Number of force levels to apply")
    parser.add_argument("-d", "--divisor", type=int, required=True, help="Scale factor of applied force")
    parser.add_argument("-s", "--structure_name", type=str, required=True)
    parser.add_argument("-n", "--min_dist", type=int, required=True, help="Maximum distance of lowest energy")
    parser.add_argument("-x", "--max_dist", type=int, required=True, help="Minimum distance with 0 energy")
    parser.add_argument("-b", "--box", type=int, required=True, help="Size of the simulation box")
    parser.add_argument("-p", "--pidmd_dir", type=str, required=True, help="Directory with executables of piDMD")
    parser.add_argument("-o", "--out_dir", type=str, required=True, help="Where to store MD conf files")
    parser.add_argument("-l", "--log", type=str, required=True, help="Logfile")
    parser.add_argument("-q", "--queue", type=str, required=True, help="SGE queue name")
    args = parser.parse_args()

    for rep in range(args.repetitions):
        for force_ in range(args.force_levels):
            force = force_ / args.divisor
            force_str = str(int(force)) if force == int(force) else str(force)
            complex_linux = os.path.join(args.pidmd_dir, "complex.linux")
            dmd_exec = os.path.join(args.pidmd_dir, "pdmd.linux")
            cur_dir = "{}/{}/{}".format(args.out_dir, rep, force_str)
            os.makedirs(cur_dir)

            tmp_constraints_filename = os.path.join(cur_dir, "tmp_cons")
            d_constraints_filename = os.path.join(cur_dir, "dynamic_constraints")
            s_constraints_filename = os.path.join(cur_dir, "static_constraints")
            s_constraints_template_filename = "{}/infiles/static_constraints_template".format(args.structure_name)
            d_constraints_template_filename = "{}/infiles/dynamic_constraints_template".format(args.structure_name)
            constraints_filename = os.path.join(cur_dir, "constraints")
            param_filename = os.path.join(cur_dir, "param")
            state_filename = os.path.join(cur_dir, "state")

            launch_params = ["-P", os.path.join(args.pidmd_dir, "parameter"),
                             "-I", "{}/infiles/in.pdb".format(args.structure_name),
                             "-D", str(args.box),
                             "-p", param_filename,
                             "-s", state_filename
                             ]
            subprocess.run([complex_linux] +
                           launch_params +
                           ["-C", d_constraints_template_filename, "-c", tmp_constraints_filename],
                           stdout=subprocess.PIPE)
            subprocess.run([complex_linux] +
                           launch_params +
                           ["-C", s_constraints_template_filename, "-c", s_constraints_filename])
            process_constraints_template(tmp_constraints_filename,
                                         d_constraints_filename,
                                         args.min_dist,
                                         args.max_dist,
                                         force)
            d_lines = open(d_constraints_filename, "r").readlines()
            s_lines = open(s_constraints_filename, "r").readlines()
            with open(constraints_filename, "w") as f:
                f.writelines(d_lines + s_lines)

            base_dir = os.getcwd()
            os.chdir(cur_dir)
            subprocess.run(["qsub", "-b", "y", "-cwd",
                            "-N", "DMD_R_{}".format(args.structure_name),
                            "-q", args.queue,
                            dmd_exec,
                            "-i", os.path.join(base_dir, "inputs/relaxation.input"),
                            "-p", param_filename,
                            "-s", state_filename,
                            "-c", constraints_filename])
            os.chdir(base_dir)
