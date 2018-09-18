# Converting all series in a DICOM folder to sitk images
#
# Copyright (C) 2018 Yves Pauchard
# License: BSD 3-clause (see LICENSE)

# imageseriesreader is not yet supporting reading metadata from DICOM
# see https://github.com/SimpleITK/SimpleITK/issues/331
# should be fixed in SimpleITK 1.1 (Jan 2018 release)

#TODO: add logging

import SimpleITK as sitk
import os
import argparse

dicom_tag_id_name = {
    '0008|0016': 'SOPClassUID',
    '0008|0022': 'AcquisitionDate',
    '0008|0031': 'AcquisitionTime',
    '0008|0060': 'Modality',
    '0008|0070': 'Manufacturer',
    '0008|0080': 'InstitutionName',
    '0008|0090': 'ReferringPhysicianName',
    '0008|1030': 'StudyDescription',
    '0008|103e': 'SeriesDescription',
    '0008|1070': 'OperatorsName',
    '0008|1090': 'ManufacturersModelName',
    '0010|0010': 'PatientName',
    '0010|0020': 'PatientID',
    '0010|0030': 'PatientBirthDate',
    '0010|0040': 'PatientSex',
    '0010|1010': 'PatientAge',
    '0010|1030': 'PatientWeight',
    '0018|0015': 'BodyPartExamined',
    '0018|0020': 'ScanningSequence',
    '0018|0021': 'SequenceVariant',
    '0018|0023': 'MRAcquisitionType',
    '0018|0024': 'SequenceName',
    '0018|0050': 'SliceThickness',
    '0018|0080': 'RepetitionTime',
    '0018|0081': 'EchoTime',
    '0018|0083': 'NumberOfAverages',
    '0018|0087': 'MagneticFieldStrength',
    '0018|0088': 'SpacingBetweenSlices',
    '0018|0089': 'NumberOfPhaseEncodingSteps',
    '0018|0091': 'EchoTrainLength',
    '0018|0095': 'PixelBandwidth',
    '0018|1030': 'ProtocolName',
    '0018|1100': 'ReconstructionDiameter',
    '0018|1250': 'ReceiveCoilName',
    '0018|1314': 'FlipAngle',
    '0020|0010': 'StudyID',
    '0020|0020': 'PatientOrientation',
    '0020|1041': 'SliceLocation',
    '0028|0010': 'Rows',
    '0028|0011': 'Columns',
    '0028|0030': 'PixelSpacing'
}

# Generate the reverse dictionary
# https://stackoverflow.com/questions/483666/python-reverse-invert-a-mapping
dicom_tag_name_id = {v: k for k, v in dicom_tag_id_name.items()}

# Dicom tags to print
tags_to_print = ['PatientID',
                 'StudyID',
                 'BodyPartExamined',
                 'SequenceName',
                 'SeriesDescription',
                 'SliceThickness',
                 'SpacingBetweenSlices',
                 'RepetitionTime',
                 'EchoTime']


# Argument parser
a_parser = argparse.ArgumentParser(
    description='Extracts each series from a DICOM folder and saves as SimpleITK image.',
    epilog='Example: python dicom_series_to_sitk.py path_to_dicoms path_to_store_output \nScans directory and saves every series to output path.')
a_parser.add_argument('dicom_path', help='Path to DICOM images')
a_parser.add_argument('output_dir', help='Path to output directory where SimpleITK images will be stored.')
a_parser.add_argument('--extension', default='.mha', help='Select SimpleITK image type by providing extension. Default is .mha')
# a_parser.add_argument("-v", "--verbose", help="increase output verbosity (more prints)", action="store_true")

# Parse arguments
args = a_parser.parse_args()

# copy arguments
dicom_path = args.dicom_path
output_dir = args.output_dir
image_extension = args.extension

# Logging
print("DICOM path {}".format(dicom_path))
print("Output path {}".format(output_dir))
print("image extension {}".format(image_extension))


# TODO: Should there be an option to just print DICOM info? Or do this in a separate script?

image_reader = sitk.ImageFileReader()

series_reader = sitk.ImageSeriesReader()

# get all series in dicom directory
seriesIDs = series_reader.GetGDCMSeriesIDs(dicom_path)

print("Found {} series".format(len(seriesIDs)))

for num, seriesID in enumerate(seriesIDs):
    # get all filenames in first series
    file_names = series_reader.GetGDCMSeriesFileNames(dicom_path, seriesID)

    # load the first 2D image to get meta data
    image_reader.SetFileName(file_names[0])
    img2D = image_reader.Execute()

    #print('\n--------------------')
    file_name = "{}_{}_{}_TR{}_TE{}".format(img2D.GetMetaData(dicom_tag_name_id['PatientID']),
                                         num,
                                         img2D.GetMetaData(dicom_tag_name_id['SequenceName']),
                                   img2D.GetMetaData(dicom_tag_name_id['RepetitionTime']),
                                   img2D.GetMetaData(dicom_tag_name_id['EchoTime']))
    file_name = file_name.replace(" ", "")

    # TODO: clean this code
    #print(file_name)

    #print("Series {}".format(num))

    # loop through metadata keys
    #all_keys = img2D.GetMetaDataKeys()
    #for tag in tags_to_print:
    #    key = dicom_tag_name_id[tag]
    #    if key in all_keys:
    #        print("{} {}: {}".format(key, dicom_tag_id_name[key], img2D.GetMetaData(key)))


    # Read the 3D image
    series_reader.SetFileNames(file_names)

    img = series_reader.Execute()

    #
    if not os.path.exists(output_dir):
        print("Creating output directory {}".format(output_dir))
        os.makedirs(output_dir)
    # Write image
    print("Writing {}".format(os.path.join(output_dir, file_name+image_extension)))
    sitk.WriteImage(img, os.path.join(output_dir, file_name+image_extension))
