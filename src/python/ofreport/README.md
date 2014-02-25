## Required ofreport Directory Structure
After running oftest with `--publish`, two json files and a directory named `logs` will be created. Copy these three items into the ofreport directory as shown below.

```
ofreport.py
equipment.json
# Custom analysis results
analysis/
  Grp100.html
  Grp100No160.html
# General overview descriptions
overview/
  Grp100.html
  Grp100No160.html
# Results generated from oftest
logs/
  results.json
  Grp100No160/
    trace.log
    ctrl.pcap
    data9.pcap
    data10.pcap
    data11.pcap
    data12.pcap
ofreport/
  views/
    groups.html
    tests.html
  css/
    basic.css
  scripts/
    basic.js
```
## Generating the metadata.json file
Device specific information is extracted from the metadata.json file. To create this file you need to have the xlrd and json module installed in python.
Run the following command. This will prompt you for application.xlsx file location.
```
python excel.py
Enter the location of the file:./application.xlsx
```

## Generating a Report
All overview and analysis html files will be compiled into a their respective test group pages. By default files will be saved in `./results`.
```
python ofreport.py
```
To compile results run
```
python ofreport.py --compress
```
The `logs/` directory must be included and have proper permissions in order to share wireshark traces.
