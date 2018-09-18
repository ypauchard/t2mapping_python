# Pre-processing image(s) by normalization to noise level.
# Intended for subsequent T2 mapping
#
# Copyright (C) 2018 Yves Pauchard
# License: BSD 3-clause (see LICENSE)

import SimpleITK as sitk
import os
import logging
import configparser
import argparse
import csv



# Create and configure logger
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s" # see https://docs.python.org/2/library/logging.html#logrecord-attributes
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logger = logging.getLogger()

def is_ini_ok(parser):
    """Checks if ini file has the necessary contents.

        [normalize]
        input_dir = register/
        image_list_csv = config/image_list.csv
        output_dir = norm/

        # optional, default is _reg
        # input_filename_ending = _reg

        # optional, default is _norm
        # output_filename_ending = _norm


    """
    expected_sections = [ 'normalize' ]
    expected_options = [ 'input_dir', 'image_list_csv', 'output_dir' ]
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
    return is_ok

def get_image_value_list(csv_file_name):
    """
        Expects a csv file with header/structure:
        filename, TE, mean_background

        skips the first (header) line

        returns a list of tuples with (filename, mean_background)
    """
    image_value_list = []

    with open(csv_file_name) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        # skip the header (first) line
        next(readCSV)

        for row in readCSV:
            image_value_list.append((row[0], row[2]))
    return image_value_list

# Argument parser
a_parser = argparse.ArgumentParser(
    description='Normalizes a list of images to a reference value using SimpleITK.',
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

input_dir = config.get('normalize', 'input_dir')
image_and_values = get_image_value_list(config.get('normalize', 'image_list_csv'))
output_dir = config.get('normalize', 'output_dir')

# optional config parameter
if config.has_option('normalize', 'input_filename_ending'):
    filename_ending = config.get('normalize', 'input_filename_ending')
else:
    filename_ending = '_reg'
if config.has_option('normalize','output_filename_ending'):
    output_filename_ending = config.get('normalize','output_filename_ending')
else:
    output_filename_ending = '_norm'

logger.info("Parameters from {}".format(args.path_to_ini_file))
logger.info(input_dir)
logger.info(image_and_values)
logger.info(filename_ending)
logger.info(output_dir)
logger.info(output_filename_ending)

#check if output_dir exists, create if not.
if not os.path.exists(output_dir):
    logger.info("Creating output directory {}".format(output_dir))
    os.makedirs(output_dir)

for image_value in image_and_values:

    #unpack tuple
    image_name, value = image_value

    # Add filename ending
    split_filename = os.path.splitext(image_name)
    image_name =  split_filename[0] + filename_ending + split_filename[1]

    # Read moving image
    logger.info("Reading image {}".format(image_name))
    #moving = sitk.ReadImage(os.path.join(input_path, moving_image_name))
    img = sitk.ReadImage(os.path.join(input_dir, image_name))
    img = sitk.Cast(img, sitk.sitkFloat32)  # we will do division on floats

    # normalize
    logger.info("Normalizing image with {}".format(value))
    img /= value

    # Create normalized image name
    filename = os.path.basename(image_name)
    split_filename = os.path.splitext(filename)  # gets filename and extension
    ouput_file_name = split_filename[0] + output_filename_ending + split_filename[1]

    # Save registered image
    logger.info("Writing normalized image {}".format(ouput_file_name))
    sitk.WriteImage(img, os.path.join(output_dir, ouput_file_name))
