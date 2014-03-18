
from xlrd import open_workbook
import sys
import json
dir=raw_input("Enter the location of application.xls file:")
wb = open_workbook(dir)
result={}
print "Running"
for s in wb.sheets():
    print 'Sheet:',s.name
    
    for row in range(18, 111):
        if str(s.cell(row,2).value)=='' or str(s.cell(row,0).value)=='' or (s.cell(row,2).value)=='NA':
            continue
        key=str(s.cell(row,0).value)
        for ch in [" ","\n","/",",","&"]:
            key=key.replace(ch, "")
        val=str(s.cell(row,2).value)
        for ch in ['\n','"']:
            val=val.replace(ch, "")
        result[key]=val

result["tframework"]="OFTest"
result["Software"]="OFTest Commit 58ee0837f6c1b8ae33fdbdaeddf2f7e30f433566"
result["server"]="HP ProLiant D160 G6 (quad-core Intel Xeon Processor @ 2.13GHz, 8GB of RAM)"
result["serveros"]="Red Hat Enterprise Linux Server release 6.4"
f=open("metadata.json", 'w')
f.write(json.dumps(result))        
f.close()
