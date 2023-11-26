#!/usr/bin/env bash
set -Eeuo pipefail

echo 'Set first argument to "addgit" if you want to add wkt files automatically'

# indicate DOCKER PROJ version
PROJ_VERSION=9.3.0
PYPROJ_VERSION=3.6.1
TAG="crs-explorer:$PROJ_VERSION"

# prepare destination
DIRNAME=`dirname $(readlink -f $0)`
mkdir -p $DIRNAME/dist
test "$(ls -A $DIRNAME/dist/)" && rm -r $DIRNAME/dist/*

# build container
docker build --pull --build-arg VERSION=$PROJ_VERSION --build-arg PYPROJ_VERSION=$PYPROJ_VERSION --tag $TAG $DIRNAME

# execute container
docker run --user $(id -u):$(id -g) --rm -v "$DIRNAME/dist:/home/dist" $TAG

DEST=$DIRNAME/..
# copy to root location
cp $DIRNAME/dist/* $DEST