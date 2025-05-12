import zipfile

with zipfile.ZipFile("peta_ikm_jambi_files.zip", 'r') as zip_ref:
    zip_ref.extractall(".")
