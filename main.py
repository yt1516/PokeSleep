import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bokeh.embed import components
from flask import Flask, render_template, request
from random import randint

from utils import time_select,sound_line,time_series_sound,time_series,correlation
from fetch import get_sound,get_room_temp,get_outside_temp,get_pokemon,get_pokemon_random,get_outside_temperature,sleep_tip

app = Flask(__name__)


@app.route('/', methods=['GET'])

@app.route('/home/', methods=['GET'])
def home():
    name, description, url = get_pokemon_random(randint(1,808))
    tip = sleep_tip()
    stat, temp, wind, pressure, humidity, cloud = get_outside_temperature()
    return render_template('index.html', title='Home', name=name, description=description, url = url, tip=tip,
    stat=stat, temp=temp, wind=wind, pressure=pressure, humidity=humidity, cloud=cloud)

@app.route('/about/', methods=['GET'])
def about():
    return render_template('about.html', title='About')

@app.route('/pokemon/', methods=['GET'])
def pokemon():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('SIOTfinal.json', scope)
    client = gspread.authorize(creds)
    poke_data = client.open('pokemon').sheet1
    dates, names, descrips, urls = get_pokemon(poke_data)
    return render_template('pokemon.html', title="Pokemon", dates=dates, names=names, descrips=descrips,
    urls=urls)

@app.route('/timeline/', methods=['GET'])
def timeline():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('SIOTfinal.json', scope)
    client = gspread.authorize(creds)
    sound_g = client.open('sound').sheet1
    room_g = client.open('room').sheet1
    outside_g = client.open('outside').sheet1
    room_df = get_room_temp(room_g)
    out_df = get_outside_temp(outside_g)
    sound_df = get_sound(sound_g)

    intervals = ["15min","30min", "1h", "4h", "1d"]
    dates = []
    all_date = sound_df.resample('D').sum()
    for i in range(len(all_date.index)):
        dates.append(str(all_date.index[i].strftime('%Y-%m-%d')))
    dates = dates[1:]
    variables = ['room temperature','room humidity','local temperature','local humidity','atmospheric pressure',
    'wind speed','cloud']
    room_variables = ['room temperature','room humidity']
    out_variables = ['local temperature','local humidity','atmospheric pressure','wind speed','cloud']

    current_date = request.args.get("dates")
    current_interval = request.args.get("intervals")
    current_variable = request.args.get("variables")

    if current_interval == None:
        current_interval = "15min"
    if current_date == None:
        current_date = str(datetime.today().strftime('%Y-%m-%d'))
    if current_variable == None:
        current_variable = 'room temperature'

    date = current_date[8:10]+current_date[5:7]+current_date[0:4]

    sound_date = time_select(sound_df,date)
    room_date = time_select(room_df,date)
    out_date = time_select(out_df,date)

    if current_variable in room_variables:
        col = room_date[current_variable]
    elif current_variable in out_variables:
        col = out_date[current_variable]

    sound_all = time_series_sound(sound_df['Trigger bool'], current_interval,"sound number change")
    room_temp = time_series(room_df['room temperature'],current_interval,"room temperature change")
    out_atm = time_series(out_df['atmospheric pressure'],current_interval,"atmospheric pressure change")

    sound_date = time_series_sound(sound_date['Trigger bool'], current_interval,"sound number change")
    other_date = time_series(col, current_interval, col.name + " " + "change")

    s1,div1 = components(sound_date)
    s2,div2 = components(other_date)
    s3,div3 = components(sound_all)
    s4,div4 = components(room_temp)
    s5,div5 = components(out_atm)
    return render_template('timeline.html', title="TimeLine", s1=s1,div1=div1,s2=s2,div2=div2,s3=s3,div3=div3,
    s4=s4,div4=div4,s5=s5,div5=div5,intervals=intervals,current_variable = current_variable, variables=variables,
    current_interval=current_interval,dates=dates, current_date=current_date)

@app.route('/insight/', methods=['GET'])
def insight():
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('SIOTfinal.json', scope)
    client = gspread.authorize(creds)
    sound_g = client.open('sound').sheet1
    room_g = client.open('room').sheet1
    outside_g = client.open('outside').sheet1
    room_df = get_room_temp(room_g)
    out_df = get_outside_temp(outside_g)
    sound_df = get_sound(sound_g)

    intervals = ["15min","30min", "1h", "4h"]
    dates = []
    dates_obj=[]
    all_date = sound_df.resample('D').sum()
    for i in range(len(all_date.index)):
        dates.append(str(all_date.index[i].strftime('%Y-%m-%d')))
        dates_obj.append(all_date.index[i])
    dates = dates[1:]
    dates_obj = dates_obj[1:]
    variables = ['room temperature','room humidity','local temperature','local humidity','atmospheric pressure',
    'wind speed','cloud']
    room_variables = ['room temperature','room humidity']
    out_variables = ['local temperature','local humidity','atmospheric pressure','wind speed','cloud']

    current_date = request.args.get("dates")
    current_interval = request.args.get("intervals")
    current_variable = request.args.get("variables")

    if current_interval == None:
        current_interval = "15min"
    if current_date == None:
        current_date = str(datetime.today().strftime('%Y-%m-%d'))
    if current_variable == None:
        current_variable = 'room temperature'

    date = current_date[8:10]+current_date[5:7]+current_date[0:4]

    sound_date = time_select(sound_df,date)
    room_date = time_select(room_df,date)
    out_date = time_select(out_df,date)

    if current_variable in room_variables:
        col = room_date[current_variable]
    elif current_variable in out_variables:
        col = out_date[current_variable]

    relation_plot = sound_line(sound_date['Trigger bool'], col, current_interval)
    correlation_plot = correlation(dates_obj,sound_df,room_df,out_df)

    s1,div1 = components(relation_plot)
    s2,div2 = components(correlation_plot)

    return render_template('insight.html', title="Insight", s1=s1,div1=div1,s2=s2,div2=div2,
    intervals=intervals,
    current_variable = current_variable, variables=variables,current_interval=current_interval,
    dates=dates, current_date=current_date)

if __name__ == "__main__":
    app.run(debug=True)
