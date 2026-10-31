import math
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import correlated_pool_metrology as m


class CovarianceTests(unittest.TestCase):
    def setUp(self):
        self.base = m.covariance_matrix(1.5, 0.2, 0.2)

    def test_nominal_heat(self):
        self.assertAlmostEqual(m.heat_uncertainty(30, 30, 27, self.base)["nominal_heat_W"],
                               997*4182*30*3/3600)

    def test_independent_baseline(self):
        r = m.heat_uncertainty(30, 30, 27, self.base)
        expected = r["nominal_heat_W"]*math.hypot(0.05, math.sqrt(0.08)/3)
        self.assertAlmostEqual(r["first_order_standard_uncertainty_W"], expected)

    def test_positive_correlation_reduces_difference_uncertainty(self):
        low = m.heat_uncertainty(30, 30, 27, m.covariance_matrix(1.5,.2,.2,corr_hot_cold=.9))
        base = m.heat_uncertainty(30, 30, 27, self.base)
        self.assertLess(low["u_delta_T_K"], base["u_delta_T_K"])
        self.assertLess(low["first_order_standard_uncertainty_W"], base["first_order_standard_uncertainty_W"])

    def test_negative_correlation_increases_uncertainty(self):
        high = m.heat_uncertainty(30, 30, 27, m.covariance_matrix(1.5,.2,.2,corr_hot_cold=-.9))
        base = m.heat_uncertainty(30, 30, 27, self.base)
        self.assertGreater(high["first_order_standard_uncertainty_W"], base["first_order_standard_uncertainty_W"])

    def test_perfect_common_mode_cancels_delta(self):
        r = m.heat_uncertainty(30,30,27,m.covariance_matrix(0,.2,.2,corr_hot_cold=1))
        self.assertAlmostEqual(r["u_delta_T_K"],0)
        self.assertAlmostEqual(r["first_order_standard_uncertainty_W"],0)

    def test_gaussian_product_second_order_positive(self):
        r = m.heat_uncertainty(30,30,27,self.base)
        self.assertGreater(r["gaussian_exact_standard_uncertainty_W"],
                           r["first_order_standard_uncertainty_W"])
        self.assertAlmostEqual(r["gaussian_exact_mean_W"],r["nominal_heat_W"])

    def test_flow_temperature_covariance_changes_expected_mean(self):
        c=m.covariance_matrix(1.5,.2,.2,corr_flow_hot=.4)
        r=m.heat_uncertainty(30,30,27,c)
        self.assertGreater(r["gaussian_exact_mean_W"],r["nominal_heat_W"])
        self.assertGreater(r["covariance_F_deltaT_m3h_K"],0)

    def test_non_psd_three_way_correlations_rejected(self):
        c=m.covariance_matrix(1.5,.2,.2,corr_hot_cold=-.9,
                              corr_flow_hot=.9,corr_flow_cold=.9)
        with self.assertRaises(ValueError):
            m.heat_uncertainty(30,30,27,c)

    def test_nonsymmetric_covariance_rejected(self):
        c=m.covariance_matrix(1.5,.2,.2)
        c[1][0]=1
        with self.assertRaises(ValueError):
            m.validate_covariance(c)

    def test_nonfinite_covariance_rejected(self):
        c=m.covariance_matrix(1.5,.2,.2)
        c[1][1]=float("nan")
        with self.assertRaises(ValueError):
            m.validate_covariance(c)

    def test_out_of_range_correlation_rejected(self):
        with self.assertRaises(ValueError):
            m.covariance_matrix(1,.2,.2,corr_hot_cold=1.01)

    def test_negative_flow_rejected(self):
        with self.assertRaises(ValueError):
            m.heat_uncertainty(-1,30,27,self.base)

    def test_zero_delta_rejected(self):
        with self.assertRaises(ValueError):
            m.heat_uncertainty(30,27,27,self.base)

    def test_bad_shape_rejected(self):
        with self.assertRaises(ValueError):
            m.validate_covariance([[1,2],[2,1]])


class StorageTests(unittest.TestCase):
    def test_uncorrelated_matches_original(self):
        x=m.pool_storage_uncertainty(.2,.2,0)
        self.assertAlmostEqual(x["u_storage_power_W"],math.sqrt(2)*.2*997*4182*500/900)

    def test_fixed_bias_cancels_temporally(self):
        x=m.pool_storage_uncertainty(.2,.2,1)
        self.assertEqual(x["u_storage_power_W"],0)

    def test_temporal_correlation_reduces_difference(self):
        self.assertLess(m.pool_storage_uncertainty(.2,.2,.95)["u_storage_power_W"],
                        m.pool_storage_uncertainty(.2,.2,0)["u_storage_power_W"])

    def test_systematic_flow_does_not_average_away(self):
        x=m.repeated_flow_uncertainty(.04,.01,96)
        self.assertGreater(x,.04)
        self.assertLess(x,.041)

    def test_bad_sample_count(self):
        for n in (0,-1,True,1.5):
            with self.subTest(n=n), self.assertRaises(ValueError):
                m.repeated_flow_uncertainty(.04,.01,n)

    def test_evidence_tracks_real_original_source(self):
        d=m.build_evidence()
        self.assertEqual(d["source_class"],"D_SYNTHETIC")
        self.assertEqual(len(d["original_uncertainty_source_sha256"]),64)
        self.assertEqual(len(d["heat_cases"]),3)
        self.assertEqual(len(d["pool_storage_cases"]),3)


if __name__=="__main__":
    unittest.main()
