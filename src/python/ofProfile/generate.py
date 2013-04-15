## TODO: Better way to generated the files.##

import os

os.system('pyxbgen -u ./xsd/match_field_test.xsd -m match_field_test')
os.system('pyxbgen -u ./xsd/switch_profile.xsd -m switch_profile')
os.system('pyxbgen -u ./xsd/test_profile.xsd -m test_profile')

os.system('mv match_field_test.py ./generated/')
os.system('mv switch_profile.py ./generated/')
os.system('mv test_profile.py ./generated/')
