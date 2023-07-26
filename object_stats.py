import numpy as np
import pandas as pd
from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord
import astropy.units as u


def simbad_query(object_name):
    """
    
    """
    sbd = Simbad()
    sbd.add_votable_fields('otype', 'sptype', 'distance', 'parallax',
                           'fluxdata(V)', 'ra(d)', 'dec(d)')
    result_table = sbd.query_object(object_name)
    
    coord = SkyCoord(result_table['RA'][0] +
                     " " + result_table['DEC'][0], unit=(u.hourangle, u.deg))
    
    data = {"oType":result_table['OTYPE'][0],
            "spType":result_table['SP_TYPE'][0],
            #"SkyCoord":coord,
            "RA":str(coord.ra),
            "DEC":str(coord.dec),
            "d":" ",
            "V":" "}
    
    if result_table['Distance_distance'][0]:
        d = result_table['Distance_distance'][0]
        dd = result_table['Distance_perr'][0]
        data['d'] = "{0:.3f}".format(d) + "$\\pm$" + "{0:0.3f}".format(dd)
    elif result_table['PLX_VALUE'][0]:
        p = result_table['PLX_VALUE'][0]
        dp = result_table['PLX_ERROR'][0]
        d = 1/p
        dd = np.sqrt((dp/p)**2)*d
        data['d'] = "{0:.3f}".format(d) + "$\\pm$" + "{0:0.3f}".format(dd) #±
    else:
        data['d'] = ""
        
    if result_table['FLUX_V'][0]:
        V = result_table['FLUX_V'][0]
        if not result_table['FLUX_ERROR_V'][0]:
            dV = 0
        else:
            dV = result_table['FLUX_ERROR_V'][0]
        data['V'] = "{0:.3f}".format(V) + "$\\pm$" + "{0:0.3f}".format(dV)
        
    return data
    
def ztf_query(object_name):
    """
    
    """
    