"""softfocus shall be called with bokeh serve

softfocus uses the "folder" version of bokeh server

Open a CLI, cd to the top softfocus folder then write:
bokeh serve softfocus
optional arguments:
    --allow-websocket-origin=localhost:5006 \\local access
    --allow-websocket-origin=REMOTE_IP:5006 \\remote access
    --show \\immediately opens a browser tab with the bokeh app
    --args folder/  \\list csv files from designated folder
              
The purpose of this 'bokeh serve' example is to give a template for vizualizing
typical measurement databases. 

If using the "tidy data" format, a database
should be comprising of several tables, each representing a single 
observational unit (e.g. a sample test in certain experimental conditions). 
This unit comprises of variables (the columns) recoded in successive 
observations (the rows).

For vizualizing purpose, it is often most practical to have a dashboard with
a main tab or window listing a summary of the information contained in each 
table. Then select one or several of them and plot their content. The objective
is to be able to compare efficiently variables against each other, but also
observational units against each other.

This template uses the sample data of Bokeh, so the different csv files do not
represent similar observational units.


Some functionalities of this template:
    - list csv files and their info in a main tab
    - plot the content of a selected csv file, selecting x-axis, y-axis and 
    optionaly a secondary y-axis
    - filter or use a custom script on the content
    - download in Excel format the transformed table (javascript 
    implementation)
    - status text

Things to add/improve in the template:
    - find a better method to change between column names for the axes
    - delete excess xls files in a separate thread without document lock
    - use Tornado to implement the download method without dummy
    - make a main class for the main tab/multi tab functionality, then 
    subclasses for the type of database (csv folders, sql, hd5...)
    - add SQL functionality
    
                      

author: https://github.com/hyamanieu/
V 0.1
"""
__version__ = '0.1'


import sys
import os

#Bokeh imports
from bokeh.layouts import row, widgetbox, column
from bokeh.models import Button, ColumnDataSource
from bokeh.models import LinearAxis, Range1d, CustomJS
#from bokeh.models.formatters import (BasicTickFormatter,
#                                     NumeralTickFormatter)
from bokeh.models.annotations import LegendItem
from bokeh.models.widgets import (DataTable, 
                                  DateFormatter, 
                                  TableColumn,
                                  DateRangeSlider,
                                  Panel,
                                  Tabs,
                                  Select,
                                  TextInput,
                                  Div)
from bokeh.plotting import figure
from bokeh.io import curdoc
#specific imports for multithreading
#from tornado import gen
#from bokeh.document import without_document_lock

#local imports


#other tools
import pandas as pd
#from datetime import date as datetype
import time
from datetime import date

#from flask import Flask, make_response, Response, send_file
#app = Flask(__name__)

#logging
import logging

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
file_handler = logging.FileHandler(filename='test.log', mode='w')
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)





class SoftFocus(object):
    """class to view and process bokeh sample data using a bokeh server.
    
    When within its parent folder, open your terminal and write:
        bokeh serve softfocus
        
    see module doc
    """
    
    def __init__(self):
        
        # put the controls and the table in a layout and add to the document
        self.document = curdoc()
        
        #following method parses arguments and create the layout
        # (in self.layout) with the main tab
        self.create()
        logger.info('layout created')
        
        #add the layout to the document
        self.document.title = "Soft Focus"
        self.document.add_root(self.layout)
        logger.info('layout added to document')
        print(self.tabs)
        print(self.tabs.active)
        print(self.info_text.text)
        
        #show main table
#        self.update()
#        logger.info('table shown')
        
        #add a callback called every hour to delete excessive amount of xlsx
        # in the /static/uploads folder, where uploads are        
        self.document.add_periodic_callback(self._delete_excess_xlsx,3600000)
        
        
        #dicts hold data from all opened secondary classes
        self.x_sel = dict()#all dropdown x selection menus from opened tabs
        self.y_sel = dict()#all dropdown y selection menus from opened tabs
        self.y_sel2 = dict()#all dropdown secondary y selection menus
        self.figs = dict()#all figures from opened tabs
        self.plot_dfs=dict()#dataframe of each plotted test
        self.ly = dict()#GlyphRenderers of each opened tab
        self.ly2 = dict()#GlyphRenderers of each opened tab (secondary y-axis)
        
    def create(self):
        """parse the bokeh serve arguments then create the main layout
        
        To create the main layout, the method _create_folder is called. Other
        methods could be called depending on the argument if we want to fetch
        data with different methods, e.g. _create_sql
        
        
        """
        
        
        if len(sys.argv)>2:
            print('Syntax for default Bokeh sampledata'
                  ' folder: bokeh serve {}'.format(sys.argv[0]))
            print('Syntax for own folder: bokeh serve'
                  ' {} --args <folder/>'.format(sys.argv[0]))
            sys.exit(0)
        
        elif len(sys.argv)==1:
            from bokeh.util.sampledata import external_data_dir
            data_dir = external_data_dir()
            if not os.path.exists(data_dir):
                from bokeh.util.sampledata import download as bokeh_download
                bokeh_download()                
        elif len(sys.argv)==2:
            data_dir = sys.argv[1]
            if not os.path.isdir(data_dir):
                print("fpath must be a string indicating"
                      " a directory path")
                sys.exit(0)
            #other arguments could be processed to call different methods
            
            
        self._create_folder(data_dir)
            
    
    def _create_folder(self,data_dir):
        #list only csv files, populate a dict with general info about the files
        logger.info('Database in a csv folder: {0}'.format(data_dir))
        list_dir = os.listdir(data_dir)
        csv_dic = {'CSV': [csv for csv in list_dir if csv.endswith('.csv')],
                   'size (kB)':[],
                   'last modification':[],
                   'number of columns':[],
                   }
        if len(csv_dic)<1:
            logger.warning("no csv file found in folder. Exit")
            sys.exit(0)
        
        
        for csv in csv_dic['CSV']:
            csv_stat = os.stat(os.path.join(data_dir,csv))
            csv_dic['size (kB)'].append(csv_stat.st_size/1024)
            csv_dic['last modification'].append(
                                     date.fromtimestamp(csv_stat.st_mtime)
                                     )
            with open(os.path.join(data_dir,csv),'rb') as f:
                csv_dic['number of columns'].append(
                                    len(f.readline().decode().split(','))
                                    )
            
        #make bokeh source from the dic
        self.df = pd.DataFrame(csv_dic)
        self.main_source = ColumnDataSource(self.df)
        
        
        ####  some widgets to filter the table ####
        #date selector
        last_date = self.df['last modification'].max() 
        first_date = self.df['last modification'].min()
        self.date_slider = DateRangeSlider(title='Start date',
                                      start=first_date,
                                      end=last_date,
                                      value=(first_date,last_date),
                                      step=1)
        self.date_slider.on_change('value', 
                                   lambda attr, old, new: self.update())
        
        #byte size selection through text input        
        self.size_inputtext = TextInput(title='size in kbytes')
        self.size_inputtext.value = "fmt: '100' or '10..200'"
        self.size_inputtext.on_change('value',
                                      lambda attr, old, new: self.update())
        
        #filter by file name        
        self.csvname_text = TextInput(title='Testname')
        self.csvname_text.on_change('value',
                                     lambda attr, old, new: self.update())
        
        #button to plot
        self.plot_button = Button(label="Plot", button_type="success")
        self.plot_button.on_click(self.add_plot_tab)
        self.plot_button.disabled = True#active only when csv is selected
        
        #make table widget
        #table formatting
        columns = []
        for c in self.df.columns.tolist():
            if c in ['last modification']:
                columns.append(TableColumn(field=c,title=c,
                                           formatter=DateFormatter(format="ISO-8601")))
            else:
                columns.append(TableColumn(field=c,title=c))
        
        self.data_table = DataTable(source=self.main_source, 
                               columns=columns, 
                               width=800,
                               index_position=None,
                               editable=False,
                               )
        self.data_table.source.on_change('selected',self.sel_table)
        
        #controls in a box
        controls = widgetbox(self.date_slider,
                             self.plot_button,
                             self.size_inputtext,
                             self.csvname_text,
                             )
        #data table in its own box
        table = widgetbox(self.data_table)
        
        #insert all widgets in a Panel
        tab1 = Panel(child=row(controls, table),title="CSVs",closable=False)
        #single tab for now
        self.tabs = Tabs(tabs=[tab1],
                              sizing_mode = 'stretch_both')
        #need to add this callback otherwise the table will turn invisible
        #after coming back to this main tab
        self.tabs.on_change('active',lambda attr, old, new: self.update())
        
        #add a status text above all tabs
        self.info_text = Div(text='<font color="green">ready.</font>',
                                 width=200, height=25)
        #main layout
        self.layout = column([self.info_text,self.tabs])
        
        # main data folder
        self.data_dir = data_dir
    
    def _create_sql(self,fpath=r"sql_db.ini"):
        """NOT IMPLEMENTED, called to link to an SQL database"""
        pass

    def _wait_message_decorator(f):
        """prints loading status during loading time
        
        Add this decorator before any methods used as callbacks
        This will indicate the user to wait or outputs errors
        """
        #https://stackoverflow.com/questions/1263451/python-decorators-in-classes
        def wait_please(*args,**kwargs):
            self = args[0]
            self.info_text.text = '<font color="orange">loading, please wait...</font>'
            try:
                r = f(*args,**kwargs)
            except:
                logger.error("Unexpected error:",sys.exc_info()[0])
                self.info_text.text = ('<font color="red">'
                                       'Error: {}'
                                       '</font>').format(sys.exc_info()[0])
            self.info_text.text = '<font color="green">ready.</font>'
            return r
        return wait_please
    
    
    #call function when selection on table
    def sel_table(self, attr, _, value):
        """
        Selection of a cell/row in a tab
        """
        sels = self.data_table.source.selected['1d']['indices']
        
        if sels:#if not empty
            self.plot_button.disabled = False
            self.sel_csv = (self.main_source.data['CSV'][sels[0]],#system number
                    self.main_source.data['size(kB)'][sels[0]])#test number
