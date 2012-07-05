
"""
Base list class for inheritance.
Most of the list stuff is common; unpacking is the only thing that
is left pure virtual.
"""

import copy

class ofp_base_list(object):
    """
    Container type to maintain a list of ofp objects

    Data members:
    @arg items An array of objects
    @arg class_list A tuple of classes that may be added to the list;
         If None, no checking is done
    @arg name The name to use when displaying the list

    Methods:
    @arg pack Pack the structure into a string
    @arg unpack Unpack a string to objects, with proper typing
    @arg add Add an item to the list; you can directly access
    the item member, but add will validate that the added object 
    is of the right type.
    @arg extend Add the items for another list to this list

    """

    def __init__(self):
        self.items = []
        self.class_list = None
        self.name = "unspecified"

    def pack(self):
        """
        Pack a list of items

        Returns the packed string
        """
        packed = ""
        for obj in self.items:
            packed += obj.pack()
        return packed

    def unpack(self, binary_string, bytes=None):
        """
        Pure virtual function for a list of items

        Unpack items from a binary string, creating an array
        of objects of the appropriate type

        @param binary_string The string to be unpacked

        @param bytes The total length of the list in bytes.  
        Ignored if decode is True.  If None and decode is false, the
        list is assumed to extend through the entire string.

        @return The remainder of binary_string that was not parsed
        """
        pass

    def add(self, item):
        """
        Add an item to a list

        @param item The item to add
        @return True if successful, False if not proper type object

        """

        # Note that the second arg of isinstance can be a list which
        # checks that the type of item is in the list
        if (self.class_list is not None) and \
                not isinstance(item, tuple(self.class_list)):
            return False

        tmp = copy.deepcopy(item)
        self.items.append(tmp)
        return True

    def remove_type(self, target):
        """
        Remove the first item on the list of the given type

        @param target The type of item to search

        @return The object removed, if any; otherwise None

        """
        for index in xrange(len(self.items)):
            if self.items[index].type == target:
                return self.items.pop(index)
        return None

    def find_type(self, target):
        """
        Find the first item on the list of the given type

        @param target The type of item to search

        @return The object with the matching type if any; otherwise None

        """
        for index in xrange(len(self.items)):
            if self.items[index].type == target:
                return self.items[index]
        return None

    def extend(self, other):
        """
        Add the items in other to this list

        @param other An object of the same type of list whose
        entries are to be merged into this list

        @return True if successful.  If not successful, the list
        may have been modified.

        @todo Check if this is proper deep copy or not

        """
        for act in other.items:
            if not self.add(act):
                return False
        return True

    def __len__(self):
        """
        Length of the list packed as a string
        """
        length = 0
        for item in self.items:
            length += item.__len__()
        return length

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.items != other.items:
            return False
        return True

    def __ne__(self, other): return not self.__eq__(other)

    # Methods to make class iterable
    def __iter__(self):
        return self.items.__iter__()

    def show(self, prefix=''):
        outstr = prefix + self.name + "list with " + str(len(self.items)) + \
            " items\n"
        count = 0
        for obj in self.items:
            count += 1
            outstr += prefix + " " + self.name + " " + str(count) + ": \n"
            outstr += obj.show(prefix + '    ')
        return outstr
