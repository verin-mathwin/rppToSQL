import rppReader

rppLink = r"D:\Upload_Temp\joe_test_iiq\20220530_UC\VUX240_BORESIGHT.rpp"
outFile = r"D:\Upload_Temp\joe_test_iiq\20220530_UC\VUX240_BORESIGHT.db"

rppReader.workflowHandler(rppLink, False, False, False, outFile, False)
