import rasterio
import numpy as np
import argparse
import pathlib

# parse command line
p = argparse.ArgumentParser(
    description="""
Convert

| 64 | 128 | 1  |
| 32 |  0  | 2  |
| 16 |  8  | 4  |

to

| 7 | 8 | 9  |
| 4 | 5 | 6  |
| 1 | 2 | 3  |

and 255 to 255

""",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
p.add_argument("input", type=pathlib.Path, help="Original D8 tif")
p.add_argument("output", type=pathlib.Path, help="New LDD file tif")

args = p.parse_args()

mapping = {0: 5, 1: 9, 2: 6, 4: 3, 8: 2, 16: 1, 32: 4, 64: 7, 128: 8, 255: 255}

with rasterio.open(args.input) as src:
    data = src.read(1)
    out = data.copy()

    for old, new in mapping.items():
        out[data == old] = new

    profile = src.profile.copy()
    profile.update(dtype="uint16", nodata=255)

    with rasterio.open(args.output, "w", **profile) as dst:
        dst.write(out.astype(np.uint16), 1)