#            print(self.sel_csv)
        else:
            self.plot_button.disabled = True
            
    #define callback function to show new table
    @_wait_message_decorator
    def update(self, attr=None, old=None, new=None):
        """
        Callback function to show the main table with all tests
        """
        df = self.df
        
        filt = ((df['last modification'] 
                   >= self.date_slider.value_as_datetime[0])
                & (df['last modification'] 
                   <= self.date_slider.value_as_datetime[1]))
        
        try:
            szfilt = [int(i) for i in self.size_inputtext.value.split('..')]
            if len(szfilt)==2:
                szfilt_max = max(szfilt)
                szfilt_min = min(szfilt)
                filt &= (df['size(kB)'] >= szfilt_min)&(df['size(kB)'] <= szfilt_max)
            elif len(szfilt)==1:
                szfilt = szfilt[0]
                filt &= (df['size(kB)'] == szfilt)
            else:
                self.size_inputtext.value = "fmt: '100' or '98..102'"
                
        except:
            self.size_inputtext.value = "fmt: '100' or '98..102'"
        
        try:
            filt &= df['CSV'].str.contains(self.csvname_text.value,na=False)
        except:
            self.csvname_text.value = ''
        
        current = df[filt]
        current = current.fillna('NaN')
            
        self.main_source.data = current.to_dict('list')
        
    #callback function to add a plot tab
    @_wait_message_decorator
    def add_plot_tab(self):
        """
        Callback function to add a new tab with a plot.
        
        Each tab is differenciated by its name. The name is the csv file name
        """
        
        
        #plot controls
        
        logger.info("adding plot of ",self.sel_csv)
        plot_df = pd.DataFrame(os.path.join(self.data_dir, self.sel_csv))
        self.plot_dfs[self.sel_csv] = plot_df
        
        cols = plot_df.columns.tolist()
        x_sel = Select(title='X-Axis',value=cols[0],options=cols)
        y_sel = Select(title='Y-Axis',value=cols[1],options=cols)
        y_sel2 = Select(title='Y-Axis 2',value='None',options=cols+['None'])
               
        #exit button
        exit_b = Button(label="Exit", button_type="success")
        exit_b.on_click(self.remove_current_tab)
        #download button
        download_b = Button(label="Download", button_type="success")
        download_b.on_click(self.download)
        
        
        #prepare figure
        source = ColumnDataSource(plot_df)
        p = figure(title=self.sel_csv,
                   x_axis_label=x_sel.value,
                   y_axis_label=y_sel.value,
#                   sizing_mode = 'stretch_both',
                   )
        #primary y-axis
        self.ly[self.sel_csv] = p.line(x_sel.value, 
               y_sel.value,
               source=source,
               legend=y_sel.value, 
               line_width=2)
        #secondary y-axis
        p.extra_y_ranges = {"right_axis": Range1d(bounds='auto')}
        self.ly2[self.sel_csv] = p.line(x_sel.value,
               cols[2],
               source=source,
               legend=y_sel2.value, 
               line_width=2,
               color='red',
               y_range_name='right_axis' )
        p.add_layout(LinearAxis(bounds='auto',y_range_name='right_axis'),
                     'right')

        #make all axes and lines invisible until user clicks "plot"        
        p.yaxis[1].visible=False
        p.xaxis[0].visible=False
        p.yaxis[0].visible=False
        self.ly[self.sel_csv].visible = False
        p.xaxis[0].axis_label=x_sel.value
        p.yaxis[0].axis_label=y_sel.value
        
        #empty the legend until user clicks "plot"
        p.legend.items = []
        #plot button
        plot_b = Button(label="Plot", button_type="success")
        plot_b.on_click(self.update_plot)
        
        #text to indicate widgets manipulating the plot only
        plot_group_text = Div(text='<b>Plot properties</b>')

        #dummy idea from https://stackoverflow.com/questions/44212250/bokeh-widgets-call-customjs-and-python-callback-for-single-event  
        #the javascript called linked to this dummy circle element is meant
        #to activate the download of whatever file is in the path 
        #./static/uploads/sessionid_output.xlsx, where sessionid is the id of the
        # current session.
        dummy = p.circle([1], [1],name='dummy',alpha=0)
        JScode_fetch = """
        var filename = p.title.text;//file name on client side
        var get_path = '/softfocus/static/uploads/';//file path on server side
        var session_id = p.tags[0];
        get_path = get_path.concat(session_id);
        get_path = get_path.concat('_output.xlsx')
        filename = filename.concat('.xlsx');
        fetch(get_path, {cache: "no-store"}).then(response => response.blob())
                            .then(blob => {
                                //addresses IE
                                if (navigator.msSaveBlob) {
                                    navigator.msSaveBlob(blob, filename);
                                }
                                
                                else {
                                    var link = document.createElement("a");
                                    link = document.createElement('a')
                                    link.href = URL.createObjectURL(blob);
                                    window.open(link.href, '_blank');
                                    
                                    link.download = filename
                                    link.target = "_blank";
                                    link.style.visibility = 'hidden';
                                    link.dispatchEvent(new MouseEvent('click'))
                                    URL.revokeObjectURL(url);
                                }
                                return response.text();
                            });
        
        
        """
        
        session_id= str(self.document.session_context._id)
        p.tags = [session_id]
        dummy.glyph.js_on_change('size', CustomJS(args=dict(p=p),
                                          code=JScode_fetch))
        
        #plot controls together in a box
        controls = widgetbox(plot_group_text,x_sel,y_sel,y_sel2,plot_b)
        #tab panel for this plot, differenciated with its name        
        plot_tab = Panel(child=row(column(controls,download_b,exit_b),p),
                         title="Plot {}".self.sel_csv,
                         closable=True,
                         name=str(self.sel_csv))#name of tab is csv filename
        
        
        self.figs[self.sel_csv]=p
        self.x_sel[self.sel_csv]=x_sel
        self.y_sel[self.sel_csv]=y_sel
        self.y_sel2[self.sel_csv]=y_sel2
        
        self.tabs.tabs.append(plot_tab)
