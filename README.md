# softfocus
Interact with a database of tidy data tables using Bokeh

## objective definition
The purpose of this 'bokeh serve' example is to give a template for visualizing typical measurement databases.

If using the "tidy data" format, a database should be comprising of several tables, each representing a single observational unit (e.g. a sample test in certain experimental conditions). 
This unit comprises of variables (the columns) recorded in successive observations (the rows). See [Wickham's paper](http://vita.had.co.nz/papers/tidy-data.pdf)

For vizualizing purpose, it is practical to have a **dashboard** with a main tab or window listing a summary of the information contained in each table. Then select one or several of them and plot/visualize their content. The objective
is to be able to compare efficiently variables against each other, but also observational units against each other.

*This template produces random csv files in a tests/ folder the first time you start it.*


Some functionalities of this template:
    - list csv files and their info in a main tab
    - plot the content of a selected csv file, selecting x-axis, y-axis and optionaly a secondary y-axis
    - download in Excel format the transformed table (javascript implementation)
    - status text

## Getting Started

### Prerequisites

You need python 3.6 and to install `bokeh`, `pandas` and all their dependencies.

If you use Anaconda, you can also go to the softfocus folder and create a new environment from there:
```
conda env create -f environment.yml
```
or make sure your current environment has the necessary packages
```
conda env update -f environment.yml
```

### Installing
Simply download the folder.

### Run it
softfocus uses the "folder" version of bokeh server.

Open a CLI, cd to the top softfocus folder then write:
```
bokeh serve softfocus
```
optional arguments:
```
    --allow-websocket-origin=localhost:5006 \\local access
    --allow-websocket-origin=REMOTE_IP:5006 \\remote access
    --show \\immediately opens a browser tab with the bokeh app
    --args folder/  \\list csv files from designated folder
```

The first time you run it, a sample data set will be generated in `tests/` if you haven't done so yet.

## Outlook / Contributing
Things to add/improve in the template:
- delete excess xls files in a separate thread without document lock
- use Tornado (or anything else) to implement the download method without dummy
- make a main class for the main tab/multi tab functionality, then subclasses for the type of database (csv folders, sql, hd5...)
- add SQL functionality    
- filter or use a custom script on a table
    
## Author
Hugues-Yanis Amanieu, hyamani.eu
