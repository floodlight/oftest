"""This module parse and store a C/C++ header file.

Date June 2009
Created by ykk
"""
import re
from config import *

class textfile:
    """Class to handle text file.
    
    Date June 2009
    Created by ykk
    """
    def __init__(self, filename):
        """Initialize filename with no content.
        """
        ##Filename
        if (isinstance(filename, str)):
            self.filename = []
            self.filename.append(filename)
        else:
            self.filename = filename
        ##Content
        self.content = []

    def read(self):
        """Read file
        """
        for filename in self.filename:
            fileRef = open(filename, "r")
            for line in fileRef:
                self.content.append(line)
            fileRef.close()        

class ctype:
    """Class to represent types in C
    """
    def __init__(self,typename, name=None, expanded=False):
        """Initialize
        """
        ##Name
        self.name = name
        ##Type of primitive
        self.typename = typename
        ##Expanded
        self.expanded = expanded

    def expand(self, cheader):
        """Expand type if applicable
        """
        raise NotImplementedError()

    def get_names(self):
        """Return name of variables
        """
        raise NotImplementedError()

class cprimitive(ctype):
    """Class to represent C primitive

    Date October 2009
    Created by ykk
    """
    def __init__(self,typename, name=None):
        """Initialize and store primitive
        """
        ctype.__init__(self, typename, name, True)

    def __str__(self):
        """Return string representation
        """
        if (self.name == None):
            return self.typename
        else:
            return self.typename+" "+str(self.name)

    def expand(self, cheader):
        """Expand type if applicable
        """
        pass
    
    def get_names(self):
        """Return name of variables
        """
        namelist = []
        namelist.append(self.name)
        return namelist

class cstruct(ctype):
    """Class to represent C struct

    Date October 2009
    Created by ykk
    """
    def __init__(self, typename, name=None):
        """Initialize struct
        """
        ctype.__init__(self, typename, name)
        ##List of members in struct
        self.members = []
    
    def __str__(self):
        """Return string representation
        """
        string = "struct "+self.typename
        if (self.name != None):
            string += " "+self.name
        if (len(self.members) == 0):
            return string
        #Add members
        string +=" {\n"
        for member in self.members:
            string += "\t"+str(member)
            if (not isinstance(member, cstruct)):
                string += ";"
            string += "\n"
        string +="};"
        return string

    def expand(self, cheader):
        """Expand struct
        """
        self.expanded = True
        #Expanded each member
        for member in self.members:
            if (isinstance(member, cstruct) and 
                (not member.expanded)):
                try:
                    if (not cheader.structs[member.typename].expanded):
                        cheader.structs[member.typename].expand(cheader)
                    member.members=cheader.structs[member.typename].members[:]
                    member.expanded = True
                except KeyError:
                    self.expanded=False
            else:
                member.expand(cheader)

    def get_names(self):
        """Return name of variables
        """
        namelist = []
        for member in self.members:
            if (isinstance(member, cstruct)):
                tmplist = member.get_names()
                for item in tmplist:
                    namelist.append(member.name+"."+item)
            else:
                namelist.extend(member.get_names())
        return namelist


class carray(ctype):
    """Class to represent C array

    Date October 2009
    Created by ykk
    """
    def __init__(self, typename, name, isPrimitive, size):
        """Initialize array of object.
        """
        ctype.__init__(self, typename, name,
                       (isinstance(size, int) and isPrimitive))
        ##Object reference
        if (isPrimitive):
            self.object = cprimitive(typename, name)
        else:
            self.object = cstruct(typename, name)
        ##Size of array
        self.size = size
        
    def __str__(self):
        """Return string representation
        """
        return str(self.object)+"["+str(self.size)+"]"

    def expand(self, cheader):
        """Expand array
        """
        self.expanded = True
        if (not self.object.expanded):
            if (isinstance(self.object, cstruct)):
                cheader.structs[self.object.typename].expand(cheader)
                self.object.members=cheader.structs[self.object.typename].members[:]    
            else:
                self.object.expand(cheader)

        if (not isinstance(self.size, int)):
            val = cheader.get_value(self.size)
            if (val == None):
                self.expanded = False
            else:
                try:
                    self.size = int(val)
                except ValueError:
                    self.size = val
                    self.expanded = False

    def get_names(self):
        """Return name of variables
        """
        namelist = []
        for i in range(0,self.size):
            namelist.append(self.object.name)
        return namelist

class ctype_parser:
    """Class to check c types

    Date October 2009
    Created by ykk
    """
    def __init__(self):
        """Initialize
        """
        self.CPrimitives = ["char","signed char","unsigned char",
                            "short","unsigned short",
                            "int","unsigned int",
                            "long","unsigned long",
                            "long long","unsigned long long",
                            "float","double",
                            "uint8_t","uint16_t","uint32_t","uint64_t"]

    def is_primitive(self,type):
        """Check type given is primitive.

        Return true if valid, and false otherwise
        """
        if (type in self.CPrimitives):
            return True
        else:
            return False

    def is_array(self, string):
        """Check if string declares an array
        """
        parts=string.strip().split()
        if (len(parts) <= 1):
            return False
        else:
            pattern = re.compile("\[.*?\]", re.MULTILINE)
            values = pattern.findall(string)
            if (len(values) == 1):
                return True
            else:
                return False

    def parse_array(self, string):
        """Parse array from string.
        Return occurrence and name.
        """
        pattern = re.compile("\[.*?\]", re.MULTILINE)
        namepattern = re.compile(".*?\[", re.MULTILINE)
        values = pattern.findall(string)
        if (len(values) != 1):
            return (1,string)
        else:
            val = values[0][1:-1]
            try:
                sizeval = int(val)
            except ValueError:
                if (val==""):
                    sizeval = 0
                else:
                    sizeval = val
            return (sizeval,
                    namepattern.findall(string)[0].strip()[0:-1])

    def parse_type(self, string):
        """Parse string and return cstruct or cprimitive.
        Else return None
        """
        parts=string.strip().split()
        if (len(parts) >= 2):
            if (parts[0].strip() == "struct"):
                typename = " ".join(parts[1:-1])
            else:
                typename = " ".join(parts[:-1])
            (size, name) = self.parse_array(parts[-1])
            if IGNORE_ZERO_ARRAYS and size == 0:
                return None
            #Create appropriate type
            if (size != 1):
                #Array
                return carray(typename, name, 
                              self.is_primitive(typename),size)
            else:
                #Not array
                if typename == "ofp_header":
                    return "ofp_header"
                if (self.is_primitive(typename)):
                    return cprimitive(typename, name)
                else:
                    return cstruct(typename, name)
        else:
            return None

class cheaderfile(textfile):
    """Class to handle C header file.
    
    Date June 2009
    Created by ykk
    """
    def __init__(self, filename):
        """Initialize filename and read from file
        """
        textfile.__init__(self,filename)
        self.read()
        self.__remove_comments()
        ##Dictionary of macros
        self.macros = {}
        self.__get_macros()
        ##Dictionary of enumerations
        self.enums = {}
        self.enum_values = {}
        self.__get_enum()
        self.__get_enum_values()
        ##Dictionary of structs
        self.structs = {}
        self.__get_struct()

    def get_enum_name(self, enum, value):
        """Return name of variable in enum
        """
        for e in self.enums[enum]:
            if (self.enum_values[e] == value):
                return e

    def eval_value(self, value):
        """Evaluate value string
        """
        try:
            return eval(value, self.enum_values)
        except:
            return value.strip()

    def get_value(self, name):
        """Get value for variable name,
        searching through enum and macros.
        Else return None
        """
        try:
            return self.enum_values[name]
        except KeyError:
            try:
                return self.macros[name]
            except KeyError:
                return None

    def __remove_comments(self):
        """Remove all comments
        """
        fileStr = "".join(self.content)
        pattern = re.compile("\\\.*?\n", re.MULTILINE)
        fileStr = pattern.sub("",fileStr)
        pattern = re.compile(r"/\*.*?\*/", re.MULTILINE|re.DOTALL)
        fileStr = pattern.sub("",fileStr)
        pattern = re.compile("//.*$", re.MULTILINE)
        fileStr = pattern.sub("",fileStr)
        self.content = fileStr.split('\n')

    def __get_struct(self):
        """Get all structs
        """
        typeparser = ctype_parser()
        fileStr = "".join(self.content)
        #Remove attribute
        attrpattern = re.compile("} __attribute__ \(\((.+?)\)\);", re.MULTILINE)
        attrmatches = attrpattern.findall(fileStr)
        for amatch in attrmatches:
            fileStr=fileStr.replace(" __attribute__ (("+amatch+"));",";")
        #Find all structs
        pattern = re.compile("struct[\w\s]*?{.*?};", re.MULTILINE)
        matches = pattern.findall(fileStr)
        #Process each struct
        namepattern = re.compile("struct(.+?)[ {]", re.MULTILINE)
        pattern = re.compile("{(.+?)};", re.MULTILINE)
        for match in matches:
            structname = namepattern.findall(match)[0].strip()
            if (len(structname) != 0):
                values = pattern.findall(match)[0].strip().split(";")
                cstru = cstruct(structname)
                for val in values:
                    presult = typeparser.parse_type(val)
                    if presult == "ofp_header":
                        cstru.members.append(cprimitive("uint8_t", "version"))
                        cstru.members.append(cprimitive("uint8_t", "type"))
                        cstru.members.append(cprimitive("uint16_t", "length"))
                        cstru.members.append(cprimitive("uint32_t", "xid"))
                    elif (presult != None):
                        cstru.members.append(presult)
                self.structs[structname] = cstru
        #Expand all structs
        for (structname, struct) in self.structs.items():
            struct.expand(self)

    def __get_enum(self):
        """Get all enumeration
        """
        fileStr = "".join(self.content)
        #Find all enumerations
        pattern = re.compile("enum[\w\s]*?{.*?}", re.MULTILINE)
        matches = pattern.findall(fileStr)
        #Process each enumeration
        namepattern = re.compile("enum(.+?){", re.MULTILINE)
        pattern = re.compile("{(.+?)}", re.MULTILINE)
        for match in matches:
            values = pattern.findall(match)[0].strip().split(",")
            #Process each value in enumeration
            enumList = []
            value = 0
            for val in values:
                if not (val.strip() == ""):
                    valList=val.strip().split("=")
                    enumList.append(valList[0].strip())
                    if (len(valList) == 1):
                        self.enum_values[valList[0].strip()] = value
                        value += 1
                    else:
                        self.enum_values[valList[0].strip()] = self.eval_value(valList[1].strip())
                    self.enums[namepattern.findall(match)[0].strip()] = enumList

    def __get_enum_values(self):
        """Patch unresolved enum values
        """
        for name,enumval in self.enum_values.items():
            if isinstance(enumval,str):
                self.enum_values[name] = self.eval_value(enumval)
        
    def __get_macros(self):
        """Extract macros
        """
        for line in self.content:
            if (line[0:8] == "#define "):
                lineList = line[8:].split()
                if (len(lineList) >= 2):
                    self.macros[lineList[0]] = self.eval_value("".join(lineList[1:]))
                else:
                    self.macros[lineList[0]] = ""
