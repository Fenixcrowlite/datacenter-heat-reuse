"""Independent uncertainty envelope for D-synthetic pool heat metrology.

No real measurements or instrument calibration are claimed.
First-order propagation uses J Sigma J^T; the optional exact expression
assumes jointly Gaussian flow and temperature readings.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_measurement_v08\neistoty_merania_v08_sk.py")
RHO = 997.0
CP = 4182.0
POOL_M3 = 500.0
SAMPLE_S = 900.0


def covariance_matrix(u_flow: float, u_hot: float, u_cold: float,
                      corr_hot_cold: float = 0.0,
                      corr_flow_hot: float = 0.0,
                      corr_flow_cold: float = 0.0) -> list[list[float]]:
    values = (u_flow, u_hot, u_cold)
    correlations = (corr_hot_cold, corr_flow_hot, corr_flow_cold)
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("uncertainties must be finite and nonnegative")
    if any(not math.isfinite(r) or abs(r) > 1 for r in correlations):
        raise ValueError("correlations outside [-1,1]")
    a, b, c = values
    return [[a*a, a*b*corr_flow_hot, a*c*corr_flow_cold],
            [a*b*corr_flow_hot, b*b, b*c*corr_hot_cold],
            [a*c*corr_flow_cold, b*c*corr_hot_cold, c*c]]


def validate_covariance(matrix: list[list[float]]) -> None:
    if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
        raise ValueError("covariance must be 3x3")
    if any(not math.isfinite(x) for row in matrix for x in row):
        raise ValueError("nonfinite covariance")
    scale = max(1.0, *(abs(x) for row in matrix for x in row))
    tol = 1e-12 * scale
    if any(abs(matrix[i][j]-matrix[j][i]) > tol for i in range(3) for j in range(3)):
        raise ValueError("nonsymmetric covariance")
    if any(matrix[i][i] < -tol for i in range(3)):
        raise ValueError("negative diagonal")
    for i in range(3):
        for j in range(i+1, 3):
            if matrix[i][i]*matrix[j][j]-matrix[i][j]**2 < -tol*scale:
                raise ValueError("non-PSD 2x2 principal minor")
    a,b,c = matrix[0]
    d,e,f = matrix[1]
    g,h,i = matrix[2]
    determinant = a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    if determinant < -tol*scale*scale:
        raise ValueError("non-PSD determinant")


def heat_uncertainty(flow_m3h: float, hot_C: float, cold_C: float,
                     covariance: list[list[float]]) -> dict:
    validate_covariance(covariance)
    if not all(map(math.isfinite, (flow_m3h, hot_C, cold_C))):
        raise ValueError("nonfinite mean")
    if flow_m3h <= 0 or hot_C <= cold_C:
        raise ValueError("requires positive flow and temperature drop")
    dt = hot_C - cold_C
    k = RHO*CP/3600.0
    j = [k*dt, k*flow_m3h, -k*flow_m3h]
    first_var = sum(j[x]*covariance[x][y]*j[y] for x in range(3) for y in range(3))
    var_flow = covariance[0][0]
    var_delta = covariance[1][1]+covariance[2][2]-2*covariance[1][2]
    cov_flow_delta = covariance[0][1]-covariance[0][2]
    # For jointly Gaussian X,Y: Var(XY) = muX² varY + muY² varX
    # + 2 muX muY covXY + varX varY + covXY².
    exact_var = first_var+k*k*(var_flow*var_delta+cov_flow_delta**2)
    if first_var < -1e-7 or exact_var < -1e-7:
        raise ValueError("negative propagated variance")
    nominal = k*flow_m3h*dt
    return {
        "nominal_heat_W": nominal,
        "delta_T_K": dt,
        "u_delta_T_K": math.sqrt(max(0, var_delta)),
        "first_order_standard_uncertainty_W": math.sqrt(max(0, first_var)),
        "gaussian_exact_mean_W": nominal+k*cov_flow_delta,
        "gaussian_exact_standard_uncertainty_W": math.sqrt(max(0, exact_var)),
        "gaussian_product_correction_W": k*cov_flow_delta,
        "relative_first_order_standard_uncertainty": math.sqrt(max(0, first_var))/nominal,
        "covariance_F_deltaT_m3h_K": cov_flow_delta,
    }


def pool_storage_uncertainty(u_before_K: float, u_after_K: float,
                             temporal_correlation: float, pool_m3: float = POOL_M3,
                             sample_s: float = SAMPLE_S) -> dict:
    if not all(map(math.isfinite, (u_before_K, u_after_K, temporal_correlation, pool_m3, sample_s))):
        raise ValueError("nonfinite input")
    if u_before_K < 0 or u_after_K < 0 or abs(temporal_correlation) > 1:
        raise ValueError("invalid uncertainty or correlation")
    if pool_m3 <= 0 or sample_s <= 0:
        raise ValueError("nonpositive volume or sample time")
    var_delta = u_before_K**2+u_after_K**2-2*temporal_correlation*u_before_K*u_after_K
    sensitivity = RHO*CP*pool_m3/sample_s
    return {"u_temperature_difference_K": math.sqrt(max(0, var_delta)),
            "u_storage_power_W": sensitivity*math.sqrt(max(0, var_delta)),
            "temporal_correlation": temporal_correlation}


def repeated_flow_uncertainty(systematic_fraction: float, random_fraction: float,
                              sample_count: int) -> float:
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 1:
        raise ValueError("sample count must be positive integer")
    if any(not math.isfinite(x) or x < 0 for x in (systematic_fraction, random_fraction)):
        raise ValueError("invalid uncertainty")
    return math.hypot(systematic_fraction, random_fraction/math.sqrt(sample_count))


def build_evidence() -> dict:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    flow, hot, cold = 30.0, 30.0, 27.0
    cases = {}
    for name, correlation in (("independent", 0.0),
                              ("shared_temperature_bias_positive_0p9", 0.9),
                              ("anti_correlated_temperature_error_negative_0p9", -0.9)):
        cov = covariance_matrix(1.5, 0.2, 0.2, corr_hot_cold=correlation)
        cases[name] = {"temperature_correlation": correlation,
                       "covariance": cov,
                       **heat_uncertainty(flow, hot, cold, cov)}
    return {
        "status": "VERIFIED_ANALYTICAL_ASSUMED_CLASS_D_NOT_CALIBRATED",
        "source_class": "D_SYNTHETIC",
        "original_uncertainty_source_path": str(SOURCE),
        "original_uncertainty_source_sha256": source_hash,
        "assumptions": {"flow_m3h": flow, "hot_C": hot, "cold_C": cold,
                        "rho_kg_m3": RHO, "cp_J_kgK": CP,
                        "flow_standard_uncertainty_fraction": 0.05,
                        "each_thermometer_standard_uncertainty_K": 0.2,
                        "joint_gaussian_only_for_exact_product_formula": True},
        "heat_cases": cases,
        "pool_storage_cases": {
            "uncorrelated_15min": pool_storage_uncertainty(0.2, 0.2, 0.0),
            "highly_correlated_15min": pool_storage_uncertainty(0.2, 0.2, 0.95),
            "fixed_bias_plus_0p05K_random_each": pool_storage_uncertainty(0.05, 0.05, 0.0),
        },
        "averaging_flow_example": {
            "samples": 96, "systematic_fraction": 0.04, "random_fraction": 0.01,
            "effective_standard_uncertainty_fraction": repeated_flow_uncertainty(0.04, 0.01, 96)},
        "limits": [
            "No manufacturer flow meter/thermometer covariance or calibration certificates",
            "Correlations are illustrative, not estimated from observations",
            "Gaussian exact product model is conditional on jointly Gaussian errors",
            "Density, heat capacity, pool volume, heat losses and temporal dynamics are treated fixed",
            "No real-world heating feasibility or equipment safety is established",
        ],
        "next_step": "Obtain paired calibrated flow and supply/return temperature records; estimate covariance and autocorrelation, then validate against independent heat-meter holdout.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    p = Path(args.output)
    if p.exists():
        raise FileExistsError(p)
    evidence = build_evidence()
    p.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("CORRELATED_METROLOGY_PASS", p)


if __name__ == "__main__":
    main()
