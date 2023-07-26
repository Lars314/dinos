import cartopy.crs as ccrs
import astropy
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
import matplotlib.pyplot as plt
import pandas as pd
from seaborn import desaturate
import numpy as np
import matplotlib.image as mpl_image
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)
from matplotlib.artist import Artist
from matplotlib.patches import Rectangle
from matplotlib import dates
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter
from astroplan import FixedTarget

def plot(targets=None, do_stars=True, do_asterisms=True,
             do_constellations=False, do_moon=True, do_time_text=False,
             times=None, observer=None, projection=ccrs.Mollweide(),
             sky_culture="rey", do_xticks=False, do_yticks=True, mag_limit=8.5, 
             path="./report_plots", star_marker="o", ax_color="xkcd:black", 
             fig_color="xkcd:white", do_title=True, do_legend=True,
             target_marker="*", do_target_colors=True):
    """
    Create a plot of the celestial sphere, with the targets of interest
    
    Parameters
    -----------
    
    targets : list of FixedTarget objects
        The objects you want to observe.
        Defaults to None.
    
    do_stars : bool
        Enable plotting the stars.
        Defaults to True.
        
    mag_limit : float
        The dimmest magnitude that will be plotted if do_stars is True. High
        values may cause significant run times. Going past 10 gets into some
        serious diminishing returns, but you can go up to 21 with these data if 
        you really want. Lowest magnitude in the data is -1.44 FYI.
        Defaults to 8.5.
        
    star_marker : str
        The marker for the background stars. Follows the same list as plt
        markerstyles.
        Defaults to "o".
        
    target_marker : 
        
    do_asterisms : bool
        Enable plotting the asterisms or not. Asterisms are the lines that most
        people associate with the constellations.
        Defaults to True.
       
    do_constellations : bool
        Enable plotting the constellations or not. The constellations are not
        the lines that most people associate with constellations, but rather
        the borders on the sky in which those lines are found. To plot the
        lines and get nice images, use do_asterisms=True.
        Defaults to False.
        
    do_moon : bool
        Enable plotting the moon at the times given by the times parameter.
        Defaults to False.
        
    do_time_text : 
        
    do_galactic_plane : 
        
    times : list of datetime objects
        The times at which the moon should be plotted.
        Defaults to Time.Now(), the current UTC time.
        
    observer : 
    
    projection : 
    
    culture : 
    
    do_xticks : 
    
    do_yticks : 
    
    do_title : 
    
    do_legend : 
    
    path : 
    
    ax_color : 
    
    fig_color : 
    
    do_target_colors : 

    """

    # check if we use one time or several
    try:
        iter(times['obs_window'])
        time_list = times['obs_window']
    except:
        if times == None:
            time_list = [Time.now()]
        else:
            time_list = [times['obs_window']]
        
    """try:
        iter(times)
        time_list = times
    except:
        if times == None:
            times = Time.now()
        time_list = [times]"""
    
    const_color = '#ff2620'
    zodiac_color = '#fcb322'
    nonzodiac_color = '#77a9da'
    other_color = '#979330'
    
    plt.rc('figure', dpi=250)
    fig = plt.figure(figsize=(30, 15), facecolor=fig_color)
    ax = plt.axes(projection=ccrs.Mollweide())
    ax.set_facecolor(ax_color)
    draw_labels=[]
    if do_xticks:
        draw_labels += ["x"]
        gl = ax.gridlines(draw_labels=draw_labels, alpha=0.4,
                  xlocs=range(-180, 180, 15), x_inline=True,
                  ylocs=range(-90, 90, 15))
        gl.xlabel_style = {'size':15}
    if do_yticks:
        draw_labels += ["y",  "left", "right","geo"]
        gl = ax.gridlines(draw_labels=draw_labels, alpha=0.4,
                          xlocs=range(-180, 180, 15), x_inline=False,
                          ylocs=range(-90, 90, 15))
        gl.ylabel_style = {'size': 15}
    
    if do_constellations:
        constellations = pd.read_csv('./data/processed/constellations.csv')
        for index, row in constellations.iterrows():
            ras = [float(x)*360/24 for x in 
                   row['ra'].replace('[', '').replace(']', '').split(',')]
            decs = [float(x) for x in
                    row['dec'].replace('[', '').replace(']', '').split(',')]
            ax.plot(ras, decs, transform=ccrs.Geodetic(), lw=0.5, alpha=0.7,
                    color=const_color)
        
    if do_asterisms:
        if sky_culture == "rey":
            asterisms = pd.read_csv('./data/processed/asterisms_rey.csv')
        elif sky_culture == "IAU":
            asterisms = pd.read_csv('./data/processed/asterisms_rey.csv')
        else:
            warnings.warn("Sky culture {0} is unrecognized in this version. " + 
                          "Defaulting to the H.A. Rey " +
                          "asterisms".format(sky_culture))
            asterisms = pd.read_csv('./data/processed/asterisms_rey.csv')
            
        for index, row in asterisms.iterrows():
            ras = [float(x)*360/24 for x in
                   row['ra'].replace('[', '').replace(']', '').split(',')]
            decs = [float(x) for x in
                    row['dec'].replace('[', '').replace(']', '').split(',')]
            color = nonzodiac_color
            if row['zodiac'] == True: 
                color = zodiac_color
            assert len(asterisms)%2 == 0
            for n in range(int(len(asterisms)/2)):
                ax.plot(ras[n*2:(n+1)*2], decs[n*2:(n+1)*2],
                        transform=ccrs.Geodetic(), color=color, lw=0.75)
        
    if do_stars:
        stars = pd.read_csv('./data/processed/hygdata_processed.csv')
        stars_plot = stars[(stars['color'] != '#000000') & 
                           (stars['mag'] < mag_limit)].copy()
        
        stars_plot['c'] = [desaturate(c, 0.75) for c in stars_plot['color']]
        stars_plot['s'] = [35*np.exp(-(1.44 + m)/(4)) for m in stars_plot['mag']]
        stars_plot['alpha'] = [min(1, 0.6-np.arctan((m-4)/5)/(np.pi)) for m in stars_plot['mag']]
        #stars_plot['alpha'] = [min(1, np.exp(-(1.44 + m)/(8))) for m in stars_plot['mag']]
        #print(stars_plot['alpha'])
        ax.scatter(stars_plot['ra']*360/24, stars_plot['dec'], transform=ccrs.Geodetic(),
                   s=stars_plot['s'], color=stars_plot['c'], lw=0, edgecolor='none', 
                   alpha=stars_plot['alpha'], marker=star_marker)

    if targets is not None:
        if type(targets) != list:
            target_list = [targets]
        else:
            target_list = targets
        for i in range(0, len(target_list)):
            target = target_list[i]['target']
            if do_target_colors:
                color = target_list[i]['color']
            else:
                color = "xkcd:white"
                
            if target_list[i]['type'] == "fixed":
                ax.plot(target.coord.ra, target.coord.dec,
                        transform=ccrs.Geodetic(),
                        marker=target_marker, markersize=12, linestyle='none',
                        color=color, label=target.name)
                ax.text(x=(target.coord.ra-3*u.deg).value,
                        y=(target.coord.dec).value,
                        s=target.name, transform=ccrs.Geodetic(),
                        color=color, size=20)
            else:
                for time in time_list:
                    if observer is None:
                        warnings.warn("You have a non-fixed target, but did not specify an observing location!")
                    # "tat" stands for "target at time"
                    tat, marker = _setup_non_fixed_target(target_list[i], time,
                                                          observer.location)
                    ax.plot(tat.coord.ra, tat.coord.dec,
                            transform=ccrs.Geodetic(), marker=marker,
                            markersize=7, linestyle='none', color=color,
                            label=tat.name)
                    if do_time_text:
                        text = tat.name + "\n" + time.strftime("%m-%d %H:%M:%S")
                    else:
                        text = tat.name
                    ax.text(x=(tat.coord.ra-3*u.deg).value,
                            y=(tat.coord.dec).value,
                            s=text, transform=ccrs.Geodetic(), color=color,
                            size=20)

    if do_moon:
        moon_cartoon = mpl_image.imread("./report_images/moon.png")
        imagebox = OffsetImage(moon_cartoon, zoom=0.15)
        imagebox.image.axes = ax
        
        for time in time_list:
            # get the moon's location
            moon = FixedTarget(name="Moon",
                               coord=astropy.coordinates.get_moon(time))
            
            # place the moon image
            transform = ccrs.Geodetic()._as_mpl_transform(ax)
            ab = AnnotationBbox(imagebox,
                                (moon.coord.ra.value, moon.coord.dec.value),
                                frameon=False, xycoords=transform)
            ax.add_artist(ab)
            
            if do_time_text:
                ax.text(x=(moon.coord.ra-4*u.deg).value, y=moon.coord.dec.value,
                        s=time.strftime("%m-%d %H:%M:%S"),
                        transform=ccrs.Geodetic(), color="xkcd:white")
        
    if observer != None:
        az_range = np.linspace(0, 360, 360)
        ras = []
        decs = []
        for az in az_range:
            coords = SkyCoord(AltAz(alt=0*u.deg, az=az*u.deg,
                                    obstime=time_list[0],
                                    location=observer.location))
            ras.append(coords.icrs.ra.value)
            decs.append(coords.icrs.dec.value)
        ax.plot(ras, decs, transform=ccrs.Geodetic(),
                lw=1, alpha=1, color="xkcd:green", label="Observation Start")
        if len(time_list) > 1:
            # do the end of the night too
            ras = []
            decs = []
            for az in az_range:
                coords = SkyCoord(AltAz(alt=0*u.deg, az=az*u.deg,
                                        obstime=time_list[-1],
                                        location=observer.location))
                ras.append(coords.icrs.ra.value)
                decs.append(coords.icrs.dec.value)
            ax.plot(ras, decs, transform=ccrs.Geodetic(),
                    lw=1, alpha=1, color="xkcd:pale green",
                    label="Observation End")
            
    if do_legend:
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper center',
                  bbox_to_anchor=(0.5, -0.005), fancybox=True, ncol=5,
                  framealpha=1, fontsize=20, labelcolor='linecolor',
                  facecolor="xkcd:white", edgecolor="xkcd:grey")

    ax.set_xlim(ax.get_xlim()[::-1])
    if do_title:
        if len(time_list) > 1:
            formatter = "%Y-%m-%d"
            text = "All-Sky Map {0}"
        else:
            formatter = "%Y-%m-%d %H:%M:%S"
            text = "All-Sky Map {0} (UTC)"
        ax.set_title(text.format(time_list[0].strftime(formatter)),
                     fontsize=32, pad=20)
        if fig_color == "xkcd:black":
            ax.title.set_color("xkcd:white")
    plt.savefig('{0}/all_sky_map.jpg'.format(path), facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close()
    return fig