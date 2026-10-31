"""Python numerical evaluator for the finite MATLAB subset in bundled kernels.

Not a MATLAB installation, arbitrary Simulink runner, or shell interpreter.
Only arithmetic, array indexing, pure functions, branches and bounded loops
are admitted. Unknown operations fail closed. Per-model execution requires
separate fixture validation; successfully parsing code is not a parity claim.
"""
from __future__ import annotations
import copy
import math
import operator
import re
import struct
import sys
from pathlib import Path


class UnsupportedMatlab(ValueError):pass


class MatlabError(ValueError):
    """A recoverable MATLAB runtime error with identifier and cause provenance."""
    def __init__(self,identifier,message,causes=()):
        self.identifier=str(identifier)
        self.message=str(message)
        self.causes=tuple(causes)
        super().__init__(f'{self.identifier}: {self.message}' if self.identifier else self.message)


def _error_record(exc):
    if isinstance(exc,MatlabError):
        return {'identifier':exc.identifier,'message':exc.message,'causes':list(exc.causes)}
    return {'identifier':'MATLAB:runtime','message':str(exc),'causes':[]}


def _error_message(template,parts):
    if not isinstance(template,str):raise UnsupportedMatlab('MATLAB error template must be a string')
    if not parts:return template
    try:return template % tuple(parts)
    except (TypeError,ValueError) as exc:
        raise UnsupportedMatlab('Unsupported MATLAB message format') from exc




class M:
    """A small column-major matrix with explicit MATLAB value semantics."""
    def __init__(self,values,rows=1,cols=None):
        self.data=list(values);self.rows=rows;self.cols=len(self.data)//rows if cols is None else cols
        if self.rows*self.cols!=len(self.data):raise ValueError('Matrix size mismatch')
    def flat(self):return list(self.data)
    def clone(self):return M(self.data,self.rows,self.cols)
    def transpose(self):return M([self.data[r+c*self.rows] for r in range(self.rows) for c in range(self.cols)],self.cols,self.rows)
    def __repr__(self):return f'M({self.data!r}, {self.rows}, {self.cols})'


COLON=object()
def flat(value):return value.data if isinstance(value,M) else [value]
def truth(value):return bool(flat(value)) and all(bool(v) for v in flat(value))
def scalar(value):
    if isinstance(value,M):
        if len(value.data)!=1:raise ValueError('Expected scalar')
        return value.data[0]
    return value
def integer(value):
    value=scalar(value)
    if not math.isfinite(value) or int(value)!=value:raise ValueError('Integer required')
    return int(value)
def unary(fn,value):return M([fn(v) for v in value.data],value.rows,value.cols) if isinstance(value,M) else fn(value)
def elementwise(fn,a,b):
    if not isinstance(a,M) and not isinstance(b,M):return fn(a,b)
    aa,bb=flat(a),flat(b)
    template=a if isinstance(a,M) and len(aa)>1 else b if isinstance(b,M) else a
    count=max(len(aa),len(bb))
    if len(aa) not in (1,count) or len(bb) not in (1,count):raise ValueError('Array sizes must agree')
    return M([fn(aa[i if len(aa)>1 else 0],bb[i if len(bb)>1 else 0]) for i in range(count)],template.rows,template.cols)
