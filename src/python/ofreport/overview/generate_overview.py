# Removes *.html files and then generates new ones based on
# ../spec/spec.json
from subprocess import call
import json

f = open('../spec/spec.json')
j = json.loads(f.read())
f.close()

call('rm *.html', shell=True)

for k, v in j.iteritems():
    f = open(k+'.html', 'w')
    f.write(v[u'purpose'].encode('utf8'))
