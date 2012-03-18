"""This module generate Python code for C structs.

Date January 2010
Created by ykk
"""
import sys
import cheader
import c2py
import datetime
import struct
import re
from config import *

def _space_to(n, str):
    """
    Generate a string of spaces to achieve width n given string str
    If length of str >= n, return one space
    """
    spaces = n - len(str)
    if spaces > 0:
        return " " * spaces
    return " "

class rules:
    """Class that specify rules for pythonization

    Date January 2010
    Created by ykk
    """
    def __init__(self):
        """Initialize rules
        """
        ##Default values for members
        self.default_values = {}
        #Default values for struct
        self.struct_default = {}
        ##What is a tab
        self.tab = "    "
        ##Macros to exclude
        self.excluded_macros = []
        ##Enforce mapping
        self.enforced_maps = {}

    def get_enforced_map(self, structname):
        """Get code to enforce mapping
        """
        code = []
        try:
            mapping = self.enforced_maps[structname]
        except KeyError:
            return None
        for (x,xlist) in mapping:
            code.append("if (not (self."+x+" in "+xlist+")):")
            code.append(self.tab+"return (False, \""+x+" must have values from "+xlist+"\")")
        return code
        

    def get_struct_default(self, structname, fieldname):
        """Get code to set defaults for member struct
        """
        try:
            return "."+fieldname+self.struct_default[(structname, fieldname)]
        except KeyError:
            return None
        
    def get_default_value(self, structname, fieldname):
        """Get default value for struct's field
        """
        try:
            return self.default_values[(structname, fieldname)]
        except KeyError:
            return 0

    def include_macro(self, name):
        """Check if macro should be included
        """
        return not (name in self.excluded_macros)