def binary(op,a,b):
    if op=='^' and isinstance(a,M) and len(a.data)>1:
        if a.rows!=a.cols:raise ValueError('Matrix power requires a square matrix')
        exponent=integer(b)
        n=a.rows
        result=M([float(r==c) for c in range(n) for r in range(n)],n,n)
        base=a.clone()
        if exponent<0:
            augmented=[[a.data[r+c*n] for c in range(n)]+[float(r==c) for c in range(n)] for r in range(n)]
            for k in range(n):
                pivot=max(range(k,n),key=lambda r:abs(augmented[r][k]))
                if augmented[pivot][k]==0:raise ValueError('Singular matrix')
                augmented[k],augmented[pivot]=augmented[pivot],augmented[k]
                scale=augmented[k][k];augmented[k]=[v/scale for v in augmented[k]]
                for r in range(n):
                    if r!=k:
                        factor=augmented[r][k];augmented[r]=[x-factor*y for x,y in zip(augmented[r],augmented[k])]
            base=M([augmented[r][n+c] for c in range(n) for r in range(n)],n,n);exponent=-exponent
        while exponent:
            if exponent&1:result=binary('*',result,base)
            exponent>>=1
            if exponent:base=binary('*',base,base)
        return result
    if op=='*' and isinstance(a,M) and isinstance(b,M) and len(a.data)>1 and len(b.data)>1:
        if a.cols!=b.rows:raise ValueError('Matrix multiplication dimensions disagree')
        values=[sum(a.data[r+k*a.rows]*b.data[k+c*b.rows] for k in range(a.cols)) for c in range(b.cols) for r in range(a.rows)]
        return M(values,a.rows,b.cols)
    functions={'+':operator.add,'-':operator.sub,'*':operator.mul,'.*':operator.mul,'/':operator.truediv,
               './':operator.truediv,'^':operator.pow,'.^':operator.pow,'==':operator.eq,'~=':operator.ne,
               '>':operator.gt,'<':operator.lt,'>=':operator.ge,'<=':operator.le,'&':lambda x,y:bool(x) and bool(y),'|':lambda x,y:bool(x) or bool(y)}
    if op not in functions:raise UnsupportedMatlab('Unsupported operator '+op)
    return elementwise(functions[op],a,b)
def concatenate(rows):
    material=[]
    for pieces in rows:
        pieces=[p if isinstance(p,M) else M([p]) for p in pieces]
        if not pieces:continue
        height=pieces[0].rows
        if any(p.rows!=height for p in pieces):raise ValueError('Horizontal concatenation dimensions disagree')
        material.append(M([v for p in pieces for v in p.data],height,sum(p.cols for p in pieces)))
    if not material:return M([],0,0)
    width=material[0].cols
    if any(p.cols!=width for p in material):raise ValueError('Vertical concatenation dimensions disagree')
    return M([v for c in range(width) for p in material for v in p.data[c*p.rows:(c+1)*p.rows]],sum(p.rows for p in material),width)
def indices(value,size):
    if value is COLON:return list(range(size))
    values=flat(value)
    if values and all(isinstance(v,bool) for v in values):
        if len(values)!=size:raise ValueError('Logical index size mismatch')
        return [i for i,v in enumerate(values) if v]
    out=[integer(v)-1 for v in values]
    if any(v<0 or v>=size for v in out):raise ValueError('MATLAB index out of bounds')
    return out
def get(matrix,args):
    if not isinstance(matrix,M):matrix=M([matrix])
    if len(args)==1:
        ix=indices(args[0],len(matrix.data));values=[matrix.data[i] for i in ix]
        if not isinstance(args[0],M) and args[0] is not COLON:return values[0]
        if args[0] is COLON:return M(values,len(values),1)
        if matrix.rows==1:return M(values,1,len(values))
        if matrix.cols==1:return M(values,len(values),1)
        return M(values,args[0].rows,args[0].cols)
    if len(args)!=2:raise UnsupportedMatlab('Only two-dimensional arrays supported')
    rr,cc=indices(args[0],matrix.rows),indices(args[1],matrix.cols)
    data=[matrix.data[r+c*matrix.rows] for c in cc for r in rr]
    return data[0] if len(data)==1 else M(data,len(rr),len(cc))
def put(matrix,args,value):
    if not isinstance(matrix,M):matrix=M([matrix])
    if len(args)==1:ix=indices(args[0],len(matrix.data))
    elif len(args)==2:ix=[r+c*matrix.rows for c in indices(args[1],matrix.cols) for r in indices(args[0],matrix.rows)]
    else:raise UnsupportedMatlab('Only two-dimensional arrays supported')
    values=flat(value)
    if len(values) not in (1,len(ix)):raise ValueError('Assignment size mismatch')
    for i,j in enumerate(ix):matrix.data[j]=values[0 if len(values)==1 else i]
    return matrix


