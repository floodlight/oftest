#!/bin/sh
echo Assumes ofps is running somewhere else
echo    like via run_switch.py
exec ./oft --verbose --test-spec=\
Echo,EchoWithData,FlowRemoveAll,PacketIn,PacketOut,FeaturesRequest,\
FlowStatsGet,FlowStats,DirectPacket,DirectPacketICMP,TwoTable1,\
BaseMatchCase,PortConfigMod,\
TableStatsGet,DescStatsGet,\
BlockPacketInByPort

##### output from `./oft --verbose 2>&1 | grep runTest | sort -r -k 4`
# runTest (pktact.TwoTable1) ... ok
# runTest (pktact.DirectPacket) ... ok
# runTest (pktact.DirectPacketICMP) ... ok
# runTest (pktact.BaseMatchCase) ... ok
# runTest (flow_stats.FlowStats) ... ok
# runTest (basic.SimpleProtocol) ... ok
# runTest (basic.SimpleDataPlane) ... ok
# runTest (basic.PacketOut) ... ok
# runTest (basic.PacketIn) ... ok
# runTest (basic.FlowStatsGet) ... ok
# runTest (basic.FlowRemoveAll) ... ok
# runTest (basic.FlowMod) ... ok
# runTest (basic.FeaturesRequest) ... ok
# runTest (basic.EchoWithData) ... ok
# runTest (basic.Echo) ... ok
# runTest (basic.DataPlaneOnly) ... ok
# runTest (basic.TableStatsGet) ... ok
# runTest (stats.DescStatsGet) ... ok
# runTest (basic.PortConfigMod) ... ok
# runTest (pktact.StripVLANTag) ... FAIL
# runTest (pktact.ModifyVID) ... FAIL
# runTest (pktact.ModifyTOS) ... FAIL
# runTest (pktact.ModifyL4Src) ... FAIL
# runTest (pktact.ModifyL4Dst) ... FAIL
# runTest (pktact.ModifyL3Src) ... FAIL
# runTest (pktact.ModifyL3Dst) ... FAIL
# runTest (pktact.ModifyL2Src) ... FAIL
# runTest (pktact.ModifyL2Dst) ... FAIL
# runTest (pktact.AddVLANTag) ... FAIL
# runTest (pktact.SingleWildcardMatchTagged) ... ERROR
# runTest (pktact.SingleWildcardMatch) ... ERROR
# runTest (pktact.FloodPlusIngress) ... ERROR
# runTest (pktact.FloodMinusPort) ... ERROR
# runTest (pktact.Flood) ... ERROR
# runTest (pktact.ExactMatchTagged) ... ERROR
# runTest (pktact.ExactMatch) ... ERROR
# runTest (pktact.DirectTwoPorts) ... ERROR
# runTest (pktact.DirectMCNonIngress) ... ERROR
# runTest (pktact.DirectMC) ... ERROR
# runTest (pktact.AllWildcardMatchTagged) ... ERROR
# runTest (pktact.AllWildcardMatch) ... ERROR
# runTest (pktact.AllPlusIngress) ... ERROR
# runTest (pktact.AllExceptOneWildcardMatchTagged) ... ERROR
# runTest (pktact.AllExceptOneWildcardMatch) ... ERROR
# runTest (pktact.All) ... ERROR
# runTest (flow_expire.FlowExpire) ... ERROR
# runTest (caps.FillTableWC) ... ERROR
