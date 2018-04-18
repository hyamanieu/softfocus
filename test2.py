# -*- coding: utf-8 -*-
"""
Created on Wed Apr 18 10:45:04 2018

@author: hy.amanieu
"""

from bokeh.io import curdoc
from bokeh.client import push_session, pull_session, ClientSession
from bokeh.layouts import *
from bokeh.models.widgets import *
from bokeh.models import *
import pandas as pd
import numpy as np
plot_df = pd.DataFrame({
        "A":np.arange(10),
        "B":np.arange(10)*10,
        "C":10*np.arange(10)**2
        })
cols = plot_df.columns.tolist()
x_sel = Select(title='X-Axis',value=cols[0],options=cols,name='x_sel')
y_sel = Select(title='Y-Axis',value=cols[1],options=cols,name='y_sel')
y_sel2 = Select(title='Y-Axis 2',value=cols[2],options=cols+['None'],name='y_sel2')
plot_b = Button(label="Plot", button_type="success")

p = Plot(x_range = Range1d(),
         y_range = Range1d(),
         x_scale = LinearScale(),
         y_scale = LinearScale(),
         plot_height=600,
         plot_width=600,
         title=Title(text='youpi'),
         name='plot')

source = ColumnDataSource(plot_df)
controls = widgetbox(x_sel,y_sel,y_sel2)
plot_tab = Panel(child=row(column(controls,plot_b),p),name='plot_tab')
tabs = Tabs(tabs=[plot_tab])
layout = column([tabs])

    
#place of def update_plot
def update_plot():
    global plot_tab
    x_sel=plot_tab.select_one({'name':'x_sel'})
    p=plot_tab.select_one({'name':'plot'})
    
    #delete previous plot and replace it by a new one
    new_p = Plot(x_range= Range1d(start = plot_df[x_sel.value].min(),
                          end = plot_df[x_sel.value].max()),
                 y_range= Range1d(start = plot_df[y_sel.value].min(),
                          end = plot_df[y_sel.value].max()),
                 x_scale = LinearScale(),
                 y_scale = LinearScale(),
                 plot_height=600,
                 plot_width=600,
                 title=Title(text='youpi'),
                 name='plot',
                 )
    
    
    plot_tab.child.children.remove(p)
    plot_tab.child.children.append(new_p)
    del p
    p = new_p
    
    
    x_axis = LinearAxis(
                    axis_label = x_sel.value,
                    ticker=BasicTicker(desired_num_ticks =10),
                    name='x_axis')
    y_axis = LinearAxis(
            axis_label = y_sel.value,
            ticker=BasicTicker(desired_num_ticks =10),
            name='y_axis')

    ly = p.add_glyph(source,
                     Line(x=x_sel.value,y=y_sel.value),
                     name='ly')


    p.add_layout(x_axis,'below')
    p.add_layout(y_axis,'left')
    
    
    
    if y_sel2.value.strip() != 'None':
        y_axis2 = LinearAxis(
                            axis_label = y_sel2.value,
                            ticker=BasicTicker(desired_num_ticks=10),
                            name='y_axis2',
                            y_range_name='right_axis')

        p.add_layout(y_axis2,'right')
        p.extra_y_ranges = {"right_axis": Range1d(
                          start = plot_df[y_sel2.value].min(),
                          end = plot_df[y_sel2.value].max())}
        ly2 = p.add_glyph(source,
                                       Line(x=x_sel.value,
                                           y=y_sel2.value,
                                           line_width=2,
                                          line_color='red',
                                           name = 'ly2'),
                            y_range_name='right_axis'
                                      )

        leg_items = [LegendItem(label=y_sel.value,
                                             renderers=[ly]),
                                 LegendItem(label=y_sel2.value,
                                           renderers=[ly2])
                              ]
    else:
        
        leg_items = [LegendItem(label=y_sel.value,
                                             renderers=[ly]),
                              ]
    p.add_layout(Legend(items=leg_items,
                                    location='top_right')
                             )
    print('#'*79)
    for ref in p.references():
        try:
            print(ref.visible,': ',ref)
        except:
            continue
        
        
def update_caller():
    curdoc().add_next_tick_callback(update_plot)


plot_b.on_click(update_caller)
curdoc().add_root(layout)
update_caller()
