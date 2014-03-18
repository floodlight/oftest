# @author Jonathan Stout
import json
import subprocess
import os
import datetime
import logging

d=datetime.datetime.now()
DIR = os.path.dirname(os.path.abspath(__file__))
ANALYSIS_DIR = DIR+'/../analysis/'
LOG_DIR = DIR+'/../logs/'
LOG_LOC = LOG_DIR+'results.json'
METADATA_LOC = DIR+'/../metadata.json'
OFREPORT_DIR = DIR+'/../ofreport/'
OVERVIEW_DIR = DIR+'/../overview/'
SPEC_DIR = DIR+'/../spec/'
SPEC_LOC = SPEC_DIR+'/spec.json'
PUBLISH_DIR = DIR + "/../{0}/".format(d.strftime("%m-%d-%Y"))
PUBLISH_PDF = PUBLISH_DIR + "{0}.pdf".format(d.strftime("%m-%d-%Y"))
PUBLISH_GROUP_DIR = PUBLISH_DIR + "/groups/"
PUBLISH_PDFGROUP_DIR = PUBLISH_DIR + "/groups/"




def get_json(path):
    try:
        f = open(path)
        data = json.load(f)
        f.close()
    except:
        print "Could not load json from {0}".format(path)
        data = {}
    return data

def get_html(path):
    try:
        f = open(path)
        html = f.read()
        f.close()
    except:
        print "Could not find html at {0}".format(path)
        html = ""
    return html

def get_caplinks(cap_dir, test):
    html = ""
    for f in os.listdir(cap_dir):
        if f != "logs.log":
            # Since links are relative add '.' to link to move
            # out of groups directory.
            html += '<a href="%s">%s</a><br/>' % ('../logs/'+test+'/'+f, f)

    return html

def create_testreport_dir():
    # Cleanup old reports and copy prerequisites.
    if os.access(PUBLISH_DIR, os.F_OK):
        subprocess.check_call(['rm', '-r', PUBLISH_DIR])
    os.mkdir(PUBLISH_DIR)
    os.mkdir(PUBLISH_GROUP_DIR)
    subprocess.check_call(['cp', '-R', LOG_DIR, PUBLISH_DIR])
    subprocess.check_call(['cp', '-R', OFREPORT_DIR+'css/', PUBLISH_DIR])
    subprocess.check_call(['cp', '-R', OFREPORT_DIR+'img/', PUBLISH_DIR])

    try: # Copy application.xlsx
        subprocess.check_call(['cp', DIR+'/../application.xls', PUBLISH_DIR])
    except subprocess.CalledProcessError as e:
        print "There was a problem opening application.xls."
    try: # Copy testlist.xlsx
        subprocess.check_call(['cp', DIR+'/../test_form.xls', PUBLISH_DIR])
    except subprocess.CalledProcessError as e:
        print "There was a problem opening test_form.xls."
    try: # Copy vendor.txt
        subprocess.check_call(['cp', DIR+'/../vendor.txt', PUBLISH_DIR])
    except subprocess.CalledProcessError as e:
        print "There was a problem opening vendor.txt."


def create_pdf():
    if os.access(PUBLISH_PDF, os.F_OK):
        subprocess.check_call(['rm', PUBLISH_PDF])
    os.system('./wkhtmltopdf-amd64 --disable-internal-links {0}index.html {0}groups/Grp10.html {0}groups/Grp20.html {0}groups/Grp30.html {0}groups/Grp40.html {0}groups/Grp50.html {0}groups/Grp60.html {0}groups/Grp70.html {0}groups/Grp80.html {0}groups/Grp90.html {0}groups/Grp100.html {1}'.format(PUBLISH_DIR, PUBLISH_PDF))
