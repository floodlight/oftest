# Copyright (c) 2008 The Board of Trustees of The Leland Stanford Junior University
# Copyright (c) 2011, 2012 Open Networking Foundation
# Copyright (c) 2012, 2013 Big Switch Networks, Inc.
# See the file LICENSE.pyloxi which should have been included in the source distribution

# Automatically generated by LOXI from template action.py
# Do not modify

import struct
import const
import util
import loxi.generic_util
import loxi

def unpack_list(reader):
    def deserializer(reader, typ):
        parser = parsers.get(typ)
        if not parser: raise loxi.ProtocolError("unknown action type %d" % typ)
        return parser(reader)
    return loxi.generic_util.unpack_list_tlv16(reader, deserializer)

class Action(object):
    type = None # override in subclass
    pass

class bsn_mirror(Action):
    type = 65535
    experimenter = 6035143
    subtype = 1

    def __init__(self, dest_port=None, vlan_tag=None, copy_stage=None):
        if dest_port != None:
            self.dest_port = dest_port
        else:
            self.dest_port = 0
        if vlan_tag != None:
            self.vlan_tag = vlan_tag
        else:
            self.vlan_tag = 0
        if copy_stage != None:
            self.copy_stage = copy_stage
        else:
            self.copy_stage = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!L", self.experimenter))
        packed.append(struct.pack("!L", self.subtype))
        packed.append(struct.pack("!L", self.dest_port))
        packed.append(struct.pack("!L", self.vlan_tag))
        packed.append(struct.pack("!B", self.copy_stage))
        packed.append('\x00' * 3)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = bsn_mirror()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 65535)
        _len = reader.read("!H")[0]
        _experimenter = reader.read("!L")[0]
        assert(_experimenter == 6035143)
        _subtype = reader.read("!L")[0]
        assert(_subtype == 1)
        obj.dest_port = reader.read("!L")[0]
        obj.vlan_tag = reader.read("!L")[0]
        obj.copy_stage = reader.read("!B")[0]
        reader.skip(3)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.dest_port != other.dest_port: return False
        if self.vlan_tag != other.vlan_tag: return False
        if self.copy_stage != other.copy_stage: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("bsn_mirror {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("dest_port = ");
                q.text("%#x" % self.dest_port)
                q.text(","); q.breakable()
                q.text("vlan_tag = ");
                q.text("%#x" % self.vlan_tag)
                q.text(","); q.breakable()
                q.text("copy_stage = ");
                q.text("%#x" % self.copy_stage)
            q.breakable()
        q.text('}')

class bsn_set_tunnel_dst(Action):
    type = 65535
    experimenter = 6035143
    subtype = 2

    def __init__(self, dst=None):
        if dst != None:
            self.dst = dst
        else:
            self.dst = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!L", self.experimenter))
        packed.append(struct.pack("!L", self.subtype))
        packed.append(struct.pack("!L", self.dst))
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = bsn_set_tunnel_dst()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 65535)
        _len = reader.read("!H")[0]
        _experimenter = reader.read("!L")[0]
        assert(_experimenter == 6035143)
        _subtype = reader.read("!L")[0]
        assert(_subtype == 2)
        obj.dst = reader.read("!L")[0]
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.dst != other.dst: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("bsn_set_tunnel_dst {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("dst = ");
                q.text("%#x" % self.dst)
            q.breakable()
        q.text('}')

class copy_ttl_in(Action):
    type = 12

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = copy_ttl_in()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 12)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("copy_ttl_in {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class copy_ttl_out(Action):
    type = 11

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = copy_ttl_out()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 11)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("copy_ttl_out {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class dec_mpls_ttl(Action):
    type = 16

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = dec_mpls_ttl()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 16)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("dec_mpls_ttl {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class dec_nw_ttl(Action):
    type = 24

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = dec_nw_ttl()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 24)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("dec_nw_ttl {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class group(Action):
    type = 22

    def __init__(self, group_id=None):
        if group_id != None:
            self.group_id = group_id
        else:
            self.group_id = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!L", self.group_id))
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = group()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 22)
        _len = reader.read("!H")[0]
        obj.group_id = reader.read("!L")[0]
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.group_id != other.group_id: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("group {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("group_id = ");
                q.text("%#x" % self.group_id)
            q.breakable()
        q.text('}')

class nicira_dec_ttl(Action):
    type = 65535
    experimenter = 8992
    subtype = 18

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!L", self.experimenter))
        packed.append(struct.pack("!H", self.subtype))
        packed.append('\x00' * 2)
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = nicira_dec_ttl()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 65535)
        _len = reader.read("!H")[0]
        _experimenter = reader.read("!L")[0]
        assert(_experimenter == 8992)
        _subtype = reader.read("!H")[0]
        assert(_subtype == 18)
        reader.skip(2)
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("nicira_dec_ttl {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class output(Action):
    type = 0

    def __init__(self, port=None, max_len=None):
        if port != None:
            self.port = port
        else:
            self.port = 0
        if max_len != None:
            self.max_len = max_len
        else:
            self.max_len = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(util.pack_port_no(self.port))
        packed.append(struct.pack("!H", self.max_len))
        packed.append('\x00' * 6)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = output()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 0)
        _len = reader.read("!H")[0]
        obj.port = util.unpack_port_no(reader)
        obj.max_len = reader.read("!H")[0]
        reader.skip(6)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.port != other.port: return False
        if self.max_len != other.max_len: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("output {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("port = ");
                q.text(util.pretty_port(self.port))
                q.text(","); q.breakable()
                q.text("max_len = ");
                q.text("%#x" % self.max_len)
            q.breakable()
        q.text('}')

class pop_mpls(Action):
    type = 20

    def __init__(self, ethertype=None):
        if ethertype != None:
            self.ethertype = ethertype
        else:
            self.ethertype = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!H", self.ethertype))
        packed.append('\x00' * 2)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = pop_mpls()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 20)
        _len = reader.read("!H")[0]
        obj.ethertype = reader.read("!H")[0]
        reader.skip(2)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.ethertype != other.ethertype: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("pop_mpls {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("ethertype = ");
                q.text("%#x" % self.ethertype)
            q.breakable()
        q.text('}')

class pop_pbb(Action):
    type = 27

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = pop_pbb()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 27)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("pop_pbb {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class pop_vlan(Action):
    type = 18

    def __init__(self):
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append('\x00' * 4)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = pop_vlan()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 18)
        _len = reader.read("!H")[0]
        reader.skip(4)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("pop_vlan {")
        with q.group():
            with q.indent(2):
                q.breakable()
            q.breakable()
        q.text('}')

