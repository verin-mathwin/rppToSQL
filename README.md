# rppToSQL
Simple tool for converting a RIEGL .rpp file to a SQLite DB file for easy external reading.

To use, call like this:
rppReader.workflowHandler(rppLink, gpsSA, gpsNSW, negIssue, outputDB, manualRiWorldUsed) where:

rppLink: Full file path to RPP file

gpsSA: Boolean indicating presence of time zone issue in line with South Australian time zone offset, i.e. +30 or -30 min offset.

gpsNSW: Boolean indicating presence of time zone offset in line with New South Wales time zone offset, i.e. +60 or -60 min offset.

negIssue: Boolean indicating whether or not the offset needs to be subtracted rather than added.

outputDB: Full path to output SQLite database file.

manualRiWorldUsed: Boolean flag indicating if swaths were assigned manually in RiWorld


I have not tested this particular version just yet, but the original script from which I have separated/tidied it is designed to run on 3.7. If you get an issue when building the dataframes, try winding back your pandas version.

Whilst technically the output is fully visible in RiProcess etc, I find this neat for:
- quick lookup of basic info
- metadata compilation

EDIT late 2024: Now exports record Pandas innto shapefile and CSV.
EDIT Feb 2025: The newer units making use of the RiSD (Riegl System Description) have a different structure in their RPPs as a result; the same is true for RPP from _any_ unit touched by RiPROCESS 1.9.6+. I've added some _very_ crude adjustments for the latter (RiPROCESS 1.9.6+ detected) that will allow this tool to run, but **this tool is now waiting on the following further changes**:
- correcting the detection of RiPROCESS version to a more explicit detection of the RPP format version (d'oh!) - right now it may not properly work with 08_RECEIVED RPP off a RiLOC unit...
- adding a function/toolset to intgrate the RiSD info into the .db file; right now those tables are left blank for RiSD-era RPP
- re-connecting the scanscripts properly (this connection has been lost for RiSD units)
More generally, I also noticed the scanscript parser is still set up for a certain client and needs to be generalised (or rather, made smarter/less vulnerable.)
