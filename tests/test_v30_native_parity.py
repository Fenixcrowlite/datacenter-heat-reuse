"""Saved native MATLAB/Stateflow v30 acceptance and fault trace parity.

All execution is regenerated through the extracted MATLAB source interpreter.
The native trace and fault records are immutable comparison-only inputs.
No MATLAB license, Simulink model execution or archived Python outputs are used.
"""
import csv
import hashlib
import json
import math
import unittest
from pathlib import Path

from heat_reuse.matlab_subset import M, UnsupportedMatlab, compile_model


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "original" / "primary" / "matlab"
DATA = ROOT / "datasets" / "reference"

# Immutable hashes of saved MATLAB exports from original v30 acceptance.
FIXTURES = {
    "v30_native_trace.csv": "c0278a93a39458f9d21a709b070fdb38b5bea913e702b4bd5c38d1486f8eab1b",
    "v30_native_cases.json": "6010f0f6b575c4aab9af56395fc3228cbe5983d32268341dbc9be9f411858fe3",
    "v30_native_faults.json": "a33c250625bf9688459716652163ac065d1a984e94cd1c563c1c604defd1b6ea",
    "v30_native_fault_audit.json": "8bd624ce5c0525d3fa844a6028d4cf4c11a324755eb296ce72fdc314ad663c43",
}
SOURCES = {
    "dchr_stateflow_hp_v30": ("simulink", "62633b49633966a552d53cc97a8353cf8b16f78d30200e1456f5110b0b63d0a2"),
    "stateflow_choose_mode_v30": ("simulink", "28b7038f55e2d85c7385ee0e4bd916a1d8f6a5bba064d0323210c6fe3d0b0ea6"),
    "stateflow_allocate_v30": ("simulink", "467f7a034652c862568e55eaaf2c05bb1125d9cd89e7316e092cf9e3150a5157"),
    "stateflow_contract_gate_v30": ("simulink", "d4b0702ae6256b55180a0a37f913754d6ea3a3e0f6897af815159434717c5fb3"),
    "storage_kernel_v30": ("+dchr/+components", "8f56a70f5a2ddd7e84c2e458412a3e18edc786a4e9f80d060059f4064bb0a44d"),
}
MUTATIONS = {
    "y(15)=y(15)+1;": 14,
    "y(17)=y(17)+1;": 16,
    "y(8)=y(8)+1;": 7,
    "y(9)=y(9)+1;": 8,
}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SavedNativeV30ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name, expected in FIXTURES.items():
            actual = _sha(DATA / name)
            if actual != expected:
                raise AssertionError(f"Original MATLAB fixture hash mismatch: {name}: {actual}")
        source_specs = []
        for name, (directory, expected_sha) in SOURCES.items():
            path = SOURCE / directory / (name + ".m")
            if _sha(path) != expected_sha:
                raise AssertionError(f"Original MATLAB source changed: {path}")
            source_specs.append({"names": [name], "source": path.read_text(encoding="utf-8-sig")})
        cls.program = compile_model({"functions": source_specs}, source_root=SOURCE)
        cls.cases = json.loads((DATA / "v30_native_cases.json").read_text(encoding="utf-8"))["cases"]
        cls.faults = json.loads((DATA / "v30_native_faults.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((DATA / "v30_native_fault_audit.json").read_text(encoding="utf-8"))
        with (DATA / "v30_native_trace.csv").open(newline="", encoding="utf-8-sig") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.keys = list(cls.rows[0])
        if len(cls.keys) != 28:
            raise AssertionError("Unexpected native v30 trace layout")

    @classmethod
    def _step(cls, x, energy, p, h, mutation=None):
        cfg = M(p, 11, 1)
        u = cls.program["dchr_stateflow_hp_v30"](M(x, 5, 1), energy, cfg, M(h, 9, 1), p[0])
        mode = cls.program["stateflow_choose_mode_v30"](u, energy, cfg)
        raw = cls.program["stateflow_allocate_v30"](mode, u, energy, cfg)
        if mutation:
            if mutation not in MUTATIONS:
                raise AssertionError(f"Mutation not allowlisted: {mutation}")
            modified = M(raw.flat(), 17, 1)
            modified.data[MUTATIONS[mutation]] += 1.
            raw = modified
        checked = cls.program["stateflow_contract_gate_v30"](raw, u, energy, cfg, p[0])
        return checked.flat(), u.flat()

    def test_23_saved_scenarios_69_steps_1863_native_values(self):
        reference = {}
        for case in self.cases:
            for index in range(len(case["inputs"])):
                reference[(case["id"], index)] = None
        rows_by_key = {}
        for row in self.rows:
            case = next(c for c in self.cases if c["id"] == row["scenario_id"])
            key = (row["scenario_id"], round(float(row["Time_h"]) / case["p"][0]))
            self.assertIn(key, reference)
            self.assertNotIn(key, rows_by_key)
            rows_by_key[key] = row
        self.assertEqual(len(self.cases), 23)
        self.assertEqual(len(reference), len(rows_by_key))
        self.assertEqual(len(self.rows), 69)
        names_y = self.keys[2:19]
        names_u = self.keys[19:27]
        self.assertEqual(len(names_y), 17)
        self.assertEqual(len(names_u), 8)
        self.assertEqual(self.keys[27], "Storage_E_Start_MWh")
        compared, modes, differences = 0, set(), []
        for case in self.cases:
            energy = case["initial_energy_MWh"]
            p, h = case["p"], case["h"]
            for index, x in enumerate(case["inputs"]):
                y, u = self._step(x, energy, p, h)
                mode = int(y[0])
                modes.add(mode)
                row = rows_by_key[(case["id"], index)]
                comparisons = [("Time_h", index * p[0]), ("Storage_E_Start_MWh", energy)]
                comparisons.extend(zip(names_y, y))
                comparisons.extend(zip(names_u, u))
                for field, value in comparisons:
                    compared += 1
                    expected = float(row[field])
                    valid = (math.isnan(value) and math.isnan(expected)) or (
                        math.isfinite(value) and math.isfinite(expected)
                        and abs(value - expected) <= 2e-9 + 2e-11 * abs(expected)
                    )
                    if not valid:
                        differences.append((case["id"], index, field, value, expected))
                energy = y[7]
        self.assertEqual(compared, 69 * 27)
        self.assertEqual(modes, set(range(6)))
        self.assertEqual(differences, [], f"MATLAB v30 mismatches: {differences[:12]}")

    def test_18_saved_native_faults_rejected_at_same_interval(self):
        native = {fault["id"]: fault for fault in self.audit["faults"]}
        self.assertEqual(len(self.faults), 18)
        self.assertEqual(len(native), 18)
        observed = []
        for fault in self.faults:
            case = fault["configured_case"]
            energy, p, h = case["initial_energy_MWh"], case["p"], case["h"]
            completed, diagnostic = 0, None
            try:
                for x in case["inputs"]:
                    y, _ = self._step(x, energy, p, h, fault["mutation"].strip())
                    energy = y[7]
                    completed += 1
            except UnsupportedMatlab as exc:
                self.fail(f"Interpreter feature gap in fault {fault['id']}: {exc}")
            except (ValueError, ArithmeticError) as exc:
                diagnostic = str(exc)
            reference = native[fault["id"]]
            accepted = (diagnostic is not None
                and fault["expected_diagnostic"] in diagnostic
                and completed == fault["expected_prefix_samples"]
                and completed == fault["actual_prefix_samples"]
                and completed == reference["samples"]
                and reference["stop_event"] == "DiagnosticError"
                and reference["error_phase"] == "Execution"
                and math.isclose(reference["error_time_h"], completed * p[0], abs_tol=1e-12))
            if not accepted:
                observed.append((fault["id"], completed, diagnostic))
        self.assertEqual(observed, [], f"Native MATLAB fault replay mismatch: {observed}")


if __name__ == "__main__":
    unittest.main()
