# rppToSQL
Simple tool for converting a RIEGL .rpp file to a SQLite DB file for easy external reading.

To use, call like this:
rppReader.workflowHandler(rppLink, gpsSA, gpsNSW, negIssue, outputDB, manualRiWorldUsed)

where:
rppLink = Full file path to RPP file
gpsSA
- Boolean indicating presence of time zone issue in line with South Australian time zone offset, i.e. +30 or -30 min offset.
gpsNSW
- Boolean indicating presence of time zone offset in line with New South Wales time zone offset, i.e. +60 or -60 min offset.
negIssue
- Boolean indicating whether or not the offset needs to be subtracted rather than added.
outputDB
- Full path to output SQLite database file.
manualRiWorldUsed
- Boolean flag indicating if swaths were assigned manually in RiWorld

I have not tested this particular version just yet, but the original script from which I have separated/tidied it is designed to run on 3.7. If you get an issue when building the dataframes, try winding back your pandas version.

Whilst technically the output is fully visible in RiProcess etc, I find this neat for:
- quick lookup of basic info
- metadata compilation
