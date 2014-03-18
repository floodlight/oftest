# A stuipd parser...
import json

class OfpTest(object):
    def __init__(self, name=""):
        self.name = name
        self.number = ''
        self.title = ''
        self.purpose = ''
        self.reference = ''
        self.status = ''
        self.requirements = ''
        self.topology = ''
        self.methodology = ''
        self.results = ''
        self.remarks = ''

    def __str__(self):
        s = ''
        s += 'Name: ' + self.name + '\n'
        s += 'Number: ' + self.number + '\n'
        s += 'Title: ' + self.title + '\n'
        s += 'Purpose: ' + self.purpose + '\n'
        s += 'Reference: ' + self.reference + '\n'
        s += 'Status: ' + self.status + '\n'
        s += 'Requirements: ' + self.requirements + '\n'
        s += 'Topology: ' + self.topology + '\n'
        s += 'Methodology: ' + self.methodology + '\n'
        s += 'Results: ' + self.results + '\n'
        s += 'Remarks: ' + self.remarks + '\n'
        s += '\n'
        return s

    def as_json(self):
        result = {}
        result['name'] = self.name

        m = self.number.split('.')
        result['number'] = 'Grp{}No{}'.format(m[0], m[1])
        result['title'] = self.title
        result['purpose'] = self.purpose
        result['ref'] = self.reference

        if 'MANDATORY' in self.status and 'L2' in self.status:
            result['status'] = 'L2'
        elif 'MANDATORY' in self.status and 'L3' in self.status:
            result['status'] = 'L3'
        elif 'MANDATORY' in self.status and 'ALL' in self.status:
            result['status'] = 'ALL'
        else:
            result['status'] = ''
        result['req'] = self.requirements
        result['topo'] = self.topology
        result['method'] = self.methodology
        result['results'] = self.results
        result['remarks'] = self.remarks
        return result

f = open('text.txt')

result = {}

while True:
    line = f.readline()
    if line == '': break

    # Name
    if line[:9] == 'Test case':
        t = OfpTest()
        s = ''

        t.name = line.split(':')[1].strip('\n ')
        end = False
        while not end:
            l = f.readline().strip('\n ')
            # TestNo
            if l == 'Test Number':
                t.number = f.readline().strip('\n ')
            # Title
            elif l == 'Test Title':
                t.title = f.readline().strip('\n ')
            # Purpose
            elif l == 'Test Purpose':
                t.title += s
                s = ''
                t.purpose = f.readline().strip('\n ')
            # Reference
            elif l == 'Specification Reference':
                t.purpose += s
                s = ''
                t.reference = f.readline().strip('\n ')
            # Status
            elif l == 'Profile Status':
                t.reference += s
                s = ''
                t.status = f.readline().strip('\n ')
            # Requirements
            elif l == 'Requirements':
                t.status += s
                s = ''
                t.requirements = f.readline().strip('\n ')
            # Topology
            elif l == 'Topology':
                t.requirements += s
                s = ''
                t.topology = f.readline().strip('\n ')
            # Methodology
            elif l == 'Methodology':
                t.topology += s
                s = ''
                t.methodology = f.readline().strip('\n ')
            # Results
            elif l == 'Results':
                t.methodology += s
                s = ''
                t.results = f.readline().strip('\n ')
            # Remarks
            elif l == 'Remarks':
                t.results += s
                s = ''
                t.remarks = f.readline().strip('\n ')
                end = True
            else:
                if l is not '':
                    s += l
        t.remarks += s
        json_txt = t.as_json()
        result[json_txt['number']] = json_txt

f.close()

g = open('spec.json', 'w')
g.write(json.dumps(result))
g.close()
