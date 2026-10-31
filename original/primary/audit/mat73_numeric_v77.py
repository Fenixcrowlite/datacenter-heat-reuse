"""Restricted read-only MATLAB v7.3 reader for numeric QA, not a general MAT API.

Preserves numeric dimensions, binary64 bits and Fortran element order. Supports
scalar structs, numeric/logical/char datasets and cells; rejects MATLAB objects,
complex/sparse values, struct arrays, null references and external/soft links.
Native Simulink objects remain archived but are deliberately not decoded.
"""
import h5py
import numpy as np


class Mat73Numeric:
    def __init__(self, path):
        self.file = h5py.File(path, 'r')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.file.close()

    def read(self, name):
        link = self.file.get(name, getlink=True)
        if not isinstance(link, h5py.HardLink):
            raise ValueError('Only in-file hard links are supported')
        return self._decode(self.file[name], set())

    def _decode(self, node, ancestors):
        if node.name in ancestors:
            raise ValueError('Cyclic reference')
        ancestors = ancestors | {node.name}
        cls = node.attrs.get('MATLAB_class', b'').decode('ascii')
        if isinstance(node, h5py.Group):
            if cls != 'struct':
                raise ValueError('Only scalar struct groups supported: ' + cls)
            result = {}
            for key in node:
                if not isinstance(node.get(key, getlink=True), h5py.HardLink):
                    raise ValueError('Linked struct field')
                result[key] = self._decode(node[key], ancestors)
            return result
        if cls not in {'double', 'single', 'logical', 'char', 'cell', 'uint64', 'uint32', 'uint16', 'uint8', 'int64', 'int32', 'int16', 'int8'}:
            raise ValueError('Unsupported MATLAB dataset: ' + cls)
        if node.attrs.get('MATLAB_empty', 0):
            dims = tuple(int(x) for x in node[()].flat)
            if cls == 'char':
                return ''
            if cls == 'cell':
                return []
            dtype = {'double': np.float64, 'single': np.float32, 'logical': np.bool_}.get(cls, cls)
            return np.empty(dims, dtype=dtype)
        data = node[()]
        if h5py.check_dtype(ref=node.dtype):
            if cls != 'cell':
                raise ValueError('Struct arrays and object references outside cells are unsupported')
            result = []
            # HDF5 dimension order is reversed relative to the MATLAB arrays.
            for ref in data.transpose().ravel(order='F'):
                if not ref:
                    raise ValueError('Null MATLAB cell reference')
                result.append(self._decode(self.file[ref], ancestors))
            return result
        if data.dtype.fields:
            raise ValueError('Complex/compound numeric dataset unsupported')
        data = data.transpose(tuple(reversed(range(data.ndim))))
        if cls == 'char':
            if data.ndim != 2 or data.shape[0] != 1:
                raise ValueError('Only character rows supported')
            return data.astype('<u2').tobytes().decode('utf-16-le')
        return data.astype(np.bool_) if cls == 'logical' else data


def plain(value):
    """Convert numeric arrays to reviewer conventions, preserving binary64 values."""
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        if value.size == 0:
            return []
        if value.size == 1:
            return value.item()
        if value.ndim == 2 and 1 in value.shape:
            return value.ravel(order='F').tolist()
        return value.tolist()
    return value
