# Register multiple images to the same reference image
#
# Copyright (C) 2018 Yves Pauchard
# License: BSD 3-clause (see LICENSE)

import SimpleITK as sitk
import os
import logging
import configparser
import argparse
import csv

#TODO: clean up how we know what are expected ini sections and options.
# Now it is defined in multiple locations.

# Create and configure logger
LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s" # see https://docs.python.org/2/library/logging.html#logrecord-attributes
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)
logger = logging.getLogger()

def is_ini_ok(parser):
    """Checks if ini file has the necessary contents.

        [register]
        reference_image = test.mha
        reference_mask = test_mask.mha
        input_dir = raw/
        images_to_register = register_images.csv
        output_dir = out/


        # optional, default is _reg
        # output_filename_ending = _reg


    """
    expected_sections = [ 'register' ]
    expected_options = [ 'reference_image', 'reference_mask', 'input_dir', 'images_to_register', 'output_dir' ]
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

def get_image_list(csv_file_name):
    """
        Expects a csv file with header/structure:
        filename, TE, mean_background

        skips the first (header) line
    """
    file_list = []

    with open(csv_file_name) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        # skip the header (first) line
        next(readCSV)

        for row in readCSV:
            file_list.append(row[0])
    return file_list

def print_values(registration_method):
    """Callback invoked when the IterationEvent happens, print values.

    :param registration_method:
    :return:
    """
    logger.debug("{}: metric = {}".format(registration_method.GetOptimizerIteration(),registration_method.GetMetricValue()))


def register_two_images(fixed_image, moving_image, fixed_mask_image=None, rigid=True):
    """Register two 3D images with rigid transform

    :param fixed_image: fixed image
    :param moving_image: moving image
    :param fixed_mask_image: (optional) mask for fixed image
    :param rigid: (optional, default is True) Set true if 3D Euler transform needed
    :return: transformed_moving_image, final_transform
    """
    R = sitk.ImageRegistrationMethod()

    #TODO: It is still a bit of a mystery which metric and optimizer we should choose.
    # *** Metric
    # R.SetMetricAsMeanSquares()

    # R.SetMetricAsCorrelation()

    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=64)
    R.SetMetricSamplingStrategy(R.RANDOM)
    R.SetMetricSamplingPercentage(0.4) # 40%

    # R.SetMetricAsJointHistogramMutualInformation()

    # *** Use mask if present
    if fixed_mask_image:
        R.SetMetricFixedMask(fixed_mask_image)

    # *** Optimizer
    #R.SetOptimizerAsGradientDescentLineSearch(learningRate=1.0,
    #                                          numberOfIterations = 200,
    #                                          convergenceMinimumValue = 1e-5,
    #                                          convergenceWindowSize = 5)

    #R.SetOptimizerAsRegularStepGradientDescent(learningRate=2.0,
    #                                           minStep = 1e-4,
    #                                           numberOfIterations = 500,
    #                                           gradientMagnitudeTolerance = 1e-8 )

    R.SetOptimizerAsGradientDescent(learningRate=10.0, numberOfIterations=100,
                                    convergenceMinimumValue=1e-6, convergenceWindowSize=10)

    # *** Transform
    if rigid: # use 3D Euler transform (default)
        #initial_transform = sitk.CenteredTransformInitializer(image1,
        #                                                      image2,
        #                                                   sitk.Euler3DTransform(),
        #                                               sitk.CenteredTransformInitializerFilter.GEOMETRY)
        #R.SetInitialTransform(initial_transform)

        # Motion should be small, so we will not apply any transform initializer
        R.SetInitialTransform(sitk.Euler3DTransform())
        R.SetOptimizerScalesFromPhysicalShift()
    else: # use 3D translation transform
        R.SetInitialTransform(sitk.TranslationTransform(fixed_image.GetDimension()))

    # *** Interpolator
    R.SetInterpolator(sitk.sitkLinear)

    # *** Observer
    R.AddCommand(sitk.sitkIterationEvent, lambda: print_values(R))


    final_transform = R.Execute(fixed_image, moving_image)

    logger.info('Optimizer\'s stopping condition, {0}'.format(R.GetOptimizerStopConditionDescription()))
    logger.info('Final metric value: {0}'.format(R.GetMetricValue()))

    #TODO: Expose interpolation method.
    moving_resampled = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())
    return moving_resampled, final_transform


# Argument parser
a_parser = argparse.ArgumentParser(
    description='Registers a series of images to a reference image using rigid registration and SimpleITK.',
    epilog='Example: python register_images.py path_to_ini_file \n Configuration is in the ini file.\n ')
a_parser.add_argument('path_to_ini_file', help='Path to configuration (ini) file')
# a_parser.add_argument("-v", "--verbose", help="increase output verbosity (more prints)", action="store_true")

# Parse arguments
args = a_parser.parse_args()


config = configparser.ConfigParser()
config.read(args.path_to_ini_file)

# Check that all parameters needed are in configuration
if not is_ini_ok(config):
    exit(0)

# Get parameters from config reader
fixed_image_name = config.get('register','reference_image')
fixed_mask_name = config.get('register','reference_mask')

moving_image_names = get_image_list(config.get('register', 'images_to_register'))
input_dir = config.get('register', 'input_dir')
output_dir = config.get('register', 'output_dir')

# optional config parameter
if config.has_option('register','output_filename_ending'):
    output_filename_ending = config.get('register','output_filename_ending')
else:
    output_filename_ending = '_reg'

logger.info("Parameters from {}".format(args.path_to_ini_file))
logger.info(fixed_image_name)
logger.info(fixed_mask_name)
logger.info(input_dir)
logger.info(moving_image_names)
logger.info(output_dir)
logger.info(output_filename_ending)

# Read fixed image
logger.info("Reading fixed image {}".format(fixed_image_name))
fixed = sitk.ReadImage(fixed_image_name)
fixed = sitk.Cast(fixed,sitk.sitkFloat32) # image registration needs float

logger.info("Reading fixed mask {}".format(fixed_mask_name))
fixed_mask = sitk.ReadImage(fixed_mask_name)

#check if output_dir exists, create if not.
if not os.path.exists(output_dir):
    logger.info("Creating output directory {}".format(output_dir))
    os.makedirs(output_dir)

# For all moving images do registration
for moving_image_name in moving_image_names:
    # Read moving image
    logger.info("Reading moving image {}".format(moving_image_name))
    moving = sitk.ReadImage(os.path.join(input_dir, moving_image_name))
    moving = sitk.Cast(moving, sitk.sitkFloat32)  # image registration needs float
    # register images
    logger.info("Register images")
    moving_resampled, final_transform = register_two_images(fixed, moving, fixed_mask_image=fixed_mask)

    # Create registered image name
    filename = os.path.basename(moving_image_name)
    split_filename = os.path.splitext(filename)  # gets filename and extension
    registered_file_name = split_filename[0] + output_filename_ending + split_filename[1]

    # Save registered image
    logger.info("Writing registered image {}".format(registered_file_name))
    sitk.WriteImage(moving_resampled, os.path.join(output_dir, registered_file_name))
