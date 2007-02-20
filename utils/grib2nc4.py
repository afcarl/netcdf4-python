try:
    from PyNGL import nio
except ImportError:
    raise ImportError('need PyNGL/PyNIO to read GRIB files')
import netCDF4_classic as netCDF4
import sys
import numpy as NP

# convert a GRIB1 file to netCDF (NETCDF4_CLASSIC format
# with zlib compression) using PyNIO and netCDF4.

if len(sys.argv) < 2:
    print """
usage:  python grib2nc4.py <grib file name>
a netCDF file (in NETCDF4_CLASSIC format, with zlib compression)
called <grib file name>.nc will be created

requires PyNIO to read GRIB1 files.
"""
    sys.exit(1)

grbfile = sys.argv[1]
f = nio.open_file(grbfile+'.grb')
nc = netCDF4.Dataset(grbfile+'.nc','w')

for name,att in f.__dict__.items():
    setattr(nc,name,att)

print 'dimensions (name, length):'
for dimname,dim in f.dimensions.items():
    nc.createDimension(dimname,dim)
    print dimname, dim

print 'variables (name, type, dimensions, units):'
for varname,var in f.variables.items():
    gribdata = NP.array(var[:])
    tmpdata = gribdata.flatten()
    # values > 1.e10 are probably bitmask
    tmpdata = tmpdata.compress(tmpdata < 1.e10)
    # find max/min (excluding masked values)
    if hasattr(var,'_FillValue'):
        tmpdata = tmpdata.compress(NP.fabs(tmpdata-var._FillValue) > 1.e-7)
    minval = tmpdata.min(); maxval = tmpdata.max()
    if maxval-minval < 1.:
        eps = 0.1*(maxval-minval)
    else:
        eps = 0.01
    # find least significant digit of unpacked grib data.
    lsd = 0
    while 1:
        fact = pow(10.,lsd)
        truncdata = NP.around(fact*tmpdata)
        if NP.fabs(truncdata-fact*tmpdata).max() < eps or lsd == 7: break
        lsd = lsd + 1
    print varname,var.typecode(),var.dimensions,var.units,lsd,minval,maxval,eps
    varo = nc.createVariable(varname,var.typecode(),var.dimensions,least_significant_digit=lsd)
    for name, att in var.__dict__.items():
        setattr(varo,name,att)
    varo[:] = gribdata[:]
