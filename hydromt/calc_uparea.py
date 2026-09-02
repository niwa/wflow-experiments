import argparse
import sys
import numpy as np
import xarray as xr
import hydromt

"""
Derive flow direction ('flwdir', D8) from elevation grid ('elevtn') using
hydromt's own d8_from_dem, then compute upstream area ('uparea', km2) from
that same derived flwdir. Both go through hydromt/pyflwdir's own pipeline
(depression filling, orientation checks) so they're guaranteed consistent
with each other and with what hydromt_wflow expects -- rather than trusting
a separately-produced flwdir that might disagree with it in subtle ways.

Usage:
    python compute_uparea.py ni_hydrography.nc --elevtn-var elevtn

Writes "<input>_with_flwdir_uparea.nc" alongside the original, containing all
original variables plus the newly-derived 'flwdir' (overwrites any existing
'flwdir' variable of that name in the output -- the original file is left
untouched) and 'uparea' (km2, nodata=-9999).
"""


def derive_uparea(ds: xr.Dataset, crs=None):
    if "flwdir" not in ds:
        raise KeyError("flwdir not in dataset")

    if crs is not None:
        ds.raster.set_crs(crs)  # mutates in place, propagates to all variables
    elif ds.flwdir.raster.crs is None:
        raise ValueError(
            "flwdir has no CRS set and none was given. Pass --crs "
            "(e.g. --crs EPSG:2193)."
        )

    # hydromt/pyflwdir require north-up orientation (y descending). Flip the
    # whole dataset (not just elevtn) so every variable -- including any
    # existing flwdir/uparea you keep around for comparison -- stays aligned.
    y_dim = ds.flwdir.raster.y_dim
    assert float(ds[y_dim].values[0]) > float(ds[y_dim].values[-1]), (
        f"{y_dim!r} coordinate is not descending"
    )

    flw = ds.flwdir
    print(flw.values)

    if flw.raster.nodata is None:
        raise ValueError("flwdir has no nodata value set")

    flwdir = hydromt.gis.flw.flwdir_from_da(flw, ftype="ldd")
    uparea = flwdir.upstream_area(unit="km2")

    print(f"  max uparea: {np.nanmax(uparea):.3f} km2")

    da_uparea = xr.DataArray(
        uparea.astype(np.float32),
        dims=flw.dims,
        coords=flw.coords,
        name="uparea",
        attrs={
            "units": "km2",
            "long_name": "upstream drainage area",
            "_FillValue": -9999.0,
        },
    )
    return ds, da_uparea


p = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
p.add_argument(
    "nc_path",
    help="Path to the hydrography NetCDF (must contain the elevation variable)",
)
p.add_argument(
    "--out", default=None, help="Output path (default: <input>_with_uparea.nc)"
)
p.add_argument(
    "--crs",
    default=None,
    help="CRS to set on the elevtn array if not already embedded, e.g. EPSG:2193 (only needed if the script errors asking for it)",
)
p.add_argument(
    "--mask-and-scale",
    dest="mask_and_scale",
    action="store_true",
    default=False,
    help="Let xarray apply _FillValue/scale_factor masking on open. Default is off, matching mask_and_scale: false in your data catalog.",
)
args = p.parse_args()

out_path = args.out or args.nc_path.rsplit(".nc", 1)[0] + "_with_uparea.nc"

ds = xr.open_dataset(args.nc_path, mask_and_scale=args.mask_and_scale)
print(ds.flwdir.values)
try:
    ds, da_uparea = derive_uparea(ds, crs=args.crs)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)

ds_out = ds.copy()
ds_out["uparea"] = da_uparea
ds_out.to_netcdf(out_path)
print(f"Wrote {out_path} (added 'uparea')")
