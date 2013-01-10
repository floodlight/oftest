import struct
import match as match
from match import oxm_tlv
from binascii import b2a_hex
from base_list import ofp_base_list


class match_list(ofp_base_list):

    def __init__(self):
        ofp_base_list.__init__(self)
        self.tlvs = self.items
        self.name = "match"
        self.class_list = match.match_class_list

    def __len__(self):
        return sum([len(i) for i in self])
    
    def unpack(self, binary_string, bytes=None):
        if bytes <= 4:
            return binary_string[4:]
        if bytes == None:
            bytes = len(binary_string)
        offset = 0
        cur_string = binary_string
        while offset < bytes:
            read = 0
            oxm_class, oxm_fieldhm, oxm_length = struct.unpack("!HBB", cur_string[read:read+4])   
            #Found padding bytes?
            if not oxm_class:
                break
            oxm_field = oxm_fieldhm >> 1
            oxm_hasmask = oxm_fieldhm & 0x00000001
            payload = struct.unpack("!" + str(oxm_length) + "s", cur_string[read+4:read+4+oxm_length])[0]
            if oxm_hasmask:
                value, mask = payload[:oxm_length/2], payload[oxm_length/2:]    
            else: 
                value, mask = payload, None
            oxm = oxm_tlv(oxm_field, oxm_hasmask, oxm_length, value,mask, oxm_class)
            self.tlvs.append(oxm)
            read = 4 + oxm_length
            offset += read
            cur_string = cur_string[read:]
            
        return cur_string
