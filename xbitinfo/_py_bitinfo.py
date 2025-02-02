import dask.array as da
import numpy as np
import numpy.ma as nm


def bitpaircount_u1(a, b):
    assert a.dtype == "u1"
    assert b.dtype == "u1"
    unpack_a = (
        a.flatten()
        .map_blocks(
            np.unpackbits,
            drop_axis=0,
            meta=np.array((), dtype=np.uint8),
            chunks=(a.size * 8,),
        )
        .astype("u1")
    )
    unpack_b = (
        b.flatten()
        .map_blocks(
            np.unpackbits,
            drop_axis=0,
            meta=np.array((), dtype=np.uint8),
            chunks=(b.size * 8,),
        )
        .astype("u1")
    )
    index = ((unpack_a << 1) | unpack_b).reshape(-1, 8)

    selection = np.array([0, 1, 2, 3], dtype="u1")
    sel = np.where((index[..., np.newaxis]) == selection, True, False)
    to_return = sel.sum(axis=0).reshape(8, 2, 2)
    return to_return


def bitpaircount(a, b):
    assert a.dtype.kind == "u"
    assert b.dtype.kind == "u"
    nbytes = max(a.dtype.itemsize, b.dtype.itemsize)

    a, b = np.broadcast_arrays(a, b)

    bytewise_counts = []
    for i in range(nbytes):
        s = (nbytes - 1 - i) * 8
        bitc = bitpaircount_u1((a >> s).astype("u1"), (b >> s).astype("u1"))
        bytewise_counts.append(bitc)
    return np.concatenate(bytewise_counts, axis=0)


def mutual_information(a, b, base=2):
    size = np.prod(np.broadcast_shapes(a.shape, b.shape))
    counts = bitpaircount(a, b)

    p = counts.astype("float") / size
    p = da.ma.masked_equal(p, 0)
    pr = p.sum(axis=-1)[..., np.newaxis]
    ps = p.sum(axis=-2)[..., np.newaxis, :]
    mutual_info = (p * np.log(p / (pr * ps))).sum(axis=(-1, -2)) / np.log(base)
    return mutual_info


def bitinformation(a, axis=0):
    sa = tuple(slice(0, -1) if i == axis else slice(None) for i in range(len(a.shape)))
    sb = tuple(
        slice(1, None) if i == axis else slice(None) for i in range(len(a.shape))
    )
    return mutual_information(a[sa], a[sb])
