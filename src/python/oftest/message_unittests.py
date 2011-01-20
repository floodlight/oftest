#!/usr/bin/python 

import unittest
from oftest import message
from oftest import action
from oftest import instruction
from oftest import cstruct as ofp

class flow_stats_pack(unittest.TestCase):
    def runTest(self):
        msg = message.flow_stats_entry()
        match = ofp.ofp_match()
        match.wildcards &= ~ofp.OFPFW_IN_PORT
        act = action.action_output()
        act.port = 3
        msg.match = match
        pkt = msg.pack()
        self.assertEqual(len(pkt), 136)
        inst = instruction.instruction_apply_actions()
        self.assertTrue(inst.actions.add(act), "Could not add action")
        self.assertTrue(msg.instructions.add(inst), "Could not add instructions")
        #self.assertTrue(msg.actions.add(act), "Could not add action")
        pkt = msg.pack()
        # 160 = 136 for flow_stats_entry and 24 for instruction_list
        self.assertEqual(len(pkt), 160)
        rep = message.flow_stats_reply()
        self.assertEqual(len(rep.pack()),12)
        rep.stats.append(msg)
        self.assertEqual(len(rep.pack()),172)
        

        
class match_pack(unittest.TestCase):
    def runTest(self):
        match = ofp.ofp_match()
        self.assertEqual(len(match.pack()), 88)
        
        
if __name__ == '__main__':
    unittest.main()
