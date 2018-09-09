from Bio.PDB import PDBParser
from copy import deepcopy
import numpy as np
from scipy import stats
import unittest

from pdb_get_pulling import add_dummies_to_pdb

TEST_REPETITIONS = 50


class TestPullingConf(unittest.TestCase):
    @staticmethod
    def get_angle(vector_1, vector_2):
        dot_product = np.dot(vector_1, vector_2)
        cosine = dot_product / np.linalg.norm(vector_1) / np.linalg.norm(vector_2)
        angle = np.arccos(cosine) / np.pi * 180
        return angle

    def test_1sq0(self):
        c1_res = np.random.randint(1, 198)
        c2_res = np.random.randint(1, 265)
        distance = np.random.randint(30, 200)
        max_angle = np.random.randint(5, 50)

        c_a_angles = np.zeros((TEST_REPETITIONS,))
        b_d_angles = np.zeros((TEST_REPETITIONS,))

        pdb_parser = PDBParser()
        s_ = pdb_parser.get_structure(0, "1sq0_test.pdb")
        for repetition in range(TEST_REPETITIONS):
            s = deepcopy(s_)
            residue_name = [c for c in s.get_chains()][2].child_list[0].resname
            add_dummies_to_pdb(s, c1_res, c2_res, distance, max_angle)
            chains = [c for c in s.get_chains()]
            self.assertEqual(len(chains), 4)
            chain_a, chain_b, chain_c, chain_d = chains
            self.assertEqual(chain_c.id, "C")
            self.assertEqual(len(chain_c.child_list), 1)
            self.assertEqual(chain_c.child_list[0].resname, residue_name)

            self.assertEqual(chain_d.id, "D")
            self.assertEqual(len(chain_d.child_list), 1)
            self.assertEqual(chain_d.child_list[0].resname, residue_name)

            a_ca_coord = chain_a.child_list[c1_res].child_dict["CA"].get_coord()
            b_ca_coord = chain_b.child_list[c2_res].child_dict["CA"].get_coord()
            c_ca_coord = chain_c.child_list[0].child_dict["CA"].get_coord()
            d_ca_coord = chain_d.child_list[0].child_dict["CA"].get_coord()

            basis_vector = a_ca_coord - b_ca_coord
            c_a_vector = c_ca_coord - a_ca_coord
            b_d_vector = b_ca_coord - d_ca_coord
            c_a_angle = self.get_angle(c_a_vector, basis_vector)
            b_d_angle = self.get_angle(b_d_vector, basis_vector)
            c_a_angles[repetition] = c_a_angle
            b_d_angles[repetition] = b_d_angle

        c_a_test = stats.kstest(c_a_angles, stats.uniform(loc=0.0, scale=max_angle).cdf)
        b_d_test = stats.kstest(b_d_angles, stats.uniform(loc=0.0, scale=max_angle).cdf)
        self.assertGreater(c_a_test[1], .05)
        self.assertGreater(b_d_test[1], .05)