class push_mpls(Action):
    type = 19

    def __init__(self, ethertype=None):
        if ethertype != None:
            self.ethertype = ethertype
        else:
            self.ethertype = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!H", self.ethertype))
        packed.append('\x00' * 2)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = push_mpls()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 19)
        _len = reader.read("!H")[0]
        obj.ethertype = reader.read("!H")[0]
        reader.skip(2)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.ethertype != other.ethertype: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("push_mpls {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("ethertype = ");
                q.text("%#x" % self.ethertype)
            q.breakable()
        q.text('}')

class push_pbb(Action):
    type = 26

    def __init__(self, ethertype=None):
        if ethertype != None:
            self.ethertype = ethertype
        else:
            self.ethertype = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!H", self.ethertype))
        packed.append('\x00' * 2)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = push_pbb()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 26)
        _len = reader.read("!H")[0]
        obj.ethertype = reader.read("!H")[0]
        reader.skip(2)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.ethertype != other.ethertype: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("push_pbb {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("ethertype = ");
                q.text("%#x" % self.ethertype)
            q.breakable()
        q.text('}')

class push_vlan(Action):
    type = 17

    def __init__(self, ethertype=None):
        if ethertype != None:
            self.ethertype = ethertype
        else:
            self.ethertype = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!H", self.ethertype))
        packed.append('\x00' * 2)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = push_vlan()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 17)
        _len = reader.read("!H")[0]
        obj.ethertype = reader.read("!H")[0]
        reader.skip(2)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.ethertype != other.ethertype: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("push_vlan {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("ethertype = ");
                q.text("%#x" % self.ethertype)
            q.breakable()
        q.text('}')

class set_field(Action):
    type = 25

    def __init__(self, field=None):
        if field != None:
            self.field = field
        else:
            self.field = ''
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(self.field)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = set_field()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 25)
        _len = reader.read("!H")[0]
        obj.field = str(reader.read_all())
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.field != other.field: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("set_field {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("field = ");
                q.pp(self.field)
            q.breakable()
        q.text('}')

class set_mpls_ttl(Action):
    type = 15

    def __init__(self, mpls_ttl=None):
        if mpls_ttl != None:
            self.mpls_ttl = mpls_ttl
        else:
            self.mpls_ttl = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!B", self.mpls_ttl))
        packed.append('\x00' * 3)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = set_mpls_ttl()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 15)
        _len = reader.read("!H")[0]
        obj.mpls_ttl = reader.read("!B")[0]
        reader.skip(3)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.mpls_ttl != other.mpls_ttl: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("set_mpls_ttl {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("mpls_ttl = ");
                q.text("%#x" % self.mpls_ttl)
            q.breakable()
        q.text('}')

class set_nw_ttl(Action):
    type = 23

    def __init__(self, nw_ttl=None):
        if nw_ttl != None:
            self.nw_ttl = nw_ttl
        else:
            self.nw_ttl = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!B", self.nw_ttl))
        packed.append('\x00' * 3)
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = set_nw_ttl()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 23)
        _len = reader.read("!H")[0]
        obj.nw_ttl = reader.read("!B")[0]
        reader.skip(3)
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.nw_ttl != other.nw_ttl: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("set_nw_ttl {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("nw_ttl = ");
                q.text("%#x" % self.nw_ttl)
            q.breakable()
        q.text('}')

class set_queue(Action):
    type = 21

    def __init__(self, queue_id=None):
        if queue_id != None:
            self.queue_id = queue_id
        else:
            self.queue_id = 0
        return

    def pack(self):
        packed = []
        packed.append(struct.pack("!H", self.type))
        packed.append(struct.pack("!H", 0)) # placeholder for len at index 1
        packed.append(struct.pack("!L", self.queue_id))
        length = sum([len(x) for x in packed])
        packed[1] = struct.pack("!H", length)
        return ''.join(packed)

    @staticmethod
    def unpack(buf):
        obj = set_queue()
        if type(buf) == loxi.generic_util.OFReader:
            reader = buf
        else:
            reader = loxi.generic_util.OFReader(buf)
        _type = reader.read("!H")[0]
        assert(_type == 21)
        _len = reader.read("!H")[0]
        obj.queue_id = reader.read("!L")[0]
        return obj

    def __eq__(self, other):
        if type(self) != type(other): return False
        if self.queue_id != other.queue_id: return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def show(self):
        import loxi.pp
        return loxi.pp.pp(self)

    def pretty_print(self, q):
        q.text("set_queue {")
        with q.group():
            with q.indent(2):
                q.breakable()
                q.text("queue_id = ");
                q.text("%#x" % self.queue_id)
            q.breakable()
        q.text('}')


def parse_experimenter(reader):

    experimenter, = reader.peek("!4xL")
    if experimenter == 0x005c16c7: # Big Switch Networks
        subtype, = reader.peek("!8xL")
    elif experimenter == 0x00002320: # Nicira
        subtype, = reader.peek("!8xH")
    else:
        raise loxi.ProtocolError("unexpected experimenter id %#x" % experimenter)

    if subtype in experimenter_parsers[experimenter]:
        return experimenter_parsers[experimenter][subtype](reader)
    else:
        raise loxi.ProtocolError("unexpected BSN experimenter subtype %#x" % subtype)

parsers = {
    const.OFPAT_OUTPUT : output.unpack,
    const.OFPAT_COPY_TTL_OUT : copy_ttl_out.unpack,
    const.OFPAT_COPY_TTL_IN : copy_ttl_in.unpack,
    const.OFPAT_SET_MPLS_TTL : set_mpls_ttl.unpack,
    const.OFPAT_DEC_MPLS_TTL : dec_mpls_ttl.unpack,
    const.OFPAT_PUSH_VLAN : push_vlan.unpack,
    const.OFPAT_POP_VLAN : pop_vlan.unpack,
    const.OFPAT_PUSH_MPLS : push_mpls.unpack,
    const.OFPAT_POP_MPLS : pop_mpls.unpack,
    const.OFPAT_SET_QUEUE : set_queue.unpack,
    const.OFPAT_GROUP : group.unpack,
    const.OFPAT_SET_NW_TTL : set_nw_ttl.unpack,
    const.OFPAT_DEC_NW_TTL : dec_nw_ttl.unpack,
    const.OFPAT_SET_FIELD : set_field.unpack,
    const.OFPAT_PUSH_PBB : push_pbb.unpack,
    const.OFPAT_POP_PBB : pop_pbb.unpack,
    const.OFPAT_EXPERIMENTER : parse_experimenter,
}

experimenter_parsers = {
    8992 : {
        18: nicira_dec_ttl.unpack,
    },
    6035143 : {
        1: bsn_mirror.unpack,
        2: bsn_set_tunnel_dst.unpack,
    },
}
