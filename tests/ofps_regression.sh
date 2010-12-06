#!/bin/sh
echo Assumes ofps is running somewhere else
echo    like via run_switch.py
exec ./oft --verbose --test-spec=Echo,EchoWithData,PacketIn,PacketOut,\
FlowStatsGet,FlowStats,DirectPacket,DirectPacketICMP,TwoTable1

