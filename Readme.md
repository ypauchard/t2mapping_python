# t2mapping_scripts
## Installation
python

1. Anaconda
2. Install SimpleITK

T2mapping

1. Get t2mapping from github
2. adjust location of t2mapping executable in run_t2mapping.py

MITK-GEM

Get from simtk

## Running the pipeline
1. Create a folder for the subject
2. Create a folder dicom and copy images from PACS into there
3. Create a folder config and copy all .ini files from here
4. Open terminal, navigate subject folder
5. Run metaimage extraction
```python
python /Users/pauc/Documents/Research/code/t2mapping_scripts/dicom_series_to_sitk.py dicom/IMAGES raw/
```
6. Open MITK-GEM, load image with lowest TE from raw folder, draw a rough mask and save in sub-folder mask
7. Prepare image_list.csv with all image names, and TE values, save in config folder
8. In MITK-GEM, measure mean background intensity in 25mm circle, record in image_list.csv
9. Edit register.ini
10. Run registration
```python
python /Users/pauc/Documents/Research/code/t2mapping_scripts/register_images.py config/register.ini
```
11. Edit normalize.ini
12. Run normalization
```python
python /Users/pauc/Documents/Research/code/t2mapping_scripts/normalize_images.py config/normalize.ini
```
13. Edit t2map.ini
14. Run t2mapping
```python
python /Users/pauc/Documents/Research/code/t2mapping_scripts/run_t2mapping.py config/t2map.ini
```
15. In MITK-GEM, create a mask of the cartilage for T2 mapping analysis, save to mask folder
16. In MITK-GEM, measure mean T2 value in cartilage mask, recurd in results csv in results sub-folder
17. In MITK-GEM, mask T2 map image with cartilage mask and save to mask folder
18. Use Paraview to visualize masked t2 map on top of gray scale image.
