import argparse
from Bio.PDB import Chain, PDBIO, PDBParser
from copy import deepcopy
import logging
import numpy as np
import sys

EPS = 1e-3


def sample_perpendicular_vector(vector, max_angle):
    vector_length = np.linalg.norm(vector)
    vector_norm = vector / vector_length

    # Find an orthonormal basis for vectors orthogonal to n_vector
    x_basis = np.random.randn(3)
    x_basis -= x_basis.dot(vector_norm) * vector_norm
    x_basis /= np.linalg.norm(x_basis)
    y_basis = np.cross(vector_norm, x_basis)

    # For uniform sampling from a circle let's sample in polar coordinates
    r_sample, phi_sample = np.random.rand(2)
    r_sample *= vector_length * np.tan(max_angle / 180 * np.pi)
    phi_sample *= 2 * np.pi
    x_coefficient = r_sample * np.cos(phi_sample)
    y_coefficient = r_sample * np.sin(phi_sample)

    sampled_vector = x_coefficient * x_basis + y_coefficient * y_basis
    if np.abs(np.dot(vector, sampled_vector)) > EPS:
        logger = logging.getLogger()
        logger.error("Could not build a perpendicular vector.")
        return None

    return sampled_vector


def add_dummies_to_pdb(pdb_structure, chain_a_res_n, chain_b_res_n, target_len, max_angle):
    """
    Takes a PDB structure with two associated chains and one dummy chain
    Adds another dummy chain identical to the first one
    "Draws" a line from chain_a_res_n to chain_b_res_n (basis line)
    "Draws" a cone with _max_angle_ aperture and _target_len_ height
    Sample two vectors of from the cone
    Moves dummy residues so that their CA atoms locate on sampled positions
    :param pdb_structure: Bio.PDB.Structure.Structure
    :param chain_a_res_n: int, residue number on the first chain
    :param chain_b_res_n: int, residue number on the second chain
    :param target_len: distance from the CA atoms to dummy CA positions
    :param max_angle: aperture of the cone
    :return: side-effects
    """
    logger = logging.getLogger()
    if len([c for c in pdb_structure.get_chains()]) != 3:
        logger.error("Wrong PDB structures passed, expected exactly 3 chains.")
        sys.exit(1)

    chain_a, chain_b, chain_c = pdb_structure.get_chains()

    def get_ca_coord(chain_name, chain, res_n):
        chain_res_list = [r for r in chain.get_residues()]
        if len(chain_res_list) < res_n or res_n <= 0:
            logger.error("Wrong number of residue from chain {}: {}".format(chain_name, res_n))
            sys.exit(1)

        res = chain_res_list[res_n - 1]
        if "CA" not in res.child_dict:
            logger.error("No CA atom in the residue {} in chain {}.".format(res_n, chain_name))
            sys.exit(1)
        ca = res.child_dict["CA"]

        return ca.get_coord()

    chain_a_ca_coord = get_ca_coord("A", chain_a, chain_a_res_n)
    chain_b_ca_coord = get_ca_coord("B", chain_b, chain_b_res_n)
    diff_vector = chain_a_ca_coord - chain_b_ca_coord
    diff_vector_target_len = diff_vector * (target_len / np.linalg.norm(diff_vector))

    chain_a_dummy_basic = chain_a_ca_coord + diff_vector_target_len
    chain_b_dummy_basic = chain_b_ca_coord - diff_vector_target_len

    c_dummy_ca_coord = sample_perpendicular_vector(diff_vector_target_len, max_angle) + chain_a_dummy_basic
    d_dummy_ca_coord = sample_perpendicular_vector(diff_vector_target_len, max_angle) + chain_b_dummy_basic

    chain_d = Chain.Chain("D")
    if len(chain_c.child_list) != 1:
        logger.error("Wrong number of children in chain_c: {}".format(len(chain_c.child_list)))
        sys.exit(1)
    chain_c_child = chain_c.child_list[0]
    chain_d.add(deepcopy(chain_c_child))
    chain_d_child = chain_d.child_list[0]
    model = pdb_structure.child_dict[0]
    model.add(chain_d)
    chain_c.transform(np.eye(3), c_dummy_ca_coord - chain_c_child.child_dict["CA"].get_coord())
    chain_d.transform(np.eye(3), d_dummy_ca_coord - chain_d_child.child_dict["CA"].get_coord())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--pdb", type=str, required=True,
                        help="path to a PDB file with three chains: two interacting and one dummy")
    parser.add_argument("-o", "--out", type=str, required=True, help="path to the output structure")
    parser.add_argument("-f", "--c1_res", type=int, required=True, help="number of residue from the first chain")
    parser.add_argument("-s", "--c2_res", type=int, required=True, help="number of residue from the second chain")
    parser.add_argument("-d", "--distance", type=int, required=True, help="how far dummy residues to place")
    parser.add_argument("-a", "--max_angle", type=float, required=True,
                        help="maximum angle between basis line and sampled vector")
    args = parser.parse_args()

    pdb_parser = PDBParser()
    s = pdb_parser.get_structure(0, args.pdb)
    add_dummies_to_pdb(s, args.c1_res, args.c2_res, args.distance, args.max_angle)

    pdb_io = PDBIO()
    pdb_io.set_structure(s)
    pdb_io.save(args.out)