TOKEN=re.compile(r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*|&&|\|\||~=|<=|>=|==|\.\*|\./|\.\^|\.\x27|[+\-*/^<>=~&|:()\[\]{},;@.\x27]')
def tokenize(source):
    tokens=[];i=0;previous=''
    while i<len(source):
        c=source[i]
        if c in ' \t\r':i+=1;continue
        if source.startswith('...',i):
            end=source.find('\n',i);i=len(source) if end<0 else end+1;continue
        if c=='%':
            end=source.find('\n',i);i=len(source) if end<0 else end;continue
        if c=='\n':tokens.append(('sep','\n',i,i+1));previous='sep';i+=1;continue
        if c in "'\"" and not (c=="'" and (previous in (')',']',"'") or previous=='operand')):
            start=i;quote=c;i+=1;value=''
            while i<len(source):
                if source[i]==quote:
                    if i+1<len(source) and source[i+1]==quote:value+=quote;i+=2;continue
                    i+=1;break
                value+=source[i];i+=1
            else:raise UnsupportedMatlab('Unclosed string')
            tokens.append(('string',value,start,i));previous='operand';continue
        match=TOKEN.match(source,i)
        if not match:raise UnsupportedMatlab('Unsupported token near '+source[i:i+40])
        text=match.group();kind='number' if text[0].isdigit() or (text.startswith('.') and len(text)>1 and text[1].isdigit()) else 'name' if re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',text) else text
        tokens.append((kind,text,i,match.end()));previous='operand' if kind in ('number','name') else text;i=match.end()
    tokens.append(('eof','',len(source),len(source)));return tokens


PRECEDENCE={'||':1,'&&':2,'|':3,'&':4,'==':5,'~=':5,'>':5,'<':5,'>=':5,'<=':5,':':6,'+':7,'-':7,'*':8,'/':8,'.*':8,'./':8,'^':10,'.^':10}
class Parser:
    def __init__(self,source):self.tokens=tokenize(source);self.pos=0
    def token(self):return self.tokens[self.pos]
    def is_(self,text):return self.token()[1]==text or self.token()[0]==text
    def take(self,text=None):
        token=self.token()
        if text is not None and not self.is_(text):raise UnsupportedMatlab('Expected '+text+', found '+repr(token[1]))
        self.pos+=1;return token
    def separators(self):
        while self.is_('sep') or self.is_(';') or self.is_(','):self.take()
    def expression(self,minimum=0,matrix=False):
        token=self.take();kind,text=token[:2]
        if kind=='number':left=('constant',float(text))
        elif kind=='string':left=('constant',text)
        elif kind=='name':left=('name',text)
        elif text==':':left=('constant',COLON)
        elif text=='~' and self.token()[1] in (']',',',';'):left=('discard',)
        elif text in ('+','-','~'):left=('unary',text,self.expression(9))
        elif text=='(':
            left=self.expression();self.take(')')
        elif text in ('[','{'):
            closing=']' if text=='[' else '}'
            rows=[[]]
            while not self.is_(closing):
                if self.is_(';') or self.is_('sep'):self.take();rows.append([]);continue
                if self.is_(','):self.take();continue
                rows[-1].append(self.expression(matrix=True))
            self.take(closing);left=('matrix' if text=='[' else 'cell',rows)
        elif text=='@':
            self.take('(');params=[]
            while not self.is_(')'):
                params.append(self.take()[1])
                if self.is_(','):self.take()
            self.take(')');left=('lambda',params,self.expression())
        else:raise UnsupportedMatlab('Unexpected expression '+repr(text))
        while True:
            token=self.token();op=token[1]
            if op=='(':
                self.take();args=[]
                while not self.is_(')'):
                    args.append(self.expression())
                    if self.is_(','):self.take()
                    else:break
                self.take(')');left=('call',left,args);continue
            if op=='{':
                self.take();args=[]
                while not self.is_('}'):
                    args.append(self.expression())
                    if self.is_(','):self.take()
                    else:break
                self.take('}');left=('cell_index',left,args);continue
            if op=='.':
                self.take();self.take('(')
                field=self.expression();self.take(')')
                left=('dynamic_field',left,field);continue
            if op in ("'",".'"):
                self.take();left=('transpose',left);continue
            if op not in PRECEDENCE or PRECEDENCE[op]<minimum:break
            if matrix and op in ('+','-') and self.tokens[self.pos-1][3]<token[2] and token[3]==self.tokens[self.pos+1][2]:break
            self.take();right=self.expression(PRECEDENCE[op]+(0 if op in ('^','.^') else 1),matrix=matrix)
            left=('binary',op,left,right)
        return left
    def statements(self,stops):
        body=[];self.separators()
        while not any(self.is_(s) for s in stops) and not self.is_('eof'):
            if self.is_('function'):
                body.append(('define',self.function()))
            elif self.is_('if'):
                self.take();branches=[];condition=self.expression();self.separators()
                branches.append((condition,self.statements({'elseif','else','end'})))
                while self.is_('elseif'):
                    self.take();condition=self.expression();self.separators();branches.append((condition,self.statements({'elseif','else','end'})))
                fallback=[]
                if self.is_('else'):self.take();self.separators();fallback=self.statements({'end'})
                self.take('end');body.append(('if',branches,fallback))
            elif self.is_('while'):
                self.take();condition=self.expression();self.separators()
                statements=self.statements({'end'});self.take('end');body.append(('while',condition,statements))
            elif self.is_('try'):
                self.take();self.separators()
                protected=self.statements({'catch','end'})
                caught=None;handler=None
                if self.is_('catch'):
                    self.take()
                    if self.token()[0]=='name':caught=self.take('name')[1]
                    self.separators()
                    handler=self.statements({'end'})
                self.take('end');body.append(('try',protected,caught,handler))
            elif self.is_('for'):
                self.take();name=self.take('name')[1];self.take('=');values=self.expression();self.separators()
                statements=self.statements({'end'});self.take('end');body.append(('for',name,values,statements))
            elif self.is_('return') or self.is_('break') or self.is_('continue'):body.append((self.take()[1],))
            else:
                left=self.expression()
                if self.is_('='):self.take();body.append(('assign',left,self.expression()))
                else:body.append(('expression',left))
            self.separators()
        return body
    def function(self):
        self.take('function');outputs=[]
        if self.is_('['):
            self.take()
            while not self.is_(']'):
                outputs.append(self.take('name')[1])
                if self.is_(','):self.take()
            self.take(']');self.take('=');name=self.take('name')[1]
        else:
            name=self.take('name')[1]
            if self.is_('='):outputs=[name];self.take();name=self.take('name')[1]
        params=[]
        if self.is_('('):
            self.take()
            while not self.is_(')'):
                params.append(self.take('name')[1])
                if self.is_(','):self.take()
            self.take(')')
        self.separators();body=self.statements({'end'})
        if self.is_('end'):self.take()
        return name,params,outputs,body
    def functions(self):
        functions=[];self.separators()
        while not self.is_('eof'):
            functions.append(self.function());self.separators()
        return functions


def reduce_matrix(fn,value,dimension=None):
    if not isinstance(value,M):return fn([value])
    if dimension=='all':return fn(value.data)
    axis=(1 if value.rows!=1 else 2) if dimension is None else integer(dimension)
    if axis==1:
        values=[fn(value.data[c*value.rows:(c+1)*value.rows]) for c in range(value.cols)]
        return values[0] if len(values)==1 else M(values)
    if axis==2:
        values=[fn([value.data[r+c*value.rows] for c in range(value.cols)]) for r in range(value.rows)]
        return values[0] if len(values)==1 else M(values,value.rows,1)
    raise UnsupportedMatlab('Unsupported reduction dimension')
def builtin(name,args):
    if name=='coder.extrinsic':
        if not all(isinstance(a,str) for a in args):raise UnsupportedMatlab('Invalid extrinsic declaration')
        return None
    if name=='struct':
        if len(args)%2:raise ValueError('Invalid struct fields')
        return {args[i]:args[i+1] for i in range(0,len(args),2)}
    if name=='MException':
        if len(args)<2 or not isinstance(args[0],str):
            raise UnsupportedMatlab('MException requires identifier and message')
        return {'identifier':args[0],'message':_error_message(args[1],args[2:]),'causes':[]}
    if name=='addCause':
        if len(args)!=2 or not isinstance(args[0],dict) or not isinstance(args[1],dict):
            raise UnsupportedMatlab('addCause requires two MATLAB exception records')
        value=copy.deepcopy(args[0]);value['causes'].append(copy.deepcopy(args[1]))
        return value
    if name in ('throw','rethrow'):
        if len(args)!=1 or not isinstance(args[0],dict):
            raise UnsupportedMatlab(name+' requires a MATLAB exception record')
        error=args[0]
        if not isinstance(error.get('identifier'),str) or not isinstance(error.get('message'),str):
            raise UnsupportedMatlab('Malformed MATLAB exception record')
        raise MatlabError(error['identifier'],error['message'],error.get('causes',()))
    if name=='isreal':return all(not isinstance(v,complex) for v in flat(args[0]))
    if name=='isnumeric':return all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in flat(args[0]))
    if name=='isstruct':return isinstance(args[0],dict)
    if name=='isfield':
        if len(args)!=2:raise UnsupportedMatlab('isfield requires a struct and a field name')
        names=args[1]
        if isinstance(names,M):
            return M([isinstance(args[0],dict) and isinstance(n,str) and n in args[0]
                      for n in names.data],names.rows,names.cols)
        if isinstance(names,list):
            return [isinstance(args[0],dict) and isinstance(n,str) and n in args[0]
                    for n in names]
        if not isinstance(names,str):raise UnsupportedMatlab('isfield field must be a string')
        return isinstance(args[0],dict) and names in args[0]
    if name=='isscalar':return len(flat(args[0]))==1
    if name=='ismissing':return unary(lambda x:x is None or isinstance(x,float) and math.isnan(x),args[0])
    if name=='string':return unary(str,args[0])
    if name=='strcmp':return elementwise(operator.eq,*args)
    if name=='strcmpi':return elementwise(lambda a,b:str(a).casefold()==str(b).casefold(),*args)
    if name=='validateattributes':
        value,classes,attributes=args[:3];values=flat(value)
        for i,attr in enumerate(attributes):
            if attr=='finite' and not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite MATLAB input')
            if attr=='real' and not all(not isinstance(v,complex) for v in values):raise ValueError('Complex MATLAB input')
            if attr=='numel' and len(values)!=attributes[i+1]:raise ValueError('MATLAB input size mismatch')
            if attr=='scalar' and len(values)!=1:raise ValueError('MATLAB input must be scalar')
            if attr=='vector' and isinstance(value,M) and min(value.rows,value.cols)!=1:
                raise ValueError('MATLAB input must be vector')
            if attr=='positive' and not all(v>0 for v in values):raise ValueError('Nonpositive MATLAB input')
            if attr=='nonnegative' and not all(v>=0 for v in values):raise ValueError('Negative MATLAB input')
        return None
    math_functions={'abs':abs,'exp':math.exp,'expm1':math.expm1,'log':math.log,'log1p':math.log1p,'sqrt':math.sqrt,
                    'sin':math.sin,'cos':math.cos,'floor':math.floor,'ceil':math.ceil,'fix':math.trunc,'sign':lambda x:(x>0)-(x<0),
                    'isfinite':math.isfinite,'isnan':math.isnan,'isinf':math.isinf,'double':float,'logical':bool,
                    'uint64':lambda x:int(x)%(1<<64),'uint32':lambda x:int(x)%(1<<32),'int32':int,'eps':math.ulp}
    if name in math_functions:return unary(math_functions[name],args[0] if args else 1.)
    if name in ('min','max'):
        fn=min if name=='min' else max
        if len(args)==1:return reduce_matrix(fn,args[0])
        if len(args)>=3 and isinstance(args[1],M) and not args[1].data:return reduce_matrix(fn,args[0],args[2])
        return elementwise(fn,args[0],args[1])
    if name in ('sum','all','any','prod'):
        fn={'sum':sum,'all':all,'any':any,'prod':math.prod}[name]
        return reduce_matrix(fn,args[0],args[1] if len(args)>1 else None)
    if name in ('zeros','ones'):
        dims=[integer(x) for x in (flat(args[0]) if len(args)==1 and isinstance(args[0],M) else args)]
        if len(dims)==1:dims*=2
        if len(dims)!=2 or min(dims)<0 or math.prod(dims)>2000000:raise ValueError('Invalid matrix allocation')
        return M([0. if name=='zeros' else 1.]*math.prod(dims),*dims)
    if name=='numel':return len(args[0]) if isinstance(args[0],list) else len(flat(args[0]))
    if name=='length':return max(args[0].rows,args[0].cols) if isinstance(args[0],M) else len(args[0]) if isinstance(args[0],list) else 1
    if name=='size':
        dims=[args[0].rows,args[0].cols] if isinstance(args[0],M) else [1,1]
        return dims[integer(args[1])-1] if len(args)>1 else M(dims)
    if name=='isempty':return not args[0] if isinstance(args[0],list) else not flat(args[0])
    if name=='ismember':return unary(lambda x:x in flat(args[1]),args[0])
    if name=='mod':return elementwise(operator.mod,*args)
    if name in ('bitand','bitor','bitxor','bitshift'):
        fn={'bitand':lambda a,b:int(a)&int(b),'bitor':lambda a,b:int(a)|int(b),'bitxor':lambda a,b:int(a)^int(b),
            'bitshift':lambda a,b:(int(a)<<int(b))%(1<<64) if b>=0 else int(a)>>-int(b)}[name]
        return elementwise(fn,*args)
    if name=='typecast':
        dtype=args[1];fmt={'double':'d','uint64':'Q','int64':'q'}.get(dtype)
        if fmt is None:raise UnsupportedMatlab('Unsupported typecast')
        return unary(lambda x:struct.unpack('<'+fmt,struct.pack('<d' if isinstance(x,float) else '<Q',x))[0],args[0])
    if name=='assert':
        if not truth(args[0]):raise ValueError(str(args[1]) if len(args)>1 else 'MATLAB assertion failed')
        return None
    if name=='error':
        if len(args)>=2 and isinstance(args[0],str) and ':' in args[0]:
            raise MatlabError(args[0],_error_message(args[1],args[2:]))
        raise MatlabError('MATLAB:runtime',_error_message(str(args[0]),args[1:]) if args else 'Error')
    if name in ('realmax','realmin'):return sys.float_info.max if name=='realmax' else sys.float_info.min
    raise UnsupportedMatlab('Unsupported function '+name)


