# t2mapping_scripts
## Installation
python

1. Anaconda http://anaconda.com/downloads get Python 3.6 installer, install.
2. Install SimpleITK
```
conda create -n sitkpy -c simpleitk python=3 numpy pandas scikit-learn matplotlib seaborn ipython-notebook simpleitk
```

T2mapping

1. Get t2mapping from github: https://github.com/ypauchard/t2mapping
2. Compile executable
3. Copy t2mapping executable to bin/ or adjust location in run_t2mapping.py

MITK-GEM

Download from https://simtk.org/projects/mitk-gem

## Running the pipeline
1. Create a folder for the subject
2. Create a folder dicom and copy images from PACS into there
3. Create a folder config and copy all .ini files from here
4. Open terminal, navigate subject folder
5. Activate conda environment
```
source activate sitkpy
```
6. Run metaimage extraction
```python
python <path>/t2mapping_python/dicom_series_to_sitk.py dicom/IMAGES raw/
```
7. Open MITK-GEM, load image with lowest TE from raw folder, draw a rough mask and save in sub-folder mask
8. Prepare image_list.csv with all image names, and TE values, save in config folder
9. In MITK-GEM, measure mean background intensity in 25mm circle, record in image_list.csv
10. Edit register.ini
11. Run registration
```python
python <path>/t2mapping_python/register_images.py config/register.ini
```
12. Edit normalize.ini
13. Run normalization
```python
python <path>/t2mapping_python/normalize_images.py config/normalize.ini
```
14. Edit t2map.ini
15. Run t2mapping
```python
python <path>/t2mapping_python/run_t2mapping.py config/t2map.ini
```
16. In MITK-GEM, create a mask of the cartilage for T2 mapping analysis, save to mask folder
17. In MITK-GEM, measure mean T2 value in cartilage mask, record in results csv in results sub-folder
18. In MITK-GEM, mask T2 map image with cartilage mask and save to mask folder
19. Use Paraview to visualize masked t2 map on top of gray scale image.

## Default directory structure
participant
  |--config
  |--dicom
  |--mask
  |--norm
  |--raw
  |--register
  |--t2maps
