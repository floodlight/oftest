#!/bin/bash
cd $(dirname $(readlink -f $0))
PYTHONPATH=src/python:tests:tests-1.3 pylint -E tests/*.py tests-1.3/*.py src/python/oftest/*.py
