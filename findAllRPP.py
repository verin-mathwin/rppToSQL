import os

def finder(rootFolder):
    """
    Searches for all .rpp files within the specified directory and its subdirectories.

    :param rootFolder: Path to the root directory to search.
    :return: List of file paths to all found .rpp files.
    """
    rppFiles = []
    for dirpath, _, filenames in os.walk(rootFolder):
        for file in filenames:
            if file.endswith(".rpp"):
                rppFiles.append(os.path.join(dirpath, file))
    return rppFiles
    

