# DE4 SIOT Coursework - PokeSleep
A sound sensor based sleep monitoring device that lets you catch Pokemon during sleep.

Video Link: https://youtu.be/dEb5gJz3n9o

# Running The Code
clone the repository: ```git clone https://github.com/yt1516/PokeSleep.git```

cd into the directory: ```cd PokeSleep```

install all required packages: ```pip install -r requirements.txt```

execute the Python script: ```python main.py```

Then open a new web browser page, go to the url shown in terminal, the default is: *127.0.0.1:5000*

# Application Structure
```LDR_sense.ino``` contains the script running on the Arduino for converting analog LDR readings to digital signal and send to the Pi

```sensing.py``` is run on the Pi with cron service which runs every day at 11 pm.

```database_12012020``` contains An example of the datasets stored in Google Sheet
