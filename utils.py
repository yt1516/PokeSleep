import pandas as pd
from datetime import datetime, timedelta
from bokeh.models import Plot, LinearAxis,Range1d, Jitter
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource

def time_select(dataframe, date):
    digits = [int(d) for d in str(date)]
    dd = date[0:2]
    mm = date[2:4]
    yy = date[4:9]
    date_formatted = datetime(year=int(yy),month=int(mm),day=int(dd))
    date_prev = date_formatted - timedelta(days=1)
    date_y = str(date_prev)
    start_time = '20:00:00'
    end_time = '5:00:00'
    end_datetime = str(date[4:9])+'-'+str(date[2:4])+'-'+str(date[0:2])+' '+ end_time
    start_datetime = str(date_y[0:4])+'-'+str(date_y[5:7])+'-'+str(date_y[8:10])+' '+ start_time
    mask = (dataframe['Datetime'] > start_datetime) & (dataframe['Datetime'] <= end_datetime)
    period = dataframe.loc[mask]
    return period

def normalise(x,y):
    x_int = [int(d) for d in x]
    y_int = [int(d) for d in y]
    g_max = max(max(x_int),max(y_int))
    x_scaled = [i/g_max for i in x_int]
    y_scaled = [i/g_max for i in y_int]
    return x_scaled, y_scaled

def scatter_line_plot(df1, df2, col1, col2):
    plot = figure(plot_width=800, plot_height=250, x_axis_type='datetime')
    set1, set2 = normalise(col1.values,col2.values)
    plot.circle(df1.index, set1,color='red',alpha=0.5)
    plot.line(df2.index, set2,color='navy',alpha=0.5)
    return plot

def bar_line_plot(col1, col2, interval):                    # Keep col1 trigger sum, col2 can be anything
    df1_resampled = col1.resample(interval).sum()
    df2_resampled = col2.resample(interval).first()
    df2_resampled = [float(d) for d in df2_resampled.values]
    set2 = [d + max(df1_resampled) - min(df2_resampled) for d in df2_resampled]
    x_label = []
    for i in range(len(df1_resampled.index)):
        x_label.append(str(df1_resampled.index[i]))
    plot = figure(plot_width=800, plot_height=450, x_range = x_label)
    plot.vbar(x_label, top = df1_resampled,color='navy', width = 1)
    plot.line(x_label, y = set2,color='red')
    plot.xaxis.major_label_orientation = "vertical"
    return plot

def sound_line(col1,col2,interval):
    df1_resampled = col1.resample(interval).sum()
    df2_resampled = col2.resample(interval).first()
    df2_resampled = [float(d) for d in df2_resampled.values]
    x_label = []
    for i in range(len(df1_resampled.index)):
        x_label.append(str(df1_resampled.index[i]))
    plot = figure(plot_width=1100, plot_height=300, x_range = x_label,
                  tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'hover'],
                  x_axis_label="Datetime", y_axis_label="Trigger Count")
    plot.y_range = Range1d(min(df1_resampled)-1,max(df1_resampled)+1)
    plot.extra_y_ranges = {col2.name: Range1d(start=min(df2_resampled)-1, end=max(df2_resampled)+1)}
    plot.add_layout(LinearAxis(y_range_name=col2.name, axis_label=col2.name), 'right')
    plot.circle(x_label,df1_resampled,color='blue',legend='Trigger Count')
    plot.line(x_label,df2_resampled,y_range_name=col2.name,color='red',legend=col2.name)
    plot.xaxis.major_label_orientation = "vertical"
    return plot

def sound_freq(df):
    x_list = []
    y_list = []
    for i in range(len(df)):
        x_list.append(df.index[i])
        y_list.append(df['Trigger bool'][i])

    p = figure(plot_width=1100, plot_height=300, x_axis_type='datetime')

    data = ColumnDataSource(dict(x=x_list,y=y_list))

    p.circle(x = "x", y={'field':"y",'transform': Jitter(width=0.1)}, source=data, alpha = 0.5)
    p.xaxis[0].formatter.days = ['%m/%d']
    return p
