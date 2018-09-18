# Will call the ITK t2mapping executable
#
# Copyright (C) 2018 Yves Pauchard
# License: BSD 3-clause (see LICENSE)

import os
import subprocess
import logging
import configparser
import argparse
import csv

# path to t2mapping executable
exec_path= "/Users/pauc/Documents/Research/code/t2mapping/build/t2mapping"

# Create and configure logger
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s" # see https://docs.python.org/2/library/logging.html#logrecord-attributes
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logger = logging.getLogger()

def is_ini_ok(parser):
    """Checks if ini file has the necessary contents.

        [t2map]
        experiments_to_run = experiment1, experiment2

        [experiment1]
        input_dir = norm/
        image_list_csv = config/image_list.csv
        # which images from csv list to use for mapping, 0-based index
        images_to_use = 0, 2
        output_dir = t2maps/
        output_basename = MOJO_0054_3_SE_TR2100.0_1010

        # --- optional
        # default is _reg_norm
        # input_filename_ending = _reg_norm

        # 0 LIN, 1 NONLIN (default), 2 NONLIN w. constant
        # method = 1

        # default 0.0
        # threshold = 30.5


    """
    expected_sections = [ 't2map' ]
    expected_options = ['experiments_to_run']
    expected_experiment_options = [ 'input_dir', 'image_list_csv', 'images_to_use', 'output_dir' , 'output_basename']
    is_ok = True
    for section in expected_sections:
        if not parser.has_section(section) :
            print('Config section {} missing, please add.'.format(section))
            is_ok = False
        else:
            for candidate in expected_options:
                if not parser.has_option(section, candidate):
                    print( 'Option {}.{} missing, please add.'.format(section, candidate ))
                    is_ok = False
    # if main section is OK, check experiment sections
    if is_ok:
        experiments = parser.get('t2map','experiments_to_run').replace(" ","").split(',')
        for experiment in experiments:
            if not parser.has_section(experiment) :
                print('Config section {} missing, please add.'.format(experiment))
                is_ok = False
            else:
                for candidate in expected_experiment_options:
                    if not parser.has_option(experiment, candidate):
                        print( 'Option {}.{} missing, please add.'.format(experiment, candidate ))
                        is_ok = False
    return is_ok

def get_image_value_list(csv_file_name):
    """
        Expects a csv file with header/structure:
        filename, TE, mean_background

        skips the first (header) line

        returns a list of tuples with (filename, TE)
    """
    image_value_list = []

    with open(csv_file_name) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        # skip the header (first) line
        next(readCSV)

        for row in readCSV:
            image_value_list.append((row[0], row[1].strip()))
    return image_value_list

# Argument parser
a_parser = argparse.ArgumentParser(
    description='Calls t2mapping executable to perform t2mapping with given list of images.',
    epilog='Example: python normalize_images.py path_to_ini_file \n Configuration is in the ini file.\n ')
a_parser.add_argument('path_to_ini_file', help='Path to configuration (ini) file')
# a_parser.add_argument("-v", "--verbose", help="increase output verbosity (more prints)", action="store_true")

# Parse arguments
args = a_parser.parse_args()


config = configparser.ConfigParser()
config.read(args.path_to_ini_file)

# Check that all parameters needed are in configuration
if not is_ini_ok(config):
    exit(0)

# Get all experiments remove whitespces and split into list
experiments = config.get('t2map','experiments_to_run').replace(" ","").split(',')

logger.info("Experiemnts {} defined in {}".format(experiments, args.path_to_ini_file))

for experiment in experiments:

    # get parameters
    input_dir = config.get(experiment, 'input_dir')
    image_and_values = get_image_value_list(config.get(experiment, 'image_list_csv'))
    output_dir = config.get(experiment, 'output_dir')
    # this is a comma separated string, so we have to split and convert to int
    images_to_use = list(map(int, config.get(experiment, 'images_to_use').split(',')))
    output_basename = config.get(experiment, 'output_basename')
    # get optional parameters
    if config.has_option(experiment,'input_filename_ending'):
        filename_ending = config.get(experiment,'input_filename_ending')
    else:
        filename_ending = '_reg_norm'
    if config.has_option(experiment, 'method'):
        method = config.get(experiment, 'method')
    else:
        method = '1'
    if config.has_option(experiment, 'threshold'):
        threshold = config.get(experiment, 'threshold')
    else:
        threshold = '0.0'

    logger.info("Parameters for {} found in {}".format(experiment, args.path_to_ini_file))
    logger.info(input_dir)
    logger.info(image_and_values)
    logger.info(filename_ending)
    logger.info(output_dir)
    logger.info(images_to_use)
    logger.info(output_basename)
    logger.info(method)
    logger.info(threshold)

    # T2mapping needs full path for output
    full_output_basename = os.path.join(output_dir, output_basename)

    # creating subprocess call list
    call_list = [exec_path,
                full_output_basename,
                method,
                threshold]
    for idx in images_to_use:
        image, te = image_and_values[idx]
        split_filename = os.path.splitext(image)
        image =  split_filename[0] + filename_ending + split_filename[1]
        call_list.append(os.path.join(input_dir, image))
        call_list.append(te)

    #check if output_dir exists, create if not.
    if not os.path.exists(output_dir):
        logger.info("Creating output directory {}".format(output_dir))
        os.makedirs(output_dir)

    logger.info("starting process with: {}".format(call_list))

    # call t2mapping executable
    subprocess.check_call(call_list)
