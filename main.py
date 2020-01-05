import pandas as pd
from datetime import datetime, timedelta
from random import randint
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import timedelta
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid,
                          Range1d, Jitter)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure, show
from bokeh.layouts import gridplot
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from flask import Flask, render_template, request
from statistics import mean
import requests
import pyowm

app = Flask(__name__)

def get_sound(sound,l_bound,u_bound):
    sound_log = pd.DataFrame(columns = ['Datetime','Trigger'])
    values_list = sound.col_values(1)
    for i in range(len(values_list)):
        if values_list[i]:
            t = values_list[i]
            t_std = datetime.strptime(t, "%Y-%m-%d_%H.%M.%S")
            sound_log = sound_log.append({'Datetime':t_std,'Trigger':randint(l_bound,u_bound), 'Trigger bool':1},ignore_index=True)
            sound_log['Datetime'] = pd.to_datetime(sound_log['Datetime'])
    sound_log = sound_log.drop_duplicates(keep='first')
    sound_log = sound_log.set_index(pd.to_datetime(sound_log['Datetime']))
    return sound_log

def get_room_temp(room_data):
    room_temp = pd.DataFrame(columns = ['Datetime','room temperature','room humidity'])
    room_time = room_data.col_values(1)
    room_tempts = room_data.col_values(2)
    room_hum = room_data.col_values(3)
    for i in range(len(room_time)):
        if room_time[i]:
            t = room_time[i]
            t_std = datetime.strptime(t, "%Y-%m-%d_%H.%M.%S")
            room_temp = room_temp.append({'Datetime':t_std,'room temperature':room_tempts[i],'room humidity':room_hum[i]}
                                         ,ignore_index=True)
            room_temp['Datetime'] = pd.to_datetime(room_temp['Datetime'])
    room_temp = room_temp.set_index(pd.to_datetime(room_temp['Datetime']))
    return room_temp

def get_outside_temp(outside):
    out_temp = pd.DataFrame(columns = ['Datetime','local temperature','local humidity','atmospheric pressure','wind speed',
                                      'weather status'])
    out_time = outside.col_values(1)
    out_tempts = outside.col_values(2)
    out_hum = outside.col_values(3)
    out_atm = outside.col_values(4)
    out_wind = outside.col_values(5)
    out_stat = outside.col_values(6)
    for i in range(len(out_time)):
        if out_time[i]:
            t = out_time[i]
            t_std = datetime.strptime(t, "%Y-%m-%d_%H.%M.%S")
            out_temp = out_temp.append({'Datetime':t_std,'local temperature':out_tempts[i],
                                        'local humidity':out_hum[i],'atmospheric pressure':out_atm[i],
                                        'wind speed':out_wind[i],'weather status':out_stat[i]},ignore_index=True)
            out_temp['Datetime'] = pd.to_datetime(out_temp['Datetime'])
    out_temp = out_temp.drop_duplicates(keep='first')
    out_temp = out_temp.set_index(pd.to_datetime(out_temp['Datetime']))
    return out_temp

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

def get_pokemon(trigger_num):
    from pokedex import pokedex
    pokedex = pokedex.Pokedex(version='v1', user_agent='ExampleApp (https://example.com, v2.0.1)')
    pokemon = pokedex.get_pokemon_by_number(trigger_num)
    name = pokemon[0]['name']
    description = pokemon[0]['description']
    url = pokemon[0]['sprite']
    response = requests.get(url, stream=True)
    return name, description, url

def get_outside_temperature():
    owm = pyowm.OWM('2a9f05a9458a49c59d610b54ed02a840')
    observation = owm.weather_at_coords(51.756236799999996,0.48742399999999997)
    w = observation.get_weather()
    wind = w.get_wind()['speed']
    temp = w.get_temperature('celsius')['temp']
    pressure = w.get_pressure()['press']
    humidity = w.get_humidity()
    cloud = w.get_clouds()
    stat = w.get_status()
    return stat, temp, wind, pressure, humidity, cloud

#@app.route("/<date>/", methods=['GET', 'POST'])
@app.route('/')
#def master(date):
def master():

    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('SIOTfinal.json', scope)
    client = gspread.authorize(creds)

    sound_g = client.open('sound').sheet1
    room_g = client.open('room').sheet1
    outside_g = client.open('outside').sheet1
    room_df = get_room_temp(room_g)
    out_df = get_outside_temp(outside_g)
    room_temp_bound = [int(d) for d in room_df['room temperature'].values]
    sound_df = get_sound(sound_g, min(room_temp_bound),max(room_temp_bound))

    intervals = ["15min","30min"]
    variables = ['room temperature','room humidity','local temperature','local humidity','atmospheric pressure',
    'wind speed']
    room_variables = ['room temperature','room humidity']
    out_variables = ['local temperature','local humidity','atmospheric pressure','wind speed']
    dates = []
    all_date = sound_df.resample('D').sum()
    for i in range(len(all_date.index)):
        dates.append(str(all_date.index[i].strftime('%Y-%m-%d')))

    current_date = request.args.get("dates")
    current_interval = request.args.get("intervals")
    current_variable = request.args.get("variables")

    if current_interval == None:
        current_interval = "10min"

    if current_variable == None:
        current_variable = 'room temperature'

    if current_date == None:
        current_date = str(datetime.today().strftime('%Y-%m-%d'))

    date = current_date[8:10]+current_date[5:7]+current_date[0:4]

    sound_date = time_select(sound_df,date)
    room_date = time_select(room_df,date)
    out_date = time_select(out_df,date)
    room_temp_sound_plot = scatter_line_plot(sound_date,room_date,sound_date['Trigger'],room_date['room humidity'])

    trig_num = int(sound_date['Trigger bool'].sum())

    digits = [int(d) for d in str(date)]
    dd = date[0:2]
    mm = date[2:4]
    yy = date[4:9]

    #script, div = components(room_temp_sound_plot)
    script, div = components(sound_freq(sound_df))
    name, description, url = get_pokemon(trig_num)
    stat, temp, wind, pressure, humidity, cloud = get_outside_temperature()
    date_formatted = datetime(year=int(yy),month=int(mm),day=int(dd))
    today = str(date_formatted)
    today = today[0:10]
    date_prev = date_formatted - timedelta(days=1)
    yesterday = str(date_prev)
    yesterday = yesterday[0:10]

    if current_variable in room_variables:
        col2 = room_date[current_variable]
    elif current_variable in out_variables:
        col2 = out_date[current_variable]

    script2,div2 = components(bar_line_plot(sound_date['Trigger bool'],col2,
    current_interval))

    return render_template('chart.html', day_sel=today, day_bef=yesterday, the_div=div, the_script=script,
    pokemon_url=url, pokemon_name=name, pokemon_des=description, stat=stat, temp=temp, wind=wind,
    pressure=pressure, humidity=humidity, cloud=cloud, script2=script2, div2=div2, intervals=intervals,
    current_interval=current_interval, current_variable = current_variable, variables=variables,
    dates=dates, current_date=current_date, trigger_num=trig_num)

if __name__ == "__main__":
    app.run(debug=True)
