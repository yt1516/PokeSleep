import pandas as pd
from datetime import datetime
from random import randint
from pokedex import pokedex
import pyowm

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

def get_pokemon(trigger_num):
    p_dex = pokedex.Pokedex(version='v1', user_agent='ExampleApp (https://example.com, v2.0.1)')
    pokemon = p_dex.get_pokemon_by_number(trigger_num)
    name = pokemon[0]['name']
    description = pokemon[0]['description']
    url = pokemon[0]['sprite']
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
