import pandas as pd
from datetime import datetime, timedelta
from bokeh.models import Plot, LinearAxis,Range1d, Jitter
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
import math

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

def get_corr(col1, col2):
    col1_r = col1.resample('15min').sum()
    col2_r = col2.resample('15min').first()
    col2_n = col2_r.dropna()

    new = pd.merge(pd.DataFrame(col1_r),pd.DataFrame(col2_n), left_index=True, right_index=True)
    dates = new.resample('D').mean()
    s1_list = []
    s2_list = []
    for i in range(1,len(dates)):
        yesterday = str(dates.index.date[i-1])
        today = str(dates.index.date[i])
        mask = new.loc[yesterday+' '+'21:00':today+' '+'5:00']
        s1_list.append(mask.iloc[:,0].values)
        s2_list.append(mask.iloc[:,1].values)
    corr_list = []
    for i in range(len(s1_list)):
        s1_f = [float(d) for d in s1_list[i]]
        s2_f = [float(d) for d in s2_list[i]]
        s1=pd.Series(s1_f)
        s2=pd.Series(s2_f)
        corr_list.append(s1.corr(s2,method='pearson'))
    return corr_list

def correlation(dates, sound, room, out):
    correl1 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],room['room temperature'])]
    correl2 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],out['local temperature'])]
    correl3 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],out['atmospheric pressure'])]
    correl4 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],out['local humidity'])]
    correl5 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],out['wind speed'])]
    correl6 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],room['room humidity'])]
    correl7 = [0 if math.isnan(x) else x for x in get_corr(sound['Trigger bool'],out['cloud'])]
    p = figure(plot_width=1100,
                          plot_height=500,
                          min_border=0, toolbar_location="above", tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'hover'],
                          outline_line_color="#666666", x_axis_type='datetime',
                          x_axis_label='Datetime', y_axis_label='correlation')
    p.y_range = Range1d(-1,2)
    p.line(dates,correl1, color='red', line_width = 2, legend = 'room temperature')
    p.line(dates,correl6, color='pink', line_width = 2, legend = 'room humidity')
    p.line(dates,correl2, color='navy', line_width = 2, legend= 'local temperature')
    p.line(dates,correl3, color='green', line_width = 2, legend = 'atmospheric pressure')
    p.line(dates,correl4, color='orange', line_width = 2, legend = 'local humidity')
    p.line(dates,correl5, color='black', line_width = 2, legend = 'wind speed')
    p.line(dates,correl7, color='gold', line_width = 2, legend = 'cloud')

    p.legend.location = "top_left"
    p.legend.click_policy="hide"
    return p

def sound_line(col1,col2,interval):
    df1_resampled = col1.resample(interval).sum()
    df2_resampled = col2.resample(interval).first()
    df2_resampled = [float(d) for d in df2_resampled.values]
    x_label = []
    for i in range(len(df1_resampled.index)):
        x_label.append(str(df1_resampled.index[i]))
    plot = figure(plot_width=1100, plot_height=400, x_range = x_label,
                  tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'hover'],
                  outline_line_color="#666666",toolbar_location="above",min_border=0,
                  x_axis_label="Datetime", y_axis_label="Trigger Count")
    plot.y_range = Range1d(min(df1_resampled)-1,max(df1_resampled)+1)
    plot.extra_y_ranges = {col2.name: Range1d(start=min(df2_resampled)-1, end=max(df2_resampled)+1)}
    plot.add_layout(LinearAxis(y_range_name=col2.name, axis_label=col2.name), 'right')
    plot.circle(x_label,df1_resampled,color='blue',legend_label='Trigger Count')
    plot.line(x_label,df2_resampled,y_range_name=col2.name,color='red',legend_label=col2.name)
    plot.xaxis.major_label_orientation = "vertical"
    plot.legend.location="bottom_left"
    return plot

def time_series_sound(col1, interval, title):
    col1_r = col1.resample(interval).sum()
    col1_sam = [float(d) for d in col1_r.values]
    p = figure(title=title, plot_width=1100,
                      plot_height=300,
                      min_border=0, toolbar_location="above", tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'hover'],
                      outline_line_color="#666666", x_axis_type='datetime',
                      x_axis_label='Datetime', y_axis_label='sound number')

    margin1=0.1*(max(col1_sam)-min(col1_sam))
    p.y_range = Range1d(min(col1_sam)-margin1,max(col1_sam)+margin1)
    p.line(col1_r.index,col1_sam, color='red', line_width = 2)
    return p

def time_series(col1, interval, title):
    col1 = col1.astype(float)
    col1_r = col1.resample(interval).mean()
    col1_r = col1_r.dropna()
    col1_sam = [float(d) for d in col1_r.values]

    p = figure(title=title, plot_width=1100,
                      plot_height=300,
                      min_border=0, toolbar_location="above", tools=['pan', 'wheel_zoom', 'box_zoom', 'reset', 'save', 'hover'],
                      outline_line_color="#666666", x_axis_type='datetime',
                      x_axis_label='Datetime', y_axis_label=col1.name)

    margin1=0.1*(max(col1_sam)-min(col1_sam))
    p.y_range = Range1d(min(col1_sam)-margin1,max(col1_sam)+margin1)
    p.line(col1_r.index,col1_sam, color='red', line_width = 2)

    return p
