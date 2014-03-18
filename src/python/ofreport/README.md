## Required ofreport Directory Structure
After running oftest with `--publish`, one json files and a directory named `logs` will be created in the ofreport directory.


## Generating a Report
All overview and analysis html files will be compiled into a their respective test group pages. By default files will be saved in `./results`.
Device specific information is extracted from the metadata.json file.To create this file you need to have xlrd and json module installed.

Running the following command will generate the report in a folder with current data.

```
python ofreport.py

```

It will also prompt you for the application.xls file

```
Enter the location of the application.xls file: ./application.xls
```



The `logs/` directory must be included and have proper permissions in order to share wireshark traces.

##Known Issues

All the test cases have to be run to generate the report with --publish and --conformance