import numpy as np
import pandas as pd

import astropy
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import EarthLocation
from astropy.time import Time
from astropy.time import TimeDelta
from astropy.coordinates import AltAz
from astropy.coordinates import solar_system_ephemeris
from astropy.coordinates import get_body
#from astropy.wcs import WCS

import astroplan
from astroplan import Observer
from astroplan import FixedTarget

#import matplotlib as mpl
#import matplotlib.pyplot as plt
#import matplotlib.image as mpl_image
#from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
#from matplotlib.artist import Artist
#from matplotlib.patches import Rectangle
#from matplotlib import dates
#import matplotlib.dates as mdates
#from matplotlib.ticker import FormatStrFormatter

import seaborn as sns
#from seaborn import desaturate

from astroquery.jplhorizons import Horizons

from datetime import timezone
from datetime import datetime

#import cartopy.crs as ccrs

import warnings

def get_ephemerides(target_id, id_type, time=None, location=None):
    """
    Credit rmquimby on GitHub. This function is taken from their
    rock_finding_chart.py program
    
    wrapper to query Horizons and return the object ephemerides.
    
    With `id_type = 'smallbody'`, you can specify the object by name
    e.g.,  `target_id = 'C/2019 Q4'` or `target_id = '2000 WK63'`
    
    With `id_type = 'id'`, you can specify the object by its ID number
    e.g., `target_id = '90000392'`
    
    `time` -- (optional) should be specified as an astropy.time.Time object
    
    `location` -- (optional) should be an astropy.coordinates.EarthLocation
    """
    if time is None:
        # use current time by default
        time = Time.now()   
    obj = Horizons(id=target_id, id_type=id_type, location=location,
                   epochs=time.jd)
    return obj.ephemerides()

def _setup_non_fixed_target(target_dict, time, location):
    """
    Sets up a single non-fixed target at a single time at a single location.
    """
    this_type = target_dict['type']
    this_name = target_dict['name']
    target = None
    marker = None
    
    if this_type == "smallbody":
        target_eph = get_ephemerides(this_name, "smallbody", time=time)
        target = FixedTarget(name=this_name,
                             coord=SkyCoord(ra=target_eph['RA'],
                                            dec=target_eph['DEC'])[0])
        marker = "d"
    elif this_type == "majorbody":
        target_eph = get_ephemerides(this_name, None, time=time)
        target = FixedTarget(name=this_name,
                             coord=SkyCoord(ra=target_eph['RA'],
                                            dec=target_eph['DEC'])[0])
        marker = "s"
    elif this_type == "planet":
        target = FixedTarget(name=this_name,
                             coord=get_body(this_name, time, location))
        marker = "o"

    return target, marker

def setup_target_list(target_ids, location):
    """
    Sets up the targets in a list of dicts containing the relevant information
    """
    targets = []
    n_targets = len(target_ids)
    #cmap = plt.cm.get_cmap('hsv', n_targets)
    cmap = sns.color_palette("husl", n_targets)
    for i in range(0, n_targets):
        # see if this is a solar-system target
        this_type = None
        this_target = None
        try:
            target_eph = get_ephemerides(target_ids[i], 'smallbody')
            this_type = "smallbody"
            this_name = target_ids[i]
        except:
            # maybe it's a major body?
            try:
                target_eph = get_ephemerides(target_ids[i], None)
                this_type = "majorbody"
                this_name = target_ids[i]
            except:
                # maybe it's a planet? (Horizons gets upset about planet names)
                try:
                    target_coord = get_body(target_ids[i], Time.now(),
                                            location.location) 
                    this_type = "planet"
                    this_name = target_ids[i]
                except:
                    # if not a solar system target, make a FixedTarget directly
                    try:
                        this_target = FixedTarget.from_name(target_ids[i])
                        this_type = "fixed"
                        this_name = target_ids[i]
                    except:
                        ra, dec, this_name = target_ids[i].split()
                        this_coord = SkyCoord(ra=ra, dec=dec, unit=(u.hourangle, u.deg))
                        this_target = FixedTarget(this_coord, name=this_name)
                        this_type = "fixed"
        
        # give this target a color
        this_color = cmap[i]
        this_dict = {"target":this_target, "color":this_color,
                     "type":this_type, "name":this_name}
        targets.append(this_dict)
    return targets

def setup_times(observer, obs_start, obs_end=None, block_start_times=None,
                block_end_times=None, block_colors=None):
    """
    Sets up a times dictionary for the night which includes the observing window
    but also the twilight times, and information about observing blocks if any.
    """
    start = Time(obs_start)
    end = Time(obs_end)
    times = {
        'sunrise':observer.sun_rise_time(start, which='next'),
        'sunset':observer.sun_set_time(start, which='previous'),
        'civ_twl':[observer.twilight_evening_civil(start, which='previous'),
                   observer.twilight_morning_civil(start, which='next')],
        'nau_twl':[observer.twilight_evening_nautical(start, which='previous'),
                   observer.twilight_morning_nautical(start, which='next')],
        'ast_twl':[observer.twilight_evening_astronomical(start,
                                                              which='previous'),
                   observer.twilight_morning_astronomical(start, which='next')],
        'blocks':None
    }
    # calculate the window for plotting
    ps = Time(times['sunset'] - TimeDelta(0*u.h), format='iso')
    pe = Time(times['sunrise'] + TimeDelta(0*u.h), format='iso')
    times['plot_window'] = (ps + (pe - ps)*np.linspace(0, 1, 100))
    
    if end != None:
        times['obs_window'] = start + (end - start)*np.linspace(0, 1, 10)
    else:
        times['obs_window'] = start
    
    if block_start_times != None:
        n_blocks = len(block_start_times)
        if block_colors == None:
            cmap = sns.color_palette("muted", n_blocks)
        else:
            cmap = block_colors
        times['blocks'] = []
        for i in range(0, n_blocks):
            block = {}
            bs = Time(block_start_times[i])
            if block_end_times != None:
                be = Time(block_end_times[i])
            else:
                try:
                    be = Time(block_start_times[i+1])
                except:
                    be = end
            #block['times'] = bs + (be - bs)*np.linspace(0, 1, 100)
            block['times'] = [bs, be]
            block['color'] = cmap[i]
            times['blocks'].append(block)
            
    
    return times

def setup_location(observer_name, lat=None, long=None, elev=None, tz=None):
    """
    Setup the observer location based on selection of pre-defined names
    """
    me_irl = None
    
    if observer_name == "Aarhus":
        location = EarthLocation.from_geodetic(10.18917*u.deg, 56.19694*u.deg,
                                               68*u.m)
        me_irl = Observer(location=location, name=observer_name,
                          timezone="Etc/GMT+1")
    elif observer_name == "NOT" or observer_name == "Nordic Optical Telescope":
        location = EarthLocation.from_geodetic(-17.884999999999998*u.deg,
                                               28.7569444*u.deg, 2383*u.m)
        me_irl = Observer(location=location, name=observer_name, timezone="GMT")
    else: # custom observer
        location = EarthLocation.from_geodetic(lat*u.deg, long*u.deg, elev*u.m)
        me_irl = Observer(location=location, name=observer_name, timezone=tz)
        
    return me_irl
