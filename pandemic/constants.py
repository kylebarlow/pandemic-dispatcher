# coding=utf-8

# file of constants to keep things readable

from collections import OrderedDict

CITIES = OrderedDict([
    (u'Atlanta', u'blue'), (u'Chicago', u'blue'), (u'Essen', u'blue'), (u'London', u'blue'), (u'Madrid', u'blue'),
    (u'Milan', u'blue'), (u'Montreal', u'blue'), (u'New York', u'blue'), (u'Paris', u'blue'),
    (u'San Francisco', u'blue'), (u'St. Petersburg', u'blue'), (u'Washington', u'blue'),

    (u'Bogotá', u'yellow'), (u'Buenos Aires', u'yellow'), (u'Johannesburg', u'yellow'), (u'Khartoum', u'yellow'),
    (u'Kinshasa', u'yellow'), (u'Lagos', u'yellow'), (u'Lima', u'yellow'), (u'Los Angeles', u'yellow'),
    (u'Mexico City', u'yellow'), (u'Miami', u'yellow'), (u'Santiago', u'yellow'), (u'São Paulo', u'yellow'),

    (u'Algiers', u'black'), (u'Baghdad', u'black'), (u'Cairo', u'black'), (u'Chennai', u'black'), (u'Delhi', u'black'),
    (u'Istanbul', u'black'), (u'Karachi', u'black'), (u'Kolkata', u'black'), (u'Moscow', u'black'),
    (u'Mumbai', u'black'), (u'Riyadh', u'black'), (u'Tehran', u'black'),

    (u'Bangkok', u'red'), (u'Beijing', u'red'), (u'Ho Chi Minh City', u'red'), (u'Hong Kong', u'red'),
    (u'Jakarta', u'red'), (u'Manila', u'red'), (u'Osaka', u'red'), (u'Seoul', u'red'), (u'Shanghai', u'red'),
    (u'Sydney', u'red'), (u'Taipei', u'red'), (u'Tokyo', u'red')
])

# months in the year
MONTHS = [u'January', u'February', u'March', u'April', u'May', u'June',
          u'July', u'August', u'September', u'October', u'November', u'December']

INFECTION_RATES = [2, 2, 2, 3, 3, 4, 4, 9] # infection rates per epidemic
                                           # note: -1 is game setup, infect 9 cities

EPIDEMICS = 5 # number of epidemics in the deck
PLAYERS = 4 # four players, of course
DRAW = 2 # draw two cards at a time
CODA_COLOR = u'yellow' # color of the COdA virus
