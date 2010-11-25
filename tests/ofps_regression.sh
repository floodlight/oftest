#!/bin/sh
echo Assumes you've run ofps somewhere else
echo    like via run_switch.py
exec ./oft --verbose --test-spec=Echo,EchoWithData,PacketIn,PacketOut,FlowStatsGet