class _Return(Exception):pass
class _Break(Exception):pass
class _Continue(Exception):pass


def _cache_key(value):
    if isinstance(value,M):
        if len(value.data)>64:raise TypeError()
        return ('M',value.rows,value.cols,tuple(_cache_key(v) for v in value.data))
    if isinstance(value,float):return ('float',struct.pack('>d',value))
    if isinstance(value,(int,bool,str,type(None))):return (type(value).__name__,value)
    raise TypeError()


def _value_copy(value):
    if isinstance(value,M):return value.clone()
    if isinstance(value,tuple):return tuple(_value_copy(v) for v in value)
    return copy.deepcopy(value)


def _dynamic_field_name(value):
    # MATLAB dynamic field names must be scalar identifiers, never Python attributes.
    if not isinstance(value,str) or re.fullmatch(r'[A-Za-z]\w*',value) is None:
        raise UnsupportedMatlab('Invalid dynamic struct field name')
    return value


class Function:
    def __init__(self,name,params,outputs,body,functions,capture=None):
        self.name=name;self.params=params;self.outputs=outputs;self.body=body;self.functions=functions;self.capture=capture
        self.cache={};self.cache_hits=0
    def __call__(self,*args):
        if len(args)>len(self.params):raise ValueError(f'{self.name}: expected at most {len(self.params)} arguments, got {len(args)}')
        key=None
        if self.capture is None:
            try:key=tuple(_cache_key(v) for v in args)
            except TypeError:pass
        if key is not None and key in self.cache:
            self.cache_hits+=1
            return _value_copy(self.cache[key])
        env=dict(self.capture or {})
        env.update({k:v.clone() if isinstance(v,M) else copy.deepcopy(v) for k,v in zip(self.params,args)})
        env['nargin']=len(args)
        try:self.execute(self.body,env)
        except _Return:pass
        result=tuple(env[k] for k in self.outputs)
        result=result[0] if len(result)==1 else result
        if key is not None:
            if len(self.cache)>=2048:self.cache.clear()
            self.cache[key]=_value_copy(result)
        return result
    def eval(self,node,env,multi=False):
        kind=node[0]
        if kind=='constant':return node[1]
        if kind=='name':
            if node[1] in env:return env[node[1]]
            if '.' in node[1]:
                pieces=node[1].split('.');value=env.get(pieces[0])
                for piece in pieces[1:]:
                    if not isinstance(value,dict) or piece not in value:raise UnsupportedMatlab('Unknown struct field '+node[1])
                    value=value[piece]
                return value
            constants={'true':True,'false':False,'pi':math.pi,'Inf':math.inf,'inf':math.inf,'NaN':math.nan,'nan':math.nan,'eps':sys.float_info.epsilon,'realmax':sys.float_info.max,'realmin':sys.float_info.min}
            if node[1] in constants:return constants[node[1]]
            raise UnsupportedMatlab('Unknown symbol '+node[1])
        if kind=='matrix':return concatenate([[self.eval(p,env) for p in row] for row in node[1]])
        if kind=='cell':return [self.eval(p,env) for row in node[1] for p in row]
        if kind=='cell_index':
            values=self.eval(node[1],env)
            if not isinstance(values,list) or len(node[2])!=1:
                raise UnsupportedMatlab('Only single-element cell brace indexing supported')
            selected=indices(self.eval(node[2][0],env|{'end':len(values)}),len(values))
            if len(selected)!=1:raise UnsupportedMatlab('Cell brace indexing must select one element')
            return _value_copy(values[selected[0]])
        if kind=='dynamic_field':
            value=self.eval(node[1],env)
            field=_dynamic_field_name(self.eval(node[2],env))
            if not isinstance(value,dict):raise UnsupportedMatlab('Dynamic field access requires a struct')
            if field not in value:raise UnsupportedMatlab('Unknown struct field '+field)
            return value[field]
        if kind=='transpose':
            value=self.eval(node[1],env);return value.transpose() if isinstance(value,M) else value
        if kind=='unary':return unary({'+':operator.pos,'-':operator.neg,'~':operator.not_}[node[1]],self.eval(node[2],env))
        if kind=='lambda':
            captured={k:v.clone() if isinstance(v,M) else v for k,v in env.items()}
            return lambda *args:self.eval(node[2],captured|dict(zip(node[1],args)))
        if kind=='binary':
            op=node[1];a=self.eval(node[2],env)
            if op=='&&':return truth(a) and truth(self.eval(node[3],env))
            if op=='||':return truth(a) or truth(self.eval(node[3],env))
            if op==':':
                if node[2][0]=='binary' and node[2][1]==':':
                    start=self.eval(node[2][2],env);step=self.eval(node[2][3],env)
                else:start=a;step=1.
                stop=self.eval(node[3],env)
                if step==0:raise ValueError('Zero range increment')
                count=max(0,int(math.floor((stop-start)/step+1e-12))+1)
                if count>2000000:raise ValueError('Excessive range')
                return M([start+i*step for i in range(count)])
            return binary(op,a,self.eval(node[3],env))
        if kind=='call':
            target=node[1]
            if target[0]!='name':function=self.eval(target,env);name=None
            else:name=target[1];function=env.get(name,self.functions.get(name))
            if function is not None and not callable(function):
                args=self.index_args(function,node[2],env);return get(function,args)
            args=[self.eval(n,env) for n in node[2]]
            result=function(*args) if callable(function) else builtin(name,args)
            return result if multi or not isinstance(result,tuple) else result[0] if result else None
        raise UnsupportedMatlab('Unsupported expression '+kind)
    def index_args(self,value,nodes,env):
        dims=[len(flat(value))] if len(nodes)==1 else [value.rows,value.cols] if isinstance(value,M) else [1,1]
        return [self.eval(node,env|{'end':dims[i]}) for i,node in enumerate(nodes)]
    def assign(self,target,value,env):
        if target[0]=='discard':return
        if target[0]=='dynamic_field':
            destination=self.eval(target[1],env)
            field=_dynamic_field_name(self.eval(target[2],env))
            if not isinstance(destination,dict):
                raise UnsupportedMatlab('Dynamic field assignment requires a struct')
            destination[field]=_value_copy(value)
            return
        if target[0]=='name':
            pieces=target[1].split('.');destination=env
            for piece in pieces[:-1]:
                if piece not in destination:destination[piece]={}
                destination=destination[piece]
            destination[pieces[-1]]=value.clone() if isinstance(value,M) else copy.deepcopy(value)
            return
        if target[0]=='call' and target[1][0]=='name':
            name=target[1][1]
            if name not in env:raise UnsupportedMatlab('Array must be allocated before indexed assignment: '+name)
            env[name]=put(env[name],self.index_args(env[name],target[2],env),value);return
        if target[0]=='matrix':
            names=[v for row in target[1] for v in row]
            if not isinstance(value,tuple) or len(value)!=len(names):raise ValueError('Output arity mismatch')
            for name,item in zip(names,value):self.assign(name,item,env)
            return
        raise UnsupportedMatlab('Unsupported assignment target')
    def execute(self,body,env):
        for statement in body:
            if statement[0]=='define':
                name,params,outputs,statements=statement[1]
                env[name]=Function(name,params,outputs,statements,self.functions,env)
        for statement in body:
            kind=statement[0]
            if kind=='define':continue
            if kind=='assign':self.assign(statement[1],self.eval(statement[2],env,multi=statement[1][0]=='matrix'),env)
            elif kind=='expression':self.eval(statement[1],env)
            elif kind=='if':
                for condition,branch in statement[1]:
                    if truth(self.eval(condition,env)):self.execute(branch,env);break
                else:self.execute(statement[2],env)
            elif kind=='for':
                values=flat(self.eval(statement[2],env))
                if len(values)>100000:raise ValueError('Loop limit exceeded')
                for value in values:
                    env[statement[1]]=value
                    try:self.execute(statement[3],env)
                    except _Break:break
                    except _Continue:continue
            elif kind=='try':
                try:self.execute(statement[1],env)
                except (ValueError,ArithmeticError) as exc:
                    # Unknown interpreter constructs are programmer gaps, not
                    # physical-model errors that MATLAB catch may conceal.
                    if isinstance(exc,UnsupportedMatlab) or statement[3] is None:raise
                    if statement[2] is not None:env[statement[2]]=_error_record(exc)
                    self.execute(statement[3],env)
            elif kind=='while':
                count=0
                while truth(self.eval(statement[1],env)):
                    count+=1
                    if count>100000:raise ValueError('Loop limit exceeded')
                    try:self.execute(statement[2],env)
                    except _Break:break
                    except _Continue:continue
            elif kind=='return':raise _Return()
            elif kind=='break':raise _Break()
            elif kind=='continue':raise _Continue()
            else:raise UnsupportedMatlab('Unsupported statement '+kind)


