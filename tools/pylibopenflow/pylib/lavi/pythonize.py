"""This module generate Python code for LAVI and messenger

(C) Copyright Stanford University
Date January 2010
Created by ykk
"""
import cpythonize

class msgrules(cpythonize.rules):
    """Class that specify rules for pythonization of messenger

    (C) Copyright Stanford University
    Date January 2010
    Created by ykk
    """
    def __init__(self):
        """Initialize rules
        """
        cpythonize.rules.__init__(self)
        ##Default values for members
        #Default values for struct
        ##Macros to exclude
        self.excluded_macros = ['MESSAGE_HH__']
        ##Enforce mapping
        self.enforced_maps['messenger_msg'] = [ ('type','msg_type') ]

class lavirules(msgrules):
    """Class that specify rules for pythonization of LAVI messages

    (C) Copyright Stanford University
    Date January 2010
    Created by ykk
    """
    def __init__(self, laviheader):
        """Initialize rules
        """
        msgrules.__init__(self)
        ##Default values for members
        
        #Default values for struct
        self.struct_default[('lavi_poll_message',
                             'header')] = ".type = "+str(laviheader.get_value('LAVIT_POLL'))
        self.struct_default[('lavi_poll_stop_message',
                             'header')] = ".type = "+str(laviheader.get_value('LAVIT_POLL_STOP'))
        ##Macros to exclude
        self.excluded_macros = ['LAVI_MSG_HH']
        ##Enforce mapping
        self.enforced_maps['lavi_header'] = [ ('type','lavi_type') ]

class msgpythonizer(cpythonize.pythonizer):
    """Class that pythonize C messenger messages

    (C) Copyright Stanford University
    Date January 2010
    Created by ykk
    """
    def __init__(self, msgheader):
        """Initialize
        """
        rules =  msgrules()
        cpythonize.pythonizer.__init__(self, msgheader, rules)
        
class lavipythonizer(cpythonize.pythonizer):
    """Class that pythonize C messenger messages

    (C) Copyright Stanford University
    Date December 2009
    Created by ykk
    """
    def __init__(self, msgheader):
        """Initialize
        """
        rules =  lavirules(msgheader)
        cpythonize.pythonizer.__init__(self, msgheader, rules)
