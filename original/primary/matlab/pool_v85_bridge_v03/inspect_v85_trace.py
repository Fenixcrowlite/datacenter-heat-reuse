import json,pathlib,math
p=pathlib.Path(r'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\horizon_sensitivity_v86_20261013T112610_976653Z\report.json')
j=json.loads(p.read_text(encoding="utf-8"))
print("run count",len(j["runs"]))
for r in j['runs']:
    if r['id'] in ('zero_demand','binding_stop','service_E3.0_a1.0_H2_dt0.25','charge_E4.95_a1.0_H2_dt0.25','charge_E8.5_a1.0_H2_dt0.25'):
        print('CASE',r['id'],'SCHEDULE',r['adapter']['schedule'],'INITIAL',r['adapter']['initial'])
        print('POLICY',r['p'])
        print('HP',r['summary'].get('hp_heat_MWh_hull'),'RECOVERED',r['summary'].get('recovered_source_MWh_hull'))
        print('SERVICE',r['summary'].get('delivered_service_MWh_hull'),'DEMAND',r['summary'].get('demand_MWh_hull'))
        trace=r['trace']
        if trace and isinstance(trace[0],(int,float)):trace=[trace]
        for k,row in enumerate(trace):
            print('interval',k,'mode',row[0],'numsegments',row[12],'timehull',row[9:11], 'energyhull',row[30:36])
            for m in range(int(row[12])):
                s=row[100+80*m:100+80*(m+1)]
                print(' segment',m, 'S1:15',s[:15], 'S20:45',s[19:45], 'S50:65',s[49:65])
        print('--')
