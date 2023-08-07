from astroplan import Observer
from astroplan import FixedTarget
import astropy
import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates

import dino_tools as tools

def plot(observer, times, targets, do_moon=True, do_moon_labels=True,
                 path="./report_plots"):
    # do airmass plot
    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches(10, 5)
    #ax2.set_aspect('equal', adjustable='box')
    
    if type(targets) != list:
        target_list = [targets]
    else:
        target_list = targets
    
    #xlo, xhi = (times['plot_window'][0]), (times['plot_window'][-1])
    #ax.set_xlim([xlo.plot_date, xhi.plot_date])
    #date_formatter = dates.DateFormatter('%d %H:%M')
    #ax.xaxis.set_major_formatter(date_formatter)
    plt.setp(ax.get_xticklabels(), rotation=20, ha='right')
    
    # vertical lines for times
    #ax.axvline(times['obs_window'][0].to_datetime())
    #ax.axvline(times['obs_window'][-1].to_datetime())
    ax.axvline(times['civ_twl'][0].to_datetime(),
               linestyle=':', alpha=0.4,
               color="xkcd:grey", label="Civil Twilight")
    ax.axvline(times['civ_twl'][1].to_datetime(),
               linestyle=':', alpha=0.4,
               color="xkcd:grey")
    ax.axvline(times['nau_twl'][0].to_datetime(),
               linestyle='--', alpha=0.6,
               color="xkcd:grey", label="Nautical Twilight")
    ax.axvline(times['nau_twl'][1].to_datetime(),
               linestyle='--', alpha=0.6,
               color="xkcd:grey")
    ax.axvline(times['ast_twl'][0].to_datetime(),
               linestyle='-', alpha=0.8,
               color="xkcd:grey", label="Astronomical Twilight")
    ax.axvline(times['ast_twl'][1].to_datetime(),
               linestyle='-', alpha=0.8,
               color="xkcd:grey")
    
    if do_moon:
        alt = []
        for time in times['plot_window']:
            moon = FixedTarget(name="Moon",
                               coord=astropy.coordinates.get_moon(time))
            alt.append(observer.altaz(time, moon).alt)
        moon_alts = astropy.coordinates.Latitude(alt, unit=u.deg)
        mm_alts = np.ma.array(moon_alts, mask=moon_alts < 0)
        ax.plot(times['plot_window'].to_datetime(), mm_alts, label='Moon',
                marker=None, linestyle="--", color="xkcd:black", linewidth=2,
                alpha=0.8)
    
    for i in range(0, len(target_list)):
        target = target_list[i]['target']
        color = target_list[i]['color']
        if target_list[i]['type'] != "fixed":
            #continue
            alt = []
            for time in times['plot_window']:
                target, marker = tools._setup_non_fixed_target(target_list[i], time,
                                                         observer.location)
                alt.append(observer.altaz(time, target).alt)
            altitude = astropy.coordinates.Latitude(alt, unit=u.deg)
        else:
            # calculate altitude
            altitude = observer.altaz(times['plot_window'], target).alt
        
        # Mask out nonsense altitude/airmass
        masked_altitude = np.ma.array(altitude, mask=altitude < 0)
        
        ax.plot(times['plot_window'].to_datetime(),
                masked_altitude, label=target_list[i]['name'],
                marker=None, linestyle="-", color=color, linewidth=2)
        
        # handle moon separation numbers
        if do_moon_labels:
            this_window = times['plot_window'][5:-6]
            these_alts  = masked_altitude[5:-6]
            n_times = len(this_window)
            for j in range(0, n_times, n_times//13):
                time = this_window[j]
                c1 = target.coord
                c2 = astropy.coordinates.get_moon(time)

                # important! separation gives the angle in the frame of the
                # first SkyCoord object, which must be the moon here
                d = c2.separation(c1)
                
                if type(these_alts[j]) == astropy.coordinates.angles.Latitude:
                    this_y = these_alts[j].value
                    ax.text(x=time.to_datetime(), y=this_y,
                        s=d.to_string(unit=u.deg, decimal=True, precision=1))
                else:
                    continue
                
                
    
    # shading for blocks
    if times['blocks'] != None:
        for block in times['blocks']:
            ax.axvspan(mdates.date2num(block['times'][0].to_datetime()),
                       mdates.date2num(block['times'][-1].to_datetime()),
                       alpha=0.3, color=block['color'])

    # xtick formatting
    ax.xaxis.set_major_locator(mdates.HourLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.set_xlim(times['sunset'].to_datetime(), times['sunrise'].to_datetime())
    #ax.set_xlim(times['plot_window'].to_datetime(), times['sunrise'].to_datetime())
    ax.set_xlabel("Time (UTC)")

    #  ytick formatting 
    alt_ticks = np.array([90, 80, 70, 60, 50, 40, 30, 20, 10, 0])
    air_ticks = 1./np.cos(np.radians(90 - alt_ticks))
    
    # altitude ticks
    ax.set_yticks(alt_ticks)
    ax.set_yticklabels([u'{0}\N{DEGREE SIGN}'.format(a) for a in alt_ticks])
    ax.set_ylim(0, 95)
    ax.set_ylabel('Altitude')
    
    # airmass ticks
    ax2 = ax.twinx()
    ax2.set_yticks(alt_ticks[:-1])
    ax2.set_yticklabels(["{0:.2f}".format(a) for a in air_ticks[:-1]])
    ax2.set_ylim(ax.get_ylim())
    ax2.set_ylabel('Airmass')
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True,
              ncol=3, framealpha=0, fontsize=12)
    
    plt.savefig('{0}/airmass.jpg'.format(path), bbox_inches='tight')
    plt.close()
    return fig