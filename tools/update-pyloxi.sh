#!/bin/bash -eux
wget -O loxi.tar.gz https://github.com/floodlight/loxigen-artifacts/tarball/master
SHA1=$( tar -tzf loxi.tar.gz| head -n1 | grep -oP 'floodlight-loxigen-artifacts-\K\w+')
git rm -rq src/python/loxi
git checkout HEAD src/python/loxi/LICENSE.pyloxi
tar -xzf loxi.tar.gz --xform s,floodlight-loxigen-artifacts-$SHA1/pyloxi,src/python,
git add src/python/loxi
git commit -m "update pyloxi to $SHA1"
rm loxi.tar.gz
