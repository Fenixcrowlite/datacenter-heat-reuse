"""Exact binary-operand constitutive loss bounds; no MATLAB eps or flow code."""
from fractions import Fraction as F
from earliest_closed_form_v73 import rows


def loss_checks(run):
    checks = []
    lam = F(run['p'][5])
    for k, r in enumerate(rows(run['trace'])):
        for j in range(int(r[12])):
            z = list(map(F, r[100+80*j:180+80*j]))
            loss = z[37:39]
            if lam == 0:
                ok = loss == [F(0), F(0)]
            else:
                lower = lam*z[6]*min(z[10], z[12])
                upper = lam*z[7]*max(z[11], z[13])
                ok = loss[0] <= upper and lower <= loss[1]
            checks.append(dict(name=f"{run['id']}_{k}_{j}_loss_constitutive", passed=ok))
    return checks
