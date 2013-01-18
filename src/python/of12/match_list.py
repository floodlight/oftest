import struct
import binascii
import match as match
from match import oxm_tlv 
from base_list import ofp_base_list


class match_list(ofp_base_list):

    def __init__(self):
        ofp_base_list.__init__(self)
        self.tlvs = self.items
        self.name = "match"
        self.class_list = match.match_class_list

    def __len__(self):
        return sum([len(i) for i in self])

    def __eq__(self, other):
        self.tlvs.sort(key=lambda x: x.field); 
        other.tlvs.sort(key=lambda x: x.field);
        return self.tlvs == other.tlvs

    def unpack(self, binary_string, bytes=None):
        oxm_tlv.factory()
        if bytes <= 4:
            return binary_string[4:]
        if bytes == None:
            bytes = len(binary_string)
        offset = 0
        cur_string = binary_string
        part = lambda: cur_string[read+4:read+4+oxm_length]
        while offset < bytes:
            read = 0
            oxm_class, oxm_fieldhm, oxm_length = struct.unpack("!HBB", 
                cur_string[read:read+4])   
            #Found padding bytes?
            if not oxm_class:
                break
            oxm_field = oxm_fieldhm >> 1
            oxm_hasmask = oxm_fieldhm & 0x00000001

            if oxm_length == 1:
                if oxm_hasmask:
                    value, mask = struct.unpack("BB", part())[:2]
                else: 
                    value = struct.unpack("!B", part())[0]
                    mask = None
            elif  oxm_length == 2 or (oxm_length == 4 and oxm_hasmask == True):
                if oxm_hasmask:
                    value, mask = struct.unpack("!HH", part())[:2]
                else:
                    value = struct.unpack("!H", part())[0]
                    mask = None    
            elif oxm_length == 4 or (oxm_length == 8 and oxm_hasmask == True):
                if oxm_hasmask:
                    value, mask = struct.unpack("!II", part())[:2]
                else: 
                    value = struct.unpack("!I", part())[0]
                    mask = None
            elif oxm_length == 6 or oxm_length == 12:
                if oxm_hasmask:
                    data = struct.unpack("!12B", part())[0]
                    value, mask = data[:6], data[6:]
                else:
                    value =  list(struct.unpack("!6B", part()))
                    mask = None
            elif oxm_length == 8 or (oxm_length == 16 and oxm_hasmask == True):
                if oxm_hasmask:
                    value, mask = struct.unpack("!QQ", part())[0]
                else: 
                    value = struct.unpack("!Q", part())[0]
                    mask = None
            elif oxm_length == 16 or oxm_length == 32:
                if oxm_hasmask:
                    data =  struct.unpack("!32s", part())[0]
                    value, mask = data[:16], data[16:]
                else:
                    value =  struct.unpack("!16s", part())[0]
                    mask = None             
          
            oxm = oxm_tlv.create(oxm_field)
            oxm.set_hasmask(oxm_hasmask)
            oxm.set_value(value)
            oxm.set_mask(mask)
            self.tlvs.append(oxm)
            read = 4 + oxm_length
            offset += read
            cur_string = cur_string[read:]   
        return cur_string