class pythonizer:
    """Class that pythonize C structures

    Date January 2010
    Created by ykk
    """
    def __init__(self, cheaderfile, pyrules = None, tab="    "):
        """Initialize
        """
        ##Rules
        if (pyrules == None):
            self.rules = rules()
        else:
            self.rules = pyrules
        ##What is a tab (same as rules)
        self.tab = str(tab)
        self.rules.tab = self.tab
        ##Reference to C header file
        self.cheader = cheaderfile
        ##Reference to cstruct2py
        self.__c2py = c2py.cstruct2py()
        ##Code for assertion
        self.__assertcode = []

    def pycode(self,preamble=None):
        """Return pythonized code
        """
        code = []
        code.append("import struct")
        code.append("")
        if (preamble != None):
            fileRef = open(preamble,"r")
            for l in fileRef:
                code.append(l[:-1])
            fileRef.close()
        code.append("# Structure definitions")
        for name,struct in self.cheader.structs.items():
            code.extend(self.pycode_struct(struct))
            code.append("")
        code.append("# Enumerated type definitions")
        for name,enum in self.cheader.enums.items():
            code.extend(self.pycode_enum(name,enum))
            if GEN_ENUM_DICTIONARY:
                code.extend(self.pycode_enum_map(name,enum))
            code.append("")
        code.append("# Values from macro definitions")
        for name,macro in self.cheader.macros.items():
            code.extend(self.pycode_macro(name))
        code.append("")
        code.append("# Basic structure size definitions.")
        if IGNORE_OFP_HEADER:
            code.append("# Does not include ofp_header members.")
        if IGNORE_ZERO_ARRAYS:
            code.append("# Does not include variable length arrays.")
        struct_keys = self.cheader.structs.keys()
        struct_keys.sort()
        for name in struct_keys:
            struct = self.cheader.structs[name]
            code.append(self.pycode_struct_size(name, struct))
        if GEN_AUX_INFO:
            self.gen_struct_map()

        return code

    def pycode_enum(self, name, enum):
        """Return Python array for enum
        """
        code=[]
        code.append(name+" = "+str(enum))
        ev = []
        for e in enum:
            v = self.cheader.get_value(e)
            ev.append(v)
            code.append(e+"%s= "%_space_to(36,e)+str(v))
        if GEN_ENUM_VALUES_LIST:
            code.append(name+"_values = "+str(ev))
        return code

    def pycode_enum_map(self, name, enum):
        """Return Python dictionary for enum
        """
        code = []
        code.append(name+"_map = {")
        first = 1
        for e in enum:
            v = self.cheader.get_value(e)
            if first:
                prev_e = e
                prev_v = v
                first = 0
            else:
                code.append(self.tab + "%s%s: '%s'," %
                            (prev_v, _space_to(32, str(prev_v)), prev_e))
                prev_e = e
                prev_v = v
        code.append(self.tab + "%s%s: '%s'" %
                            (prev_v, _space_to(32, str(prev_v)), prev_e))
        code.append("}")
        return code

    def pycode_macro(self,name):
        """Return Python dict for macro
        """
        code = []
        if (self.rules.include_macro(name)):
            code.append(name+" = "+str(self.cheader.get_value(name)))
        return code

    def pycode_struct_size(self, name, struct):
        """Return one liner giving the structure size in bytes
        """
        pattern = '!' + self.__c2py.get_pattern(struct)
        bytes = self.__c2py.get_size(pattern)
        code = name.upper() + "_BYTES = " + str(bytes)
        return code

    def pycode_struct(self, struct_in):
        """Return Python class code given C struct.

        Returns None if struct_in is not cheader.cstruct.
        Else return list of strings that codes Python class.
        """
        if (not isinstance(struct_in, cheader.cstruct)):
            return None

        code=[]
        self.__assertcode = []
        code.extend(self.codeheader(struct_in))
        code.extend(self.codeinit(struct_in))
        code.append("")
        code.extend(self.codeassert(struct_in))
        code.append("")
        code.extend(self.codepack(struct_in))
        code.append("")
        code.extend(self.codeunpack(struct_in))
        code.append("")
        code.extend(self.codelen(struct_in))
        code.append("")
        if GEN_OBJ_EQUALITY:
            code.extend(self.codeeq(struct_in))
            code.append("")
        if GEN_OBJ_SHOW:
            code.extend(self.codeshow(struct_in))
            code.append("")
        return code

    def codeheader(self, struct_in):
        """Return Python code for header
        """
        code=[]
        code.append("class "+struct_in.typename+":")
        code.append(self.tab+"\"\"\"Automatically generated Python class for "+struct_in.typename)
        code.append("")
        code.append(self.tab+"Date "+str(datetime.date.today()))
        code.append(self.tab+"Created by "+self.__module__+"."+self.__class__.__name__)
        if IGNORE_OFP_HEADER:
            code.append(self.tab+"Core structure: Messages do not include ofp_header")
        if IGNORE_ZERO_ARRAYS:
            code.append(self.tab+"Does not include var-length arrays")
        code.append(self.tab+"\"\"\"")
        return code

    def codeinit(self, struct_in):
        """Return Python code for init function
        """
        code = []
        code.append(self.tab+"def __init__(self):")
        code.append(self.tab*2+"\"\"\"Initialize")
        code.append(self.tab*2+"Declare members and default values")
        code.append(self.tab*2+"\"\"\"")
        code.extend(self.codemembers(struct_in,self.tab*2+"self"))
        return code

    def codemembers(self, struct_in, prepend=""):
        """Return members of class
        """
        code = []
        for member in struct_in.members:
            if (isinstance(member, cheader.cstruct)):
                code.append(prepend+"."+member.name+" = "+member.typename+"()")
                struct_default = self.rules.get_struct_default(struct_in.typename, member.name)
                if (struct_default != None):
                    code.append(prepend+struct_default)
                self.__structassert(member, (prepend+"."+member.name).strip())
            elif (isinstance(member, cheader.carray)):
                if (member.typename == "char"):
                    initvalue = "\"\""
                    self.__stringassert(member, (prepend+"."+member.name).strip())
                else:
                    if (isinstance(member.object, cheader.cprimitive)):
                        initvalue="0"
                    else:
                        initvalue="None"
                    initvalue=(initvalue+",")*member.size
                    initvalue="["+initvalue[:-1]+"]"
                    self.__arrayassert(member, (prepend+"."+member.name).strip())
                code.append(prepend+"."+member.name+"= "+initvalue)
            else:
                code.append(prepend+"."+member.name+" = "+
                            str(self.rules.get_default_value(struct_in.typename, member.name)))
        return code

    def gen_struct_map(self, file=None):
        if not file:
            file = sys.stdout
        print >> file
        print >> file, "# Class to array member map"
        print >> file, "class_to_members_map = {"
        for name, struct in self.cheader.structs.items():
            if not len(struct.members):
                continue
            s =  "    '" + name + "'"
            print >> file, s + _space_to(36, s) + ": ["
            prev = None
            for member in struct.members:
                if re.search('pad', member.name):
                    continue
                if prev:
                    print _space_to(39, "") + "'" + prev + "',"
                prev = member.name
            print >> file, _space_to(39, "") + "'" + prev + "'"
            print >> file, _space_to(38, "") + "],"
        print >> file, "    '_ignore' : []"
        print >> file, "}"

    def __structassert(self, cstruct, cstructname):
        """Return code to check for C array
        """
        self.__assertcode.append(self.tab*2+"if(not isinstance("+cstructname+", "+cstruct.typename+")):")
        self.__assertcode.append(self.tab*3+"return (False, \""+cstructname+" is not class "+cstruct.typename+" as expected.\")")        

    def __addassert(self, prefix):
        code = []
        code.append(prefix+"if(not self.__assert()[0]):")
        code.append(prefix+self.tab+"return None")        
        return code

    def __stringassert(self, carray, carrayname):
        """Return code to check for C array
        """
        self.__assertcode.append(self.tab*2+"if(not isinstance("+carrayname+", str)):")
        self.__assertcode.append(self.tab*3+"return (False, \""+carrayname+" is not string as expected.\")")        
        self.__assertcode.append(self.tab*2+"if(len("+carrayname+") > "+str(carray.size)+"):")      
        self.__assertcode.append(self.tab*3+"return (False, \""+carrayname+" is not of size "+str(carray.size)+" as expected.\")")

    def __arrayassert(self, carray, carrayname):
        """Return code to check for C array
        """
        if (carray.size == 0):
            return
        self.__assertcode.append(self.tab*2+"if(not isinstance("+carrayname+", list)):")
        self.__assertcode.append(self.tab*3+"return (False, \""+carrayname+" is not list as expected.\")")
        self.__assertcode.append(self.tab*2+"if(len("+carrayname+") != "+str(carray.size)+"):")
        self.__assertcode.append(self.tab*3+"return (False, \""+carrayname+" is not of size "+str(carray.size)+" as expected.\")") 

    def codeassert(self, struct_in):
        """Return code for sanity checking
        """
        code = []
        code.append(self.tab+"def __assert(self):")
        code.append(self.tab*2+"\"\"\"Sanity check")
        code.append(self.tab*2+"\"\"\"")
        enforce = self.rules.get_enforced_map(struct_in.typename)
        if (enforce != None):
            for line in enforce:
                code.append(self.tab*2+line)
        code.extend(self.__assertcode)
        code.append(self.tab*2+"return (True, None)")
        return code

    def codepack(self, struct_in, prefix="!"):
        """Return code that pack struct
        """
        code = []
        code.append(self.tab+"def pack(self, assertstruct=True):")
        code.append(self.tab*2+"\"\"\"Pack message")
        code.append(self.tab*2+"Packs empty array used as placeholder")
        code.append(self.tab*2+"\"\"\"")
        code.append(self.tab*2+"if(assertstruct):")
        code.extend(self.__addassert(self.tab*3))
        code.append(self.tab*2+"packed = \"\"")
        primPattern = ""
        primMemberNames = []
        for member in struct_in.members:
            if (isinstance(member, cheader.cprimitive)):
                #Primitives
                primPattern += self.__c2py.structmap[member.typename]
                primMemberNames.append("self."+member.name)
            else:
                (primPattern, primMemberNames) = \
                              self.__codepackprimitive(code, primPattern,
                                                       primMemberNames, prefix)
                if (isinstance(member, cheader.cstruct)):
                    #Struct
                    code.append(self.tab*2+"packed += self."+member.name+".pack()")
                elif (isinstance(member, cheader.carray) and member.typename == "char"):
                    #String
                    code.append(self.tab*2+"packed += self."+member.name+".ljust("+\
                                str(member.size)+",'\\0')")
                elif (isinstance(member, cheader.carray) and \
                      isinstance(member.object, cheader.cprimitive)):
                    #Array of Primitives
                    expandedarr = ""
                    if (member.size != 0):
                        for x in range(0, member.size):
                            expandedarr += ", self."+member.name+"["+\
                                           str(x).strip()+"]"
                        code.append(self.tab*2+"packed += struct.pack(\""+prefix+\
                                    self.__c2py.structmap[member.object.typename]*member.size+\
                                    "\""+expandedarr+")")
                    else:
                        code.append(self.tab*2+"for i in self."+member.name+":")
                        code.append(self.tab*3+"packed += struct.pack(\""+\
                                    prefix+self.__c2py.get_pattern(member.object)+\
                                    "\",i)")
                elif (isinstance(member, cheader.carray) and \
                      isinstance(member.object, cheader.cstruct)):
                    #Array of struct
                    if (member.size != 0):
                        for x in range(0, member.size):
                            code.append(self.tab*2+"packed += self."+member.name+"["+\
                                        str(x).strip()+"].pack()")
                    else:
                        code.append(self.tab*2+"for i in self."+member.name+":")
                        code.append(self.tab*3+"packed += i.pack(assertstruct)")
        #Clear remaining fields
        (primPattern, primMemberNames) = \
                      self.__codepackprimitive(code, primPattern,
                                               primMemberNames, prefix)
        code.append(self.tab*2+"return packed")
        return code

    def __codepackprimitive(self, code, primPattern, primMemberNames, prefix):
        """Return code for packing primitives
        """
        if (primPattern != ""):
            #Clear prior primitives
            code.append(self.tab*2+"packed += struct.pack(\""+\
                        prefix+primPattern+"\", "+\
                        str(primMemberNames).replace("'","")[1:-1]+")")
        return ("",[])

    def codelen(self, struct_in):
        """Return code to return length
        """
        pattern = "!" + self.__c2py.get_pattern(struct_in)
        code = []
        code.append(self.tab+"def __len__(self):")
        code.append(self.tab*2+"\"\"\"Return length of message")
        code.append(self.tab*2+"\"\"\"")
        code.append(self.tab*2+"l = "+str(self.__c2py.get_size(pattern)))
        for member in struct_in.members:
            if (isinstance(member, cheader.carray) and member.size == 0):
                if (isinstance(member.object, cheader.cstruct)):
                    code.append(self.tab*2+"for i in self."+member.name+":")
                    # FIXME:  Is this right?  Doesn't seem to be called
                    code.append(self.tab*3+"l += i.length()")
                else:
                    pattern="!"+self.__c2py.get_pattern(member.object)
                    size=self.__c2py.get_size(pattern)
                    code.append(self.tab*2+"l += len(self."+member.name+")*"+str(size))
        code.append(self.tab*2+"return l")
        return code

    def codeeq(self, struct_in):
        """Return code to return equality comparisons
        """
        code = []
        code.append(self.tab+"def __eq__(self, other):")
        code.append(self.tab*2+"\"\"\"Return True if self and other have same values")
        code.append(self.tab*2+"\"\"\"")
        code.append(self.tab*2+"if type(self) != type(other): return False")
        for member in struct_in.members:
            code.append(self.tab*2 + "if self." + member.name + " !=  other." +
                        member.name + ": return False")
        code.append(self.tab*2+"return True")
        code.append("")
        code.append(self.tab+"def __ne__(self, other): return not self.__eq__(other)")
        return code

    def codeshow(self, struct_in):
        """Return code to print basic members of structure
        """
        code = []
        code.append(self.tab+"def show(self, prefix=''):")
        code.append(self.tab*2+"\"\"\"" + "Generate string showing basic members of structure")
        code.append(self.tab*2+"\"\"\"")
        code.append(self.tab*2+"outstr = ''")
        for member in struct_in.members:
            if re.search('pad', member.name):
                continue
            elif (isinstance(member, cheader.cstruct)):
                code.append(self.tab*2 + "outstr += prefix + '" + 
                            member.name + ": \\n' ")
                code.append(self.tab*2 + "outstr += self." + member.name + 
                            ".show(prefix + '  ')")
            elif (isinstance(member, cheader.carray) and
                  not isinstance(member.object, cheader.cprimitive)):
                code.append(self.tab*2 + "outstr += prefix + '" + member.name +
                            ": \\n' ")
                code.append(self.tab*2 + "for obj in self." + member.name + ":")
                code.append(self.tab*3 + "outstr += obj.show(prefix + '  ')")
            else:
                code.append(self.tab*2 + "outstr += prefix + '" + member.name +
                            ": ' + str(self." + member.name + ") + '\\n'")
        code.append(self.tab*2+"return outstr")
        return code

    def codeunpack(self, struct_in, prefix="!"):
        """Return code that unpack struct
        """
        pattern = self.__c2py.get_pattern(struct_in)
        structlen = self.__c2py.get_size(prefix + pattern)
        code = []
        code.append(self.tab+"def unpack(self, binaryString):")
        code.append(self.tab*2+"\"\"\"Unpack message")
        code.append(self.tab*2+"Do not unpack empty array used as placeholder")
        code.append(self.tab*2+"since they can contain heterogeneous type")
        code.append(self.tab*2+"\"\"\"")
        code.append(self.tab*2+"if (len(binaryString) < "+str(structlen)+"):")
        code.append(self.tab*3+"return binaryString")
        offset = 0
        primPattern = ""
        primMemberNames = []
        for member in struct_in.members:
            if (isinstance(member, cheader.cprimitive)):
                #Primitives
                primPattern += self.__c2py.structmap[member.typename]
                primMemberNames.append("self."+member.name)
            else:
                (primPattern, primMemberNames, offset) = \
                              self.__codeunpackprimitive(code, offset, primPattern,
                                                         primMemberNames, prefix)
                if (isinstance(member, cheader.cstruct)):
                    #Struct
                    code.append(self.tab*2+"self."+member.name+\
                                ".unpack(binaryString["+str(offset)+":])")
                    pattern = self.__c2py.get_pattern(member)
                    offset += self.__c2py.get_size(prefix+pattern)
                elif (isinstance(member, cheader.carray) and member.typename == "char"):
                    #String
                    code.append(self.tab*2+"self."+member.name+\
                                " = binaryString["+str(offset)+":"+\
                                str(offset+member.size)+"].replace(\"\\0\",\"\")")
                    offset += member.size
                elif (isinstance(member, cheader.carray) and \
                      isinstance(member.object, cheader.cprimitive)):
                    #Array of Primitives
                    expandedarr = ""
                    if (member.size != 0):
                        arrpattern = self.__c2py.structmap[member.object.typename]*member.size
                        for x in range(0, member.size):
                            expandedarr += "self."+member.name+"["+\
                                           str(x).strip()+"], "
                        code.append(self.tab*2 + "fmt = '" + prefix+arrpattern + "'")
                        code.append(self.tab*2 + "start = " + str(offset))
                        code.append(self.tab*2 + "end = start + struct.calcsize(fmt)")
                        code.append(self.tab*2 + "("+expandedarr[:-2] + 
                                    ") = struct.unpack(fmt, binaryString[start:end])")
                        offset += struct.calcsize(prefix + arrpattern)
                elif (isinstance(member, cheader.carray) and \
                      isinstance(member.object, cheader.cstruct)):
                    #Array of struct
                    astructlen = self.__c2py.get_size("!"+self.__c2py.get_pattern(member.object))
                    for x in range(0, member.size):
                        code.append(self.tab*2+"self."+member.name+"["+str(x)+"]"+\
                                ".unpack(binaryString["+str(offset)+":])")
                        offset += astructlen
        #Clear remaining fields
        (primPattern, primMemberNames, offset) = \
                      self.__codeunpackprimitive(code, offset, primPattern,
                                                 primMemberNames, prefix)
        code.append(self.tab*2+"return binaryString["+str(structlen)+":]");
        return code

    def __codeunpackprimitive(self, code, offset, primPattern,
                              primMemberNames, prefix):
        """Return code for unpacking primitives
        """
        if (primPattern != ""):
            #Clear prior primitives
            code.append(self.tab*2 + "fmt = '" + prefix + primPattern + "'")
            code.append(self.tab*2 + "start = " + str(offset))
            code.append(self.tab*2 + "end = start + struct.calcsize(fmt)")
            if len(primMemberNames) == 1:
                code.append(self.tab*2 + "(" + str(primMemberNames[0]) + 
                            ",) = struct.unpack(fmt, binaryString[start:end])")
            else:
                code.append(self.tab*2+"("+str(primMemberNames).replace("'","")[1:-1]+
                            ") = struct.unpack(fmt,  binaryString[start:end])")

        return ("",[], offset+struct.calcsize(prefix+primPattern))

