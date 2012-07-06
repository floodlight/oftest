
# Python OpenFlow instruction wrapper classes

from cstruct import *
from action_list import action_list



class instruction_write_metadata(ofp_instruction_write_metadata):
    """
    Wrapper class for write_metadata instruction object

    Data members inherited from ofp_instruction_write_metadata:
    @arg type
    @arg len
    @arg metadata
    @arg metadata_mask

    """
    def __init__(self):
        ofp_instruction_write_metadata.__init__(self)
        self.type = OFPIT_WRITE_METADATA
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "instruction_write_metadata\n"
        outstr += ofp_instruction_write_metadata.show(self, prefix)
        return outstr


class instruction_goto_table(ofp_instruction_goto_table):
    """
    Wrapper class for goto_table instruction object

    Data members inherited from ofp_instruction_goto_table:
    @arg type
    @arg len
    @arg table_id

    """
    def __init__(self):
        ofp_instruction_goto_table.__init__(self)
        self.type = OFPIT_GOTO_TABLE
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "instruction_goto_table\n"
        outstr += ofp_instruction_goto_table.show(self, prefix)
        return outstr


class instruction_write_actions(ofp_instruction_actions):
    """
    Wrapper class for write_actions instruction object

    Data members inherited from ofp_instruction_actions:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_instruction_actions.__init__(self)
        self.type = OFPIT_WRITE_ACTIONS
        self.actions = action_list()
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "instruction_write_actions\n"
        outstr += ofp_instruction_actions.show(self, prefix)
        outstr += self.actions.show(prefix)
        return outstr
    def unpack(self, binary_string):
        binary_string = ofp_instruction_actions.unpack(self, binary_string)
        bytes = self.len - OFP_INSTRUCTION_ACTIONS_BYTES
        self.actions = action_list()
        binary_string = self.actions.unpack(binary_string, bytes=bytes)
        return binary_string
    def pack(self):
        self.len = self.__len__()
        packed = ""
        packed += ofp_instruction_actions.pack(self)
        packed += self.actions.pack()
        return packed
    def __len__(self):
        return ofp_instruction_actions.__len__(self) + self.actions.__len__()


class instruction_apply_actions(ofp_instruction_actions):
    """
    Wrapper class for apply_actions instruction object

    Data members inherited from ofp_instruction_actions:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_instruction_actions.__init__(self)
        self.type = OFPIT_APPLY_ACTIONS
        self.actions = action_list()
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "instruction_apply_actions\n"
        outstr += ofp_instruction_actions.show(self, prefix)
        outstr += self.actions.show(prefix)
        return outstr
    def unpack(self, binary_string):
        binary_string = ofp_instruction_actions.unpack(self, binary_string)
        bytes = self.len - OFP_INSTRUCTION_ACTIONS_BYTES
        self.actions = action_list()
        binary_string = self.actions.unpack(binary_string, bytes=bytes)
        return binary_string
    def pack(self):
        self.len = self.__len__()
        packed = ""
        packed += ofp_instruction_actions.pack(self)
        packed += self.actions.pack()
        return packed
    def __len__(self):
        return ofp_instruction_actions.__len__(self) + self.actions.__len__()


class instruction_clear_actions(ofp_instruction):
    """
    Wrapper class for clear_actions instruction object

    Data members inherited from ofp_instruction:
    @arg type
    @arg len

    """
    def __init__(self):
        ofp_instruction.__init__(self)
        self.type = OFPIT_CLEAR_ACTIONS
        self.len = self.__len__()
    def show(self, prefix=''):
        outstr = prefix + "instruction_clear_actions\n"
        outstr += ofp_instruction.show(self, prefix)
        return outstr

instruction_class_list = (
    instruction_apply_actions,
    instruction_clear_actions,
    instruction_goto_table,
    instruction_write_actions,
    instruction_write_metadata)
