# Python utilities
import sys
import argparse
import json
import os
import shutil
import pandas as pd

# Astropy utilities
from astropy.time import Time

# DINOS utilities
import dino_tools as tools
import all_sky_map
import local_sky
import airmass
import finder_image
import object_stats

# read command line arguments
parser = argparse.ArgumentParser(description="Just an example",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--input", help="input path")
parser.add_argument("-o", "--output", help="output path")
parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")

args = vars(parser.parse_args())

# define templates
temp_night = """
\\newpage

\DIV[1]{{section}}*{{The Night}}\label{{Ueff}}
\\vspace{{-0.2cm}}\hrule
\\vspace{{1cm}}

\\begin{{minipage}}{{0.45\\textwidth}}

\\textbf{{Telescope Name}}: {0}

\\textbf{{Telescope Location}}: {2:.4f} {1:.4f}

\\textbf{{Telescope Elevation}}: {3}

\\textbf{{Sunset}}: {4}

\\textbf{{Sunrise}}: {5}

\\textbf{{Civil Twilights}}: {6} , {7}

\\textbf{{Nautical Twilights}}: {8} , {9}

\\textbf{{Astronomical Twilights}}: {10} , {11}


\end{{minipage}}
\hspace{{0.1\\textwidth}}
\\begin{{minipage}}{{0.45\\textwidth}}

\\textbf{{Observation Start}}: {12}

\\textbf{{Observation End}}: {13}

\\textbf{{Observation Blocks}}:

\\vspace{{0.2cm}}

\\begin{{tabular}}{{l|c|c}}%
    \\bfseries Block Name & \\bfseries Start Time & \\bfseries End Time
    \csvreader[head to column names]{{blocks.csv}}{{}}
    {{\\\\\hline\\name & \starttime & \endtime }}
\end{{tabular}}

\end{{minipage}}
"""

temp_finder = """
\\newpage

\DIV[1]{{section}}*{{Finder Chart {0}}}\label{{Ueff}}
%\\vspace{{0.2cm}}

\\begin{{minipage}}{{0.6\\textwidth}}
    \includegraphics[width=9cm]{{{1}/finder_{7}.jpg}}
\\vspace{{-2cm}}

\end{{minipage}}
\\begin{{minipage}}{{0.3\\textwidth}}

\\textbf{{Object RA}}: {2}

\\textbf{{Object DEC}}: {3}

\\textbf{{Object Type}}: {4}

\\textbf{{Spectral Type}}: {5}

\\textbf{{Apparent V magnitude}}: {6}

\end{{minipage}}
"""

#print(temp_finder)


def _read_input(path):
    # load the json
    with open(path) as f:
        data = json.load(f)
        f.close()
        
    night_data = data['Night']
    target_data = data['Targets']
    config_data = data['Config']
    
    return night_data, target_data, config_data


if __name__ == "__main__":
    """
    Dino time
    """
    print("""
  _____ _____ _   _  ____   _____        __ 
 |  __ \_   _| \ | |/ __ \ / ____|      /_ |
 | |  | || | |  \| | |  | | (___   __   _| |
 | |  | || | | . ` | |  | |\___ \  \ \ / / |
 | |__| || |_| |\  | |__| |____) |  \ V /| |
 |_____/_____|_| \_|\____/|_____/    \_/ |_|
                                            """)
    print("It's dino time\n")
    
    # read command line arguments
    if args['input'] == None:
        args['input'] = "./dinos_config.json"
        
    if args['output'] == None:
        args['output'] = "./output"
        
    if not os.path.exists(args['output']):
        os.mkdir(args['output'])
    
    if args['verbose']:
        print("----------------------------------")
        print("----------- Arguments ------------")
        print("----------------------------------")
        print(args)
        print()
    
    # read configuration file
    print("reading configuration...")
    night_data, target_data, config_data = _read_input(args['input'])
    
    # define observer
    print("defining observer...")
    dino_loc = tools.setup_location(night_data['telescope_name'],
                                    night_data['observer_lat'],
                                    night_data['observer_long'],
                                    night_data['observer_elevation'],
                                    night_data['observer_timezone'])
    print("setting up times...")
    try:
        bst = night_data['block_start_times']
    except:
        bst = None
    try:
        bet = night_data['block_end_times']
    except:
        bet = None        
    try:
        bc = night_data['block_colors']
    except:
        bc = None
    
    times = tools.setup_times(dino_loc,
                              night_data['obs_start'],
                              night_data['obs_end'],
                              block_start_times=bst,
                              block_end_times=bet,
                              block_colors=bc)
    
    if args['verbose']:
        print("----------------------------------")
        print("---------- times -----------")
        print("----------------------------------")
        print(times)
        print()
        
    # setup blocks.csv
    blocks_df = pd.DataFrame(columns=["name", "starttime", "endtime"])
    i = 1
    for this_block in times['blocks']:
        this_dict = {
            "name":"Block " + str(i),
            "starttime":this_block['times'][0].iso.split()[1][:8],
            "endtime":this_block['times'][1].iso.split()[1][:8]
        }
        this_df = pd.DataFrame(this_dict, index=[0])
        blocks_df = pd.concat([blocks_df, this_df], join="outer")
        i += 1
    blocks_df.to_csv("{0}/blocks.csv".format(args['output']))
    
    # define targets
    if args['verbose']:
        print("----------------------------------")
        print("---------- target_data -----------")
        print("----------------------------------")
        print(target_data)
        print()
        
    print("setting up targets...")
    targets = tools.setup_target_list(target_data, dino_loc)
    
    if args['verbose']:
        print("----------------------------------")
        print("------------ targets -------------")
        print("----------------------------------")
        print(targets)
        print()
        
    
    # create targets.csv, rise_and_set.csv
    df = pd.DataFrame(columns=["Object", "RA", "DEC", "oType", "spType",
                               "d", "V", "rise", "set", "lowest_a"])
    for target in targets:
        # get target properties
        try:
            data = object_stats.simbad_query(target['name'])
        except:
            try:
                data = {"oType":" ",
                        "spType":" ",
                        "RA":str(target['target'].ra),
                        "DEC":str(target['target'].dec),
                        "d":" ",
                        "V":" "}
            except:
                data = {"oType":"non-fixed",
                        "spType":" ",
                        "RA":"variable",
                        "DEC":"variable",
                        "d":" ",
                        "V":" "}
        
        data['Object'] = target['name']
        
        
        # get rise time
        try:
            data['rise'] = dino_loc.target_rise_time(night_data['obs_start'],
                                                     target['target'],
                                                     which="nearest").iso.split()[1][:8]
            #print(dino_loc.target_rise_time(night_data['obs_start'],
            #                                         target['target'],
            #                                         which="nearest").scale)
        except:
            data['rise'] = "NA"
        
        # get set time
        try:
            data['set'] = dino_loc.target_set_time(night_data['obs_start'],
                                                   target['target'],
                                                   which="nearest").iso.split()[1][:8]
        except:
            data['set'] = "NA"
        
        # get time of lowest airmass
        
        # append it to the dataframe
        this_df = pd.DataFrame(data, index=[0])
        df = pd.concat([df, this_df], join="outer")
        target.update(data)
        
    if args['verbose']:
        print("----------------------------------")
        print("------------ targets -------------")
        print("----------------------------------")
        print(targets)
        print()

    
    df.to_csv("{}/targets.csv".format(args['output']))

    # create all-sky map
    print("creating plots...")
    print("all sky map")
    all_sky_map.plot(targets, times=times, path=args['output'],
                     observer=dino_loc, **config_data['all_sky_map'])
    
    # create local-sky map
    print("local sky map")
    local_sky.plot(dino_loc, times, targets, path=args['output'],
                   **config_data['local_sky'])
    
    # create airmass plot
    print("airmass")
    airmass.plot(dino_loc, times, targets, path=args['output'],
                 **config_data['airmass'])
    
    # create finder images
    for target in targets:
        print("Finder image {0}".format(target['name']))
        finder_image.plot(target, path=args['output'],
                          **config_data['finder_images'])

    finder_charts = ""
    for target in targets:
        finder_charts += temp_finder.format(target['name'],
                                            args['output'],
                                            target['RA'], 
                                            target['DEC'],
                                            target['oType'],
                                            target['spType'],
                                            target['V'],
                                            target['name'].replace(" ", "").replace(".", "_"))
    
    # create the night page
    print("formatting document...")
    night_page = temp_night.format(
        night_data['telescope_name'],
        night_data['observer_lat'],
        night_data['observer_long'],
        night_data['observer_elevation'],
        times['sunset'].iso,
        times['sunrise'].iso,
        times['civ_twl'][0].iso.split()[1][:8],
        times['civ_twl'][1].iso.split()[1][:8],
        times['nau_twl'][0].iso.split()[1][:8],
        times['nau_twl'][1].iso.split()[1][:8],
        times['ast_twl'][0].iso.split()[1][:8],
        times['ast_twl'][1].iso.split()[1][:8],
        night_data['obs_start'],
        night_data['obs_end']
    )
    
    # edit latex template
    this_date = night_data['obs_start'].split()[0]
    
    # read the template
    with open('report_template.tex', 'r') as file:
        file_data = file.read()

        # Searching and replacing the text
        file_data = file_data.replace("DD-MM-YYYY", this_date)
        file_data = file_data.replace("TELESCOPE-NAME",
                                      night_data['telescope_name'])
        file_data = file_data.replace("%FINDERCHARTS", finder_charts)
        file_data = file_data.replace("%THENIGHT", night_page)
        file_data = file_data.replace("OUTPUTDIRECTORY", args['output'])
  
    # generate the name of the new tex file
    script_name = '{0}/dinos_{1}_{2}.tex'.format(args['output'],
                        this_date,
                        night_data['telescope_name'].replace(" ", "-"))
    # write changes to new tex file
    with open(script_name, 'w') as file:

        # Writing the replaced data in our
        # text file
        file.write(file_data)

    # run report script
    #os.system("pdflatex -jobname dinos_report -output-directory {0} --interaction=batchmode {1}".format(args['output'], script_name))
    os.system("pdflatex -jobname dinos_report -output-directory {0} --interaction=batchmode {1}".format(args['output'], script_name))
    
    print("Done!")