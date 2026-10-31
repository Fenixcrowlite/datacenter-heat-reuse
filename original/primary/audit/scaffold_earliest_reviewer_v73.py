"""Create the v73 reviewer from the preserved independent closed-form lane."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    source=(ROOT/'audit/verify_earliest_dispatch_v71.py').read_text()
    start=source.index('def analyze(run):');end=source.index('\ndef main():',start)
    math=source[:end].replace('row[1]==71','row[1]==73')
    math=math.replace("check(pre+'_HP_limit',", "check(pre+'_source_capacity_certificate',contains(row[65:67],source*p[12]))\n        check(pre+'_source_limiter_certificate',contains(row[67:69],source*p[12]*(1+(floor+p[17]-Te)/a)))\n        check(pre+'_water_limiter_certificate',contains(row[69:71],p[15]*p[16]))\n        check(pre+'_selected_limiter',L<=dec(row[67]) and L<=dec(row[69]) and L<=p[10])\n        check(pre+'_HP_limit',")
    math=math.replace("check(pre+'_physical_clock',", "if row[61]==1:\n            check(pre+'_retained_age_certificate',contains(row[63:65],age-dec(row[62])))\n        check(pre+'_physical_clock',")
    math=math.replace("check(label+f'_energy_{j}',", "check(label+f'_nonnegative_energy_{j}',z[31+2*j]>=0 and value>=0)\n                check(label+f'_energy_{j}',")
    target=ROOT/'audit/earliest_closed_form_v73.py';assert not target.exists();target.write_text(math)

if __name__=='__main__':main()
