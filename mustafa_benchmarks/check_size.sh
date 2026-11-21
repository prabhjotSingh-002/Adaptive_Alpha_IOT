#!/bin/bash
set -eu
TMP=/tmp/test_tsch
cd "$TMP/sensor"
msp430-size build/z1/sensor.z1
