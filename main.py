import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from bokeh.embed import components
from flask import Flask, render_template, request
from random import randint

from utils import time_select,normalise,scatter_line_plot,bar_line_plot,sound_line,sound_freq
from fetch import get_sound,get_room_temp,get_outside_temp,get_pokemon,get_pokemon_random,get_outside_temperature,sleep_tip

app = Flask(__name__)

#@app.route("/<date>/", methods=['GET', 'POST'])
@app.route('/', methods=['GET'])
#def master(date):
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

@app.route('/insight/', methods=['GET'])
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

    return render_template('insight.html', day_sel=today, day_bef=yesterday, the_div=div, the_script=script,
    stat=stat, temp=temp, wind=wind,
    pressure=pressure, humidity=humidity, cloud=cloud, script2=script2, div2=div2, intervals=intervals,
    current_interval=current_interval, current_variable = current_variable, variables=variables,
    dates=dates, current_date=current_date, trigger_num=trig_num)

if __name__ == "__main__":
    app.run(debug=True)
