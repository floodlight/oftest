#!/bin/sh
echo Assumes ofps is running somewhere else
echo    like via run_switch.py
exec ./oft --verbose --test-spec=FlowStats,Echo,EchoWithData,PacketIn,PacketOut,FlowStatsGet,DirectPacket,DirectPacketICMP