#        self.update_plot()
    
    
    @_wait_message_decorator
    def update_plot_source(self, attr=None, old=None, new=None):
        tab_ix = self.tabs.active
        test = self.tabs.tabs[tab_ix].name
        source = self.ly[test].data_source
        pass
    
    
    @_wait_message_decorator    
    def update_plot(self):
        #find table name of active tab and its bokeh instances
        tab_ix = self.tabs.active
        test = self.tabs.tabs[tab_ix].name#contains csv filename
        
        p=self.figs[test]
        x_sel=self.x_sel[test]
        y_sel=self.y_sel[test]
        y_sel2=self.y_sel2[test]
        plot_df = self.plot_dfs[test]
        
        self.ly[test].visible = True
        p.xaxis[0].visible=True
        p.yaxis[0].visible=True
        p.xaxis[0].axis_label=x_sel.value
        p.yaxis[0].axis_label=y_sel.value
        
        # add a line renderer with legend and line thickness    
        self.ly[test].glyph.x = x_sel.value
        self.ly[test].glyph.y = y_sel.value
        s = plot_df[y_sel.value].min()
        e = plot_df[y_sel.value].max()
        p.y_range.start = s - abs(s*0.1)
        p.y_range.end   = e + abs(e*0.1)
        if y_sel2.value.strip() != 'None':
            self.ly2[test].glyph.x = x_sel.value
            self.ly2[test].glyph.y = y_sel2.value
            self.ly2[test].visible=True
            p.yaxis[1].visible=True
            s = plot_df[y_sel2.value].min()
            e = plot_df[y_sel2.value].max()
            p.extra_y_ranges['right_axis'].start = s - abs(s*0.1)
            p.extra_y_ranges['right_axis'].end   = e + abs(e*0.1)
            p.legend.items = [LegendItem(label=y_sel.value,
                                         renderers=[self.ly[test]]),
                             LegendItem(label=y_sel2.value,
                                        renderers=[self.ly2[test]])]
        else:
            self.ly2[test].visible=False
            p.yaxis[1].visible=False
            
            p.legend.items = [LegendItem(label=y_sel.value,
                                         renderers=[self.ly[test]])]
            
           
    def print_active_tab(self):
        """
        non used: method for debugging
        """        
        tab_ix = self.tabs.active
        test = self.tabs.tabs[tab_ix].name
        print(test)
        
        
    #callback function to remove a tab
    def remove_current_tab(self):
        """
        Callback function to remove a tab
        """
        tab_ix = self.tabs.active
        curr_csv = self.tabs.tabs[tab_ix].name
        if tab_ix == 0:
            return#do nothing if main tab where all tests are   
        
        del self.x_sel[curr_csv]
        del self.y_sel[curr_csv]
        del self.y_sel2[curr_csv]
        del self.figs[curr_csv]
        del self.ly[curr_csv]
        del self.ly2[curr_csv]
        
        #self.tabs.tabs.pop(tab_ix)
        del self.tabs.tabs[tab_ix]
        


    
    
    @_wait_message_decorator
    def download(self):
        tab_ix = self.tabs.active
        test = self.tabs.tabs[tab_ix].name
        p=self.figs[test]
        dummy = p.select(name='dummy')[0]#handle invisible model
        session_id= str(self.document.session_context._id)
        data = pd.DataFrame(self.ly[test].data_source.data)
        dirpath = os.path.join(os.path.dirname(__file__),'static','uploads')
        xlsxpath = os.path.join(dirpath,session_id+'_output.xlsx')
        if os.path.exists(xlsxpath):
            os.remove(xlsxpath)
        writer = pd.ExcelWriter(xlsxpath,
                                engine='xlsxwriter')
        logger.info('Testname: ',test)
        data.to_excel(writer,'data'+test)
#        infos.to_excel(writer,'info'+infos['Testname'])        
        writer.close()
        #change its size
        dummy.glyph.size = (dummy.glyph.size 
                            + pd.np.random.choice([-1,1],size=1)[0])
        

#    @gen.coroutine
    def _delete_excess_xlsx(self):
        """deletes all xlsx files in the upload static folder older than 24h"""
        dirpath = os.path.join(os.path.dirname(__file__),'static','uploads')
        now = time.time()
        for dirpath, dirnames, filenames in os.walk(dirpath,topdown=False):
            for fname in filenames:
                fpath = os.path.join(dirpath,fname)
                file_age = (now - os.getatime(fpath))/3600
                if ((file_age>24) and fpath.endswith('output.xlsx')):
                    os.remove(fpath)
        

print("soft focus starting up...")
soft_focus = SoftFocus()


if __name__ == "__main__":
    pass
    