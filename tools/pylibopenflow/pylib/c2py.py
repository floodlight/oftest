"""This module converts C types to Python struct pattern string.

Date June 2009
Created by ykk
"""
import cheader
import struct

class cstruct2py:
    """Class converts C struct to Python struct pattern string

    Date October 2009
    Created by ykk
    """
    def __init__(self):
        """Initialize
        """
        ##Mapping
        self.structmap = {}
        self.structmap["char"] = "c"
        self.structmap["signed char"] = "b"
        self.structmap["uint8_t"]=\
            self.structmap["unsigned char"] = "B"
        self.structmap["short"] = "h"
        self.structmap["uint16_t"] =\
            self.structmap["unsigned short"] = "H"
        self.structmap["int"] = "i"
        self.structmap["unsigned int"] = "I"
        self.structmap["long"] = "l"
        self.structmap["uint32_t"] =\
            self.structmap["unsigned long"] = "L"
        self.structmap["long long"] = "q"
        self.structmap["uint64_t"] =\
            self.structmap["unsigned long long"] = "Q"
        self.structmap["float"] = "f"
        self.structmap["double"] = "d"

    def get_pattern(self,ctype):
        """Get pattern string for ctype.
        Return None if ctype is not expanded.
        """
        if (ctype.expanded):
            if (isinstance(ctype, cheader.cprimitive)):
                return self.structmap[ctype.typename]
            elif (isinstance(ctype, cheader.cstruct)):
                string=""
                for member in ctype.members:
                    string += self.get_pattern(member)
                return string
            elif (isinstance(ctype, cheader.carray)):
                if (ctype.size == 0):
                    return ""
                else:
                    string = self.get_pattern(ctype.object)
                    return string * ctype.size
        return None
        
    def get_size(self, ctype, prefix="!"):
        """Return size of struct or pattern specified
        """
        if (isinstance(ctype, str)):
            return struct.calcsize(ctype)
        elif (isinstance(ctype, cheader.ctype)):
            return struct.calcsize(prefix + self.get_pattern(ctype))
        else:
            return 0

class structpacker:
    """Pack/unpack packets with ctype.
    
    Date October 2009
    Created by ykk
    """
    def __init__(self, prefix=""):
        """Initialize with prefix to struct
        """
        ##Reference to prefix
        self.prefix = prefix
        
    def pack(self, ctype, *arg):
        """Pack packet accordingly ctype or pattern provided.
        Return struct packed.
        """
        if (isinstance(ctype, str)):
            return struct.pack(self.prefix+ctype, *arg)
        elif (isinstance(ctype, cheader.ctype)):
            return struct.pack(self.prefix+cstruct2py.get_pattern(ctype),
                               *arg)
        else:
            return None

    def unpack_from_front(self, ctype, binaryString, returnDictionary=True):
        """Unpack packet using front of packet,
        accordingly ctype or pattern provided.

        Return (dictionary of values indexed by arg name, 
        remaining binary string) if ctype is cheader.ctype
        and returnDictionary is True, 
        else return (array of data unpacked, remaining binary string).
        """
        pattern = ""
        if (isinstance(ctype, str)):
            pattern = ctype
        elif (isinstance(ctype, cheader.ctype)):
            pattern = cstruct2py.get_pattern(ctype)
        else:
            return None
        dsize = struct.calcsize(pattern)

        if (dsize > len(binaryString)):
            return None

        return (structpacker.peek_from_front(self, pattern, binaryString, returnDictionary),
                binaryString[dsize:])

    def peek_from_front(self, ctype, binaryString, returnDictionary=True):
        """Unpack packet using front of packet,
        accordingly ctype or pattern provided.

        Return dictionary of values indexed by arg name,
        if ctype is cheader.ctype and returnDictionary is True, 
        else return array of data unpacked.
        """
        pattern = self.prefix
        if (isinstance(ctype, str)):
            pattern += ctype
        elif (isinstance(ctype, cheader.ctype)):
            pattern += cstruct2py.get_pattern(ctype)
        else:
            return None
        dsize = struct.calcsize(pattern)
        if (dsize > len(binaryString)):
            return None
        data = struct.unpack(pattern, binaryString[0:dsize])
        
        #Return values
        if (isinstance(ctype, str) or
            (not returnDictionary)):
            return data
        else:
            return self.data2dic(data, ctype)

    def data2dic(self,ctype,data):
        """Convert data to dictionary
        """
        valDic = {}
        names = ctype.get_names()
        for name in names:
            valDic[name] = []
        for d in data:
            name = names.pop(0)
            valDic[name].append(d)
        return valDic