def compile_functions(source):
    functions={}
    for name,params,outputs,body in Parser(source).functions():
        functions[name]=Function(name,params,outputs,body,functions)
    return functions


class _LinkedFunctions(dict):
    def __init__(self,local,public,resolver):
        super().__init__(local);self.public=public;self.resolver=resolver
    def get(self,name,default=None):
        if name in self:return dict.get(self,name)
        if name in self.public:return self.public[name]
        return self.resolver(name) if self.resolver else default


def compile_model(model,source_root=None):
    """Link chart-public functions while keeping each source's helpers local."""
    modules=[];public={}
    for source in model['functions']:
        functions=compile_functions(source['source']);modules.append(functions)
        if source['names']:public[source['names'][0]]=functions[source['names'][0]]
    missing=set()
    def resolve(name):
        if source_root is None or name in missing:return None
        if not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*',name):return None
        pieces=name.split('.')
        root=Path(source_root)
        if len(pieces)>1:candidates=[root.joinpath(*('+'+p for p in pieces[:-1]),pieces[-1]+'.m')]
        else:candidates=[root/(name+'.m'),root/'simulink'/(name+'.m')]
        file=next((p for p in candidates if p.is_file()),None)
        if file is None:missing.add(name);return None
        functions=compile_functions(file.read_text(encoding='utf-8-sig'))
        function=functions.get(pieces[-1])
        if function is None:raise UnsupportedMatlab('External source has no matching function '+name)
        public[name]=function
        namespace=_LinkedFunctions(functions,public,resolve)
        for local in functions.values():local.functions=namespace
        return function
    for functions in modules:
        namespace=_LinkedFunctions(functions,public,resolve)
        for function in functions.values():function.functions=namespace
    return public
