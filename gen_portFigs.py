__author__= 'gianluca'

# imports
import numpy as np
import requests
import datetime
from datetime import date

import cProfile
import re
from tiingo import TiingoClient

from gen_portStats import *

# this date range will be provided by parseCSV
sDate = date(2015,12,31) 
eDate = date.today()-timedelta(1)

