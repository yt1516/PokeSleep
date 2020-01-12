from oauth2client.service_account import ServiceAccountCredentials
import Adafruit_DHT
import pyowm
from pokedex import pokedex
from datetime import datetime

light = 14
sound = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(light, GPIO.IN)
GPIO.setup(sound, GPIO.IN, pull_up_down=GPIO.PUD_UP)

count=0
trigger=True
date = str(datetime.today().date())

legendary = [144,145,146,150,151,243,244,245,249,250,251,377,378,379,380,
             381,382,383,384,385,386,480,481,482,483,484,485,486,487,488,
             489,490,491,492,493,494,638,639,640,641,642,643,644,645,646,
             647,648,649]
non_legendary = list(range(1,808))
for i in non_legendary[:]:
    if i in legendary:
        non_legendary.remove(i)


def register_sound(channel):
    global count
    count = count+1
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('SIOTfinal.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('sound').sheet1
    now = datetime.now()
    stamp = "{0:%Y}-{0:%m}-{0:%d}_{0:%H}.{0:%M}.{0:%S}".format(now)
    row = [stamp,"trigger"]
    sheet.insert_row(row,1)

def record_temp(sheet2):
    humidity, temperature = Adafruit_DHT.read_retry(11, 4)
    now = datetime.now()
    stamp = "{0:%Y}-{0:%m}-{0:%d}_{0:%H}.{0:%M}.{0:%S}".format(now)
    row = [stamp,temperature, humidity]
    sheet2.insert_row(row,1)
    print("Latest Temperature is:", temperature)

def record_outside(sheet3,temp,wind,humidity,cloud,pressure,stat):
    now = datetime.now()
    stamp = "{0:%Y}-{0:%m}-{0:%d}_{0:%H}.{0:%M}.{0:%S}".format(now)
    row = [stamp,temp,humidity,pressure,wind,cloud,stat]
    sheet3.insert_row(row,1)
    print("Current weather is:", row)

def add_pokemon_dynamic(trigger_num, average,date, base, legendary=legendary, non_legendary=non_legendary):
    if trigger_num <= average:
        base = base+10
        if base >= 500:
            base = 500
    elif trigger_num >= average * 1.2:
        base = base-10
        if base <= 50:
            base = 50
    ones = base + int(200*(average-trigger_num)/average)
    p_list = [0 for i in range(1,1001)]
    for i in range(ones):
        p_list[i]=1
    select = p_list[randint(1,1000)]
    if select == 1:
        dex=legendary[randint(0,len(legendary))]
    elif select == 0:
        dex=non_legendary[randint(0,len(non_legendary))]
    p_dex = pokedex.Pokedex(version='v1', user_agent='ExampleApp (https://example.com, v2.0.1)')
    pokemon = p_dex.get_pokemon_by_number(dex)
    name = pokemon[0]['name']
    description = pokemon[0]['description']
    url = pokemon[0]['sprite']

    row = [date, name, description, url, trigger_num]
    poke_data.insert_row(row,1)
    poke_data.update_cell(1,6,str(base))

while trigger:
    time.sleep(1)
    if GPIO.input(14) == 0:
        trigger = False

start = time.time()
run_period = 21600

try:
    while True:
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('google_api.json', scope)
        client = gspread.authorize(creds)
        owm = pyowm.OWM('2a9f05a9458a49c59d610b54ed02a840')
        sheet2 = client.open('room').sheet1
        sheet3 = client.open('outside').sheet1
        record_temp(sheet2)
        observation = owm.weather_at_coords(51.7562368,0.4894240)
        w = observation.get_weather()
        record_outside(sheet3,w.get_temperature('celsius')['temp'],w.get_wind()['speed'],w.get_humidity(),w.get_clouds(),w.get_pressure()['press'],w.get_status())
        time.sleep(900)
        if time.time() > start + run_period : break
    poke_data = client.open('pokemon').sheet1
    base = int(poke_data.cell(1,6).value)
    average = mean([int(i) for i in poke_data.col_values(5)])
    add_pokemon_dynamic(count,average,date,base)
except Exception,e:
    print(e)
    GPIO.cleanup()
