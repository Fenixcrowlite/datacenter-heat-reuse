import unittest
import json
from pathlib import Path
from heat_reuse.matlab_subset import compile_functions,compile_model,UnsupportedMatlab,M


class MatlabSubsetTests(unittest.TestCase):
    def test_array_one_based_column_major_and_transpose(self):
        f=compile_functions('function y=f(x)\na=[1 2;3 4];a(2)=x;a(:,2)=[7;8];y=[a(:);sum(a(1,:))];\nend')['f']
        self.assertEqual([1.,9.,7.,8.,8.],f(9).flat())

    def test_branches_loops_local_functions_multiple_outputs(self):
        src='''function [y,z]=f(x)
y=zeros(1,3);z=0;
for k=1:3
 if k==2,y(k)=twice(x);elseif k==3,y(k)=x^2;else,y(k)=x;end
 z=z+y(k);
end
end
function y=twice(x)
y=2*x;
end'''
        y,z=compile_functions(src)['f'](3)
        self.assertEqual([3.,6.,9.],y.flat());self.assertEqual(18.,z)

    def test_anonymous_handle_boolean_and_elementwise(self):
        f=compile_functions('function y=f(x)\nP=@(v)[v v];a=P(x);assert(all(isfinite(a)));y=sum(a.^2);\nend')['f']
        self.assertEqual(18.,f(3))

    def test_unsupported_side_effect_fails_closed(self):
        f=compile_functions("function y=f(x)\ny=system('echo forbidden');\nend")['f']
        with self.assertRaises(UnsupportedMatlab):f(1)

    def test_ignored_outputs_struct_fields_and_bounded_while(self):
        src='''function y=f(x)
coder.extrinsic('external_reference');
cfg.value=x;
[a,~]=pair(cfg);y=0;
while y<a,y=y+1;end
end
function [a,b]=pair(cfg)
a=cfg.value;b=99;
end'''
        self.assertEqual(3,compile_functions(src)['f'](3))

    def test_nested_function_definition_does_not_end_parent(self):
        src='''function y=f(x)
a=twice(x);
function z=twice(v)
z=2*v;
end
y=a+1;
end'''
        self.assertEqual(7,compile_functions(src)['f'](3))

    def test_continue_skips_only_current_iteration(self):
        source='function y=f(x)\ny=0;for k=1:5,if k==x,continue;end;y=y+k;end\nend'
        self.assertEqual(12,compile_functions(source)['f'](3))

    def test_fix_truncates_toward_zero(self):
        fn=compile_functions('function y=f(x)\ny=fix(x);\nend')['f']
        self.assertEqual(-1,fn(-1.9));self.assertEqual(1,fn(1.9))

    def test_void_monitor_function_is_a_valid_statement(self):
        source='function y=f(x)\nmonitor(x);y=x+1;\nend\nfunction monitor(x)\nassert(x>0);\nend'
        self.assertEqual(3,compile_functions(source)['f'](2))

    def test_pure_function_cache_preserves_value_semantics_and_signed_zero(self):
        fn=compile_functions('function y=f(x)\ny=[x x+1];\nend')['f']
        result=fn(2.);result.data[0]=99
        self.assertEqual([2.,3.],fn(2.).flat())
        self.assertGreater(fn.cache_hits,0)
        bits=compile_functions("function y=f(x)\ny=typecast(x,'uint64');\nend")['f']
        self.assertEqual(0,bits(0.));self.assertEqual(1<<63,bits(-0.))

    def test_matrix_power_and_explicit_reduction_dimension(self):
        functions=compile_functions('''function y=square()
y=[1 2;3 4]^2;
end
function y=rowsum()
y=sum([1 2],1);
end
function y=colsum()
y=sum([1;2],2);
end''')
        self.assertEqual([7.,15.,10.,22.],functions['square']().flat())
        self.assertEqual([1.,2.],functions['rowsum']().flat())
        self.assertEqual([1.,2.],functions['colsum']().flat())

    def test_legacy_v22_links_external_numeric_matlab_components(self):
        root=Path(__file__).resolve().parents[1]
        model=json.loads(next((root/'models/extracted').glob('dchr-dispatch-stateflow-v22-*.json')).read_text(encoding='utf-8'))
        program=compile_model(model,source_root=root/'original/primary/matlab')
        x=M([8.,35.,70.,5.],4,1)
        p=M([1.,10.,3.,4.,.9,.8,.1,2.],8,1)
        h=M([12.,.45,2.2,7.,0.,0.,7.2,-.075,.00022],9,1)
        actual=program['hp_adapter'](x,5.,p,h).flat()
        cop=.45*343.15/35.;power=8./cop
        for a,b in zip(actual,[5.,8.,power,8.-power,8.,cop,1.,power]):self.assertAlmostEqual(a,b,places=12)


    def test_matlab_try_catch_preserves_error_identity(self):
        functions=compile_functions("""function value=guarded(x,step)
try
    validateattributes(x,{'double'},{'real','finite','scalar','positive'});
    if step~=1
        error('CHECK:Step','Step must be %.17g, got %.17g.',1,step);
    end
    value=x+1;
catch original
    if strcmp(original.identifier,'CHECK:Step'), rethrow(original); end
    failure=MException('CHECK:Domain','Invalid physical input: %s',original.message);
    failure=addCause(failure,original);
    throw(failure);
end
end""")
        self.assertEqual(functions['guarded'](2.,1.),3.)
        with self.assertRaisesRegex(ValueError,'CHECK:Step'):
            functions['guarded'](2.,0.)
        with self.assertRaisesRegex(ValueError,'CHECK:Domain') as captured:
            functions['guarded'](-2.,1.)
        self.assertEqual(captured.exception.identifier,'CHECK:Domain')
        self.assertIn('Nonpositive MATLAB input',captured.exception.causes[0]['message'])
        with self.assertRaisesRegex(UnsupportedMatlab,'Unsupported function system'):
            compile_functions('''function y=unsafe()
try
    y=system('echo unintended');
catch original
    y=0;
end
end''')['unsafe']()

    def test_legacy_v24_external_contract_checks_valid_and_wrong_dt(self):
        root=Path(__file__).resolve().parents[1]
        model=json.loads(next((root/'models/extracted').glob('dchr-dispatch-stateflow-v24-*.json')).read_text(encoding='utf-8'))
        program=compile_model(model,source_root=root/'original/primary/matlab')
        x=M([8.,35.,70.,5.],4,1)
        p=M([1.,10.,3.,4.,.9,.8,.1,2.],8,1)
        h=M([12.,.45,2.2,7.,0.,0.,7.2,-.075,.00022],9,1)
        u=program['hp_adapter'](x,5.,p,h,1.)
        self.assertEqual(len(u.flat()),8)
        self.assertEqual(u.flat()[0],5.)
        with self.assertRaisesRegex(ValueError,'DCHR:v24:IntegrationStep'):
            program['hp_adapter'](x,5.,p,h,.5)


    def test_legacy_v28_exponential_storage_contract(self):
        import math
        root=Path(__file__).resolve().parents[1]
        model=json.loads(next((root/'models/extracted').glob('dchr-dispatch-stateflow-v28-*.json')).read_text(encoding='utf-8'))
        program=compile_model(model,source_root=root/'original/primary/matlab')
        x=M([8.,35.,70.,5.],4,1)
        p=M([1.,10.,3.,4.,.9,.8,.1,2.],8,1)
        h=M([12.,.45,2.2,7.,0.,0.,7.2,-.075,.00022],9,1)
        u=program['hp_adapter'](x,5.,p,h,1.)
        mode=program['stateflow_choose_mode_v28'](u,5.,p)
        raw=program['stateflow_allocate_v28'](mode,u,5.,p)
        checked=program['stateflow_contract_gate_v28'](raw,u,5.,p,1.)
        tampered=M(raw.flat(),13,1)
        tampered.data[7]+=0.5
        with self.assertRaisesRegex(ValueError,'first-law|mismatch'):
            program['stateflow_contract_gate_v28'](tampered,u,5.,p,1.)
        self.assertEqual(len(checked.flat()),13)
        self.assertEqual(mode,2.)
        self.assertAlmostEqual(checked.flat()[6],5.*math.exp(-.1),places=12)
        with self.assertRaisesRegex(ValueError,'DCHR:v28:IntegrationStep'):
            program['hp_adapter'](x,5.,p,h,.5)


    def test_cell_braces_and_dynamic_struct_fields_are_value_safe(self):
        src="""function y=f(x)
keys={'alpha','beta'};
s=struct('alpha',x,'beta',3);
for j=1:numel(keys)
    s.(keys{j})=s.(keys{j})+1;
end
y=s.alpha+s.beta;
end"""
        f=compile_functions(src)['f']
        self.assertEqual(9.,f(4.))
        self.assertEqual(9.,f(4.))

    def test_dynamic_field_rejects_invalid_keys_and_out_of_range_cells(self):
        f=compile_functions("""function y=f(s,key)
y=s.(key);
end""")['f']
        self.assertEqual(3,f({'a':3},'a'))
        with self.assertRaisesRegex(UnsupportedMatlab,'Invalid dynamic struct field'):
            f({'a':3},42)
        with self.assertRaisesRegex(UnsupportedMatlab,'Unknown struct field'):
            f({'a':3},'missing')
        with self.assertRaisesRegex(UnsupportedMatlab,'requires a struct'):
            f(10,'a')
        g=compile_functions("""function y=g()
names={'a','b'};
y=names{3};
end""")['g']
        with self.assertRaisesRegex(ValueError,'out of bounds'):
            g()

    def test_v30_original_storage_parameters_fail_on_missing_named_field(self):
        root=Path(__file__).resolve().parents[1]
        path=root/'original/primary/matlab/+dchr/+components/storage_parameters_v30.m'
        fn=compile_functions(path.read_text(encoding='utf-8-sig'))['storage_parameters_v30']
        storage=dict(heat_capacity_MWh_per_K=2.,ambient_C=20.,delivery_cutoff_C=28.,
                     max_temperature_C=50.,initial_temperature_C=35.,charge_limit_MW=1.,
                     discharge_limit_MW=1.,eta_charge=.9,continuous_loss_rate_per_h=.1)
        with self.assertRaisesRegex(ValueError,'storage.eta_discharge'):
            fn({'sim':{'dt_h':1.},'storage':storage})



    def test_v30_original_storage_parameters_valid_numeric_vector(self):
        root=Path(__file__).resolve().parents[1]/'original/primary/matlab'
        src=(root/'+dchr/+components/storage_parameters_v30.m').read_text(encoding='utf-8-sig')
        program=compile_model(
            {'functions':[{'source':src,'names':['storage_parameters_v30']}]},
            source_root=root,
        )
        storage=dict(heat_capacity_MWh_per_K=2.,ambient_C=20.,delivery_cutoff_C=28.,
                     max_temperature_C=50.,initial_temperature_C=35.,charge_limit_MW=1.,
                     discharge_limit_MW=1.,eta_charge=.9,eta_discharge=.9,
                     continuous_loss_rate_per_h=.1)
        config={'sim':{'dt_h':1.},'storage':storage}
        self.assertEqual(
            [1.,60.,1.,1.,.9,.9,.1,16.,2.,20.],
            program['storage_parameters_v30'](config).flat(),
        )
        with self.assertRaisesRegex(ValueError,'DCHR:v30:StorageDomain'):
            program['storage_parameters_v30'](
                {'sim':{'dt_h':1.},'storage':{**storage,'eta_discharge':0.}},
            )



if __name__=='__main__':unittest.main()
