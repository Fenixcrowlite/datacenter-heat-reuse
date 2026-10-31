import unittest
from heat_reuse.matlab_subset import compile_functions,UnsupportedMatlab


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


if __name__=='__main__':unittest.main()
