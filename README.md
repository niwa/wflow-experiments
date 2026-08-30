# Wflow

This details my experiments in getting Wflow running in New Zealand, both for
calibrated catchments and nationally.

Wflow.jl [repo](https://github.com/Deltares/Wflow.jl) and their [doco](https://deltares.github.io/Wflow.jl/stable/)

## Installing Julia

On linux
```
curl -fsSL https://install.julialang.org | sh
```
will install `julia` and `juliaup` in your HOME dir.

Under Windows, get it from the Microsoft store
```
winget install --name Julia --id 9NJNWW8PVKMN -e -s msstore
```

The HPC already has julia via
```
conda activate niwa_julia110_2026.05.1
export JULIA_DEPOT_PATH="$HOME/.julia"      # probably want this in your .bashrc
```

## Installing Wflow

Start julia, hit ] to get into the package manager and type
```
add Wflow
```

## Moselle example

This isn't in NZ, the Moselle catchment is in Germany, it is a tributary to the Rhine.  However
it is Deltares most basic [example](https://deltares.github.io/Wflow.jl/dev/getting_started/download_example_models.html)
and if you can't run this one, you won't be able to run anything else.

Start julia and copy'n'paste this in:
```
# urls to TOML and netCDF of the Piave example model
toml_url = "https://raw.githubusercontent.com/Deltares/Wflow.jl/main/Wflow/test/sbm_gwf_piave_demand_config.toml"
staticmaps = "https://github.com/visr/wflow-artifacts/releases/download/v1.0.0/staticmaps-piave.nc"
forcing = "https://github.com/visr/wflow-artifacts/releases/download/v1.0.0/forcing-piave.nc"
instates = "https://github.com/visr/wflow-artifacts/releases/download/v1.0.0/instates-piave-gwf.nc"

# create a "data/input" directory in the current directory
testdir = @__DIR__
inputdir = joinpath(testdir, "data/input")
isdir(inputdir) || mkpath(inputdir)
toml_path = joinpath(testdir, "sbm_gwf_piave_demand_config.toml")

# download resources to current and data dirs
download(staticmaps, joinpath(inputdir, "staticmaps-piave.nc"))
download(forcing, joinpath(inputdir, "forcing-piave.nc"))
download(instates, joinpath(inputdir, "instates-piave-gwf.nc"))
download(toml_url, toml_path)
```

This makes the toml you need and a data folder with the forcings etc in it.  To
run it while in julia you can do
```
using Wflow
toml_path = "sbm_config.toml"
Wflow.run(toml_path)
```

The output ends up in `data/output`

## Building NZ example

Here I build a small NZ example from scratch

### Required static input data

There are seven required static input variables, all provided via a NetCDF raster file.

* `wflow_ldd` is the flow directions, by default it uses the PCRaster LDD convention: ~[](lddcode.png).

* `wflow_river` is 1 where there is a river, and nodata where not.

* `wflow_riverlength`.  FIXME

* `wflow_riverwidth`.  Width of the river in metres in that raster cell.

* `wflow_subcatch`.  1 for the catchment, nodata elsewhere.

* `Slope`.  This is the land slope in m/m.  FIXME

* `RiverSlope`.  The slope of the river in m/m.  FIXME

All of these are straight forward except I'm not sure what the river length is,
it is really not clear from their example.  Also the slopes need defining, lots
of different ways to define it.

### Required forcing data

There are three required variables: `pet`, `precip`, and `temp`, all provided via a
NetCDF.  The examples often have `mask` and `idx_out`.  The mask isn't
required (we need forcing to cover at least `wflow_subcatch` but Wflow can work
this out), and `idx_out` is just a pointer into input data that was used to
make the forcing data.


