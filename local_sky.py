import astropy.units as u
import numpy as np
import matplotlib.pyplot as plt
import dino_tools as tools
from astroplan import Observer
from astroplan import FixedTarget

def plot(observer, times, targets, do_moon=False, do_grid=True,
             az_label_offset=0.0*u.deg, path="./report_plots"):
    """
    can take a single time or multiple
    """
    #plt.rcParams["figure.figsize"] = (15, 15)
    fig, ax = plt.subplots(ncols=1, subplot_kw={'projection':'polar'})
    #ax = plt.subplot(121, projection='polar')
    #fig, ax = plt.subplots(1, 1)
    ax.set_rlim(90, 0)
    #ax.set_rticks([30, 60, 90])
    ax.set_theta_zero_location('N')
    
    if type(targets) != list:
        target_list = [targets]
    else:
        target_list = targets

    try:
        iter(times['obs_window'])
        time_list = times['obs_window']
    except:
        time_list = [times['obs_window']]
        
    for i in range(0, len(target_list)):
        target = target_list[i]['target']
        az = []
        alt = []
        for time in time_list:
            if target_list[i]['type'] != "fixed":
                target, marker = tools._setup_non_fixed_target(target_list[i],
                                                            time,
                                                            observer.location)
            altitude = (observer.altaz(time, target).alt) * (1/u.deg)
            azimuth = observer.altaz(time, target).az * (1/u.deg) * \
                      (np.pi/180.0)

            alt.append(altitude)
            az.append(azimuth)

        color = target_list[i]['color']

        ax.scatter(az, alt, marker='o', facecolors='none', edgecolors=color)
        ax.plot(az[0], alt[0], marker='o', label=target.name, color=color,
                linestyle='none')

    if do_moon:
        alt = []
        az = []
        for time in time_list:
            moon = FixedTarget(name="Moon",
                               coord=astropy.coordinates.get_moon(time))
            altitude = (observer.altaz(time, moon).alt) * (1/u.deg)
            azimuth = observer.altaz(time, moon).az * (1/u.deg) * (np.pi/180.0)

            alt.append(altitude)
            az.append(azimuth)

        ax.scatter(az, alt, marker='o', facecolors='none',
                   edgecolors="xkcd:grey")
        ax.plot(az[0], alt[0], marker='o', label=moon.name, color="xkcd:grey",
                linestyle='none')

    # Grid, ticks & labels.
    # May need to set ticks and labels AFTER plotting points.
    if do_grid is True:
        ax.grid(True, which='major')
    else:
        ax.grid(False)
    degree_sign = u'\N{DEGREE SIGN}'

    # For positively-increasing range (e.g., range(1, 90, 15)),
    # labels go from middle to outside.
    r_labels = [
        '0' + degree_sign,
        '',
        '30' + degree_sign,
        '',
        '60' + degree_sign,
        '',
        '90' + degree_sign + ' Alt.',
    ]

    theta_labels = []
    for chunk in range(0, 7):
        label_angle = (az_label_offset*(1/u.deg)) + (chunk*45.0)
        while label_angle >= 360.0:
            label_angle -= 360.0
        if chunk == 0:
            theta_labels.append('N ' + '\n' + str(label_angle) + degree_sign
                                + ' Az')
        elif chunk == 2:
            theta_labels.append('E' + '\n' + str(label_angle) + degree_sign)
        elif chunk == 4:
            theta_labels.append('S' + '\n' + str(label_angle) + degree_sign)
        elif chunk == 6:
            theta_labels.append('W' + '\n' + str(label_angle) + degree_sign)
        else:
            theta_labels.append(str(label_angle) + degree_sign)
    theta_labels.append('')
    # Set ticks and labels.
    ax.set_rgrids(range(1, 106, 15), r_labels, angle=-45)
    ax.set_thetagrids(range(0, 360, 45), theta_labels)
        
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), fancybox=True,
                  ncol=3, framealpha=0, fontsize=12)
    plt.savefig('{0}/local_sky.jpg'.format(path), bbox_inches='tight')
    plt.close()
    return fig