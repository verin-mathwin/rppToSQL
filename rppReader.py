import os
import datetime
import sqlite3
import xml.etree.ElementTree as e_t
import pandas as pd
import re
from packaging import version  # Handles version comparisons properly


def getModifier(root):
    """
    Extracts the modifier data from the XML root element.

    :param root: XML root element.
    :return: Modifier value from the 'data' attribute or None if not found.
    """
    modifier_element = root.find(".//modifier")  # Find the modifier tag
    if modifier_element is not None:
        return modifier_element.get("data")  # Return the 'data' attribute value
    return None  


def determinVer(modifier):
    """
    Determines the version category based on the modifier value.

    :param modifier: Modifier string extracted from XML.
    :return: "A" if modifier is None or below version 1.9.6, otherwise "B".
    """
    if modifier is None:
        return "A"
    match = re.search(r"\d+\.\d+\.\d+", modifier)
    if not match:
        return "A"
    modifier_version = version.parse(match.group())  # Convert to version object
    threshold_version = version.parse("1.9.6")  # Define threshold
    return "B" if modifier_version >= threshold_version else "A"


def makePandas(lasconfigList, rppDic, navDevDic, camDevDic, lasDevDic, manualRi, ver):
    """
    Takes the dictionaries gathered from the RPP scrape and turns them into pandas dataframes.
    Violently simple. Separate in case it needs to be tweaked.
    :param lasconfigList:         Lasconfig list scraped from RPP
    :param rppDic:                Records dic scraped from the RPP
    :param navDevDic:             Nav device information dic scraped from the RPP
    :param camDevDic:             Camera device information dic scraped from the RPP
    :param lasDevDic:             LiDAR device information dic scraped from the RPP
    :param manualRi:              Boolean flag indicating if swaths were assigned manually in RiWorld
    :return:                      Ungrouped collection of dataframes - one for each dictionary/list above.

    USAGE:
    lasconfigPandas, navDevPandas, recordPandas,
                camDevPandas, lasDevPandas = makePandas(lasconfigList, rppDic, navDevDic,
                                                           camDevDic, lasDevDic, manualRiWorldUsed)
    """
    print('Making dataframes for RPP info...')
    lasconfigPandas = pd.DataFrame(columns=['lasconfig_index', 'lasconfig'], data=lasconfigList).set_index(
        'lasconfig_index')
    recordPandas = pd.DataFrame.from_dict(rppDic, orient='index')
    if "B" in ver:
        print("record debug")
        recordPandas.info()
    if not manualRi:
        try:
            recordPandas.dropna(subset=['scan-script'], inplace=True)
        except KeyError:
            print('warning - no Scan Script info saved')
    navDevPandas = pd.DataFrame.from_dict(navDevDic, orient='index')
    camDevPandas = pd.DataFrame.from_dict(camDevDic, orient='index')
    lasDevPandas = pd.DataFrame.from_dict(lasDevDic, orient='index')
    return lasconfigPandas, navDevPandas, recordPandas, camDevPandas, lasDevPandas


def create_connection(outputDB):
    """
    Creates a connection to a SQLite database file

    :param outputDB:              Full path to database file
    :return:                      Connection object
    """
    dbFile = outputDB
    conn = None
    try:
        conn = sqlite3.connect(dbFile)
    except sqlite3.Error as e:
        logging.info(e)
    return conn


def write_outputDB(outputDB, lasdevPandas, camdevPandas, navdevPandas, recordPandas):
    """
    Writes the dataframes to the SQLite database file.
    :param outputDB:              Full path to output SQLite database file.
    :param lasdevPandas:          Dataframe of information about the LiDAR scanner
    :param camdevPandas:          Dataframe of information about the camera
    :param navdevPandas:          Dataframe of information about the IMU/nav system
    :param recordPandas:          Dataframe of information about the scanner records (swaths)
    """
    print('Writing output file...')
    conn = create_connection(outputDB)
    if conn is not None:
        with conn:
            lasdevPandas.astype(str).to_sql("las_device", conn, if_exists="replace", dtype="string", index=True)
            camdevPandas.to_sql("cam_device", conn, if_exists="replace", dtype="string", index=True)
            navdevPandas.to_sql("nav_device", conn, if_exists="replace", dtype="string", index=True)
            try:
                recordPandas.to_sql("record_info", conn, if_exists="replace", dtype="string", index=True)
            except sqlite3.InterfaceError as e:
                print(e)
                for i, c in enumerate(recordPandas.columns):
                    print(i, c)
                numInError = int(re.findall(r'\b\d+\b', str(e))[0])
                relevantCol = recordPandas.iloc[:, numInError]
                print(relevantCol)
                exit()
                

def timeIssueEditor(rppDic, negIssue, timeZoneEdit):
    """
    Occasionally there seems to be an issue with the system time being out by a factor of a time zone difference.
    I have also seen it occur in both a positive and negative direction.
    Regardless of the cause, this function seeks to be an available solution for that issue.

    :param rppDic:                Dictionary of records and record information extracted from rpp
    :param negIssue:              Boolean inducating if the time delta needs to be negative
    :param timeZoneEdit:          integer of minutes' absolute difference required
    :return updated RPP dic:

    USAGE:
    rppDic = time_issue_editor(rppDic, False, 30)
    """
    print('Applying time zone correction...')
    if negIssue:
        h = -1 * timeZoneEdit
    else:
        h = timeZoneEdit
    for key in rppDic.keys():
        wrongTimeStart = rppDic[key]['time-start']
        wrongStartAsDT = datetime.datetime.strptime(wrongTimeStart, '%Y-%m-%d %H:%M:%S.%f')
        correctStartAsDT = wrongStartAsDT + datetime.timedelta(hours=h)
        wrongTimeEnd = rppDic[key]['time-end']
        wrongTimeEndAsDT = datetime.datetime.strptime(wrongTimeEnd, '%Y-%m-%d %H:%M:%S.%f')
        correctTimeEndAsDT = wrongTimeEndAsDT + datetime.timedelta(hours=h)
        correctStart = correctStartAsDT.strftime('%Y-%m-%d %H:%M:%S.%f')
        correctEnd = correctTimeEndAsDT.strftime('%Y-%m-%d %H:%M:%S.%f')
        rppDic[key]['time-start'] = correctStart
        rppDic[key]['time-end'] = correctEnd
        return rppDic


def read194nav(project):
    """
    Extracts navigation, LiDAR, and camera device information from an RPP project of version 1.9.4 or below.

    :param project: XML element representing the project.
    :return: Extracted data dictionaries and lists.
    """
    navdevDic = {}
    lasdevDic = {}
    camdevDic = {}
    navSystem = [x for x in project.findall(".objects/object/[@kind='SYSTEM']/objects/object/[@kind='NAVDEVICES']")][0]
    nav_fields = [x for x in navSystem.findall(".objects/object/fields/field")]
    lasSystem = [x for x in project.findall(".objects/object/[@kind='SYSTEM']/objects/object/[@kind='LASDEVICES']")][0]
    lasSettings = [x for x in project.findall(".objects/object/[@kind='SYSTEM']/objects/object/[@kind='LASCONFIGS']")][0]
    camSystem = [x for x in project.findall(".objects/object/[@kind='SYSTEM']/objects/object/[@kind='CAMDEVICES']")][0]
    camSettings = [x for x in project.findall(".objects/object/[@kind='SYSTEM']/objects/object/[@kind='CAMCONFIGS']")][0] 
    for a in nav_fields:
        navdevDic[a.attrib['name']] = a.attrib['data']
    lasdev_fields = [x for x in lasSystem.findall(".objects/object/fields/field")]
    for a in lasdev_fields:
        lasdevDic[a.attrib['name']] = a.attrib['data']
    camdev_fields = [x for x in camSystem.findall(".objects/object/fields/field")]
    for a in camdev_fields:
        camdevDic[a.attrib['name']] = a.attrib['data']
    lasSettingList = [x for x in lasSettings.findall(".objects/object")]
    lasconfigList = [(
            lc.attrib['name'].replace(' m', 'm').replace(' kn', 'kn').replace(' kHz', 'kHz').replace(
                ' lps', 'lps').replace('(', '').replace(')', '').replace('PWR=', ''),
            str(lasSettingList.index(lc))) for lc in lasSettingList]
    return navSystem, nav_fields, lasSystem, lasSettings, camSystem, camSettings, navdevDic, lasdevDic, camdevDic, lasSettingList, lasconfigList


def read195nav():
    """
    Placeholder function for reading RISD data.
    Will be updated when time permits to handle the RISD.
    """
    pass



def organiseRpp(rppLink, gpsSA, gpsNSW, negIssue, segments):
    """
    Scrapes the RPP for information. This version can handle both pre- and post-RiWorld versions.

    :param rppLink:               Full file path to RPP file
    :param gpsSA:                 Boolean indicating presence of time zone issue in line with South Australian time
                                       zone offset, i.e. +30 or -30 min offset.
    :param gpsNSW:                Boolean indicating presence of time zone offset in line with New South Wales time
                                       zone offset, i.e. +60 or -60 min offset.
    :param negIssue:              Boolean indicating whether or not the offset needs to be subtracted rather than added.
    :returns rppDic, lasdevDic, camdevDic, navdevDic, lasconfigList, camSettings:

    USAGE:
    rppDic, lasdevDic, camdevDic, navdevDic, lasconfigList, camSettings = organiseRpp(full_path, False, True, False)
    """
    print('Reading RPP...')
    rppDic = {}
    lasdevDic = {}
    camdevDic = {}
    navdevDic = {}
    lasconfigList = []
    camSettings = []
    tree = e_t.parse(rppLink)
    root = tree.getroot()
    
    projects = [x for x in root.findall(".content/object/[@kind='project']")]
    mod = getModifier(root)
    classRPP = determinVer(mod)
    print(mod)
    print("Found RPP of type", classRPP)
    print("##")
    for project in projects:
        print(project.attrib['name'])
        records = [x for x in project.findall(".objects/object/[@kind='RECORDS']/objects/object/[@kind='record']")]


        if "A" in classRPP:
            navSystem, nav_fields, lasSystem, lasSettings, camSystem, camSettings, navdevDic, lasdevDic, camdevDic, lasSettingList, lasconfigList =  read194nav(project)
        elif "B" in classRPP:
            pass

        for i, elem in enumerate(records):
            try:
                recInfo = [x for x in elem.findall(".objects/object/[@kind='lasdata']")][0]
            except IndexError:
                print('Misfire detected, index ', i)
                recInfo = None
            if recInfo is not None:
                recordName = elem.attrib['name']
                try:
                    recordNum, line_no = recordName.split('_')
                except ValueError:
                    recordNum = recordName
                    line_no = None
                dataDic = {'project-name': project.attrib['name'], 'record': recordNum, 'line-number': line_no}
                print(', '.join(['%s: %s' % (a, dataDic[a]) for a in dataDic.keys() if 'project-name' not in a]))
                rxpInfo = [x for x in recInfo.findall(".objects/object/[@kind='rxp-file']")][0]
                try:
                    cDatat = [a for a in elem.findall("./objects/object/[@kind='camdata']")][0]
                except IndexError:
                    cDatat = []
                if len(cDatat) > 0:
                    cAttribs = [x.attrib for x in cDatat.findall('.fields/field')]
                    for a in cAttribs:
                        dataDic[a['name']] = a['data']
                else:
                    print('c datat issue on %s' % recordName)

                try:
                    lasconfig = [x for x in rxpInfo.findall(".links/link/[@kind='lasconfig']")][0].attrib['node']
                    lasconfigIndex = int(lasconfig.split('[')[-1].strip('[]'))
                    lasconfig = lasconfigList[lasconfigIndex][0]
                except IndexError:
                    lasconfig = None
                    lasconfigIndex = None
                swathName = rxpInfo.attrib['name']
                recAttribs = [x.attrib for x in rxpInfo.findall(".fields/field")]
                for atr in recAttribs:
                    dataDic[atr['name']] = atr['data']
                dataDic['scan-script'] = lasconfig
                dataDic['lasconfig-index'] = lasconfigIndex
                dataDic['time-start'] = dataDic['time-start'].replace('+', '.')
                try:
                    dataDic['time-end'] = dataDic['time-end'].replace('+', '.')
                except KeyError:  # can occur if system shut down abruptly. assume rest is this swath
                    if i == len(records) - 1:
                        dataDic['time-end'] = None  # will add thing to check for this later, once we know end time
                    elif segments:
                        dataDic['time-end'] = None 
                    else:
                        raise KeyError
                rppDic[swathName] = dataDic
                print('scraped %s...' % swathName)
    print('found %s records...' % len(rppDic.keys()))
    if gpsSA:
        rppDic = timeIssueEditor(rppDic, negIssue, 0.5)
    if gpsNSW:
        rppDic = timeIssueEditor(rppDic, negIssue, 1)

    return rppDic, lasdevDic, camdevDic, navdevDic, lasconfigList, camSettings, classRPP


def workflowHandler(rppLink, gpsSA, gpsNSW, negIssue, outputDB, manualRiWorldUsed, segments):
    """
    Workflow manager.

    :param rppLink:               Full file path to RPP file
    :param gpsSA:                 Boolean indicating presence of time zone issue in line with South Australian time
                                       zone offset, i.e. +30 or -30 min offset.
    :param gpsNSW:                Boolean indicating presence of time zone offset in line with New South Wales time
                                       zone offset, i.e. +60 or -60 min offset.
    :param negIssue:              Boolean indicating whether or not the offset needs to be subtracted rather than added.
    :param outputDB:              Full path to output SQLite database file.
    :param manualRiWorldUsed:     Boolean flag indicating if swaths were assigned manually in RiWorld
    """
    rppDic, lasDevDic, camDevDic, navDevDic, lasconfigList, camSettings, classRPP = organiseRpp(rppLink, gpsSA, gpsNSW, negIssue, segments)
    lasconfigPandas, navDevPandas, recordPandas, camDevPandas, lasDevPandas = makePandas(lasconfigList, rppDic, navDevDic,
                                                           camDevDic, lasDevDic, manualRiWorldUsed, classRPP)
    write_outputDB(outputDB, lasDevPandas, camDevPandas, navDevPandas, recordPandas)
    print('done')
    print('###################')
    recordPandas.info()
    print("on exit")
    return recordPandas
    
    
