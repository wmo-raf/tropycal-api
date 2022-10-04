#!/bin/bash
set -xeu

prefix=${PREFIX:-/usr}

v=3.7.2
(
  set -xeu
  wget -q http://download.osgeo.org/geos/geos-${v}.tar.bz2
  bunzip2 geos-${v}.tar.bz2
  tar -xf geos-${v}.tar
  cd geos-${v}
  ./configure --prefix="$prefix"
  make -j4
  make install
)
rm -rf geos-${v}
rm -f geos-${v}.tar.bz2
rm -f geos-${v}.tar

v=6.1.1
(
  set -xeu
  wget -q http://download.osgeo.org/proj/proj-${v}.tar.gz
  tar -xf proj-${v}.tar.gz
  cd proj-${v}
  ./configure --prefix="$prefix"
  make -j4
  make install
)
rm -rf proj-${v}
rm -f proj-${v}.tar.gz

v=3.2.0
(
  set -xeu
  wget -q http://download.osgeo.org/gdal/${v}/gdal-${v}.tar.gz
  tar -xf gdal-${v}.tar.gz
  cd gdal-${v}
  ./configure --with-geos=yes --with-netcdf --with-proj=/usr
  make -j4
  make install
)
rm -rf gdal-${v}
rm -f gdal-${v}.tar.gz
