import rppReader

rppLink = r"D:\TroubleShooting_20220218\220209_041805\220209_041805.rpp"
outFile = r"D:\TroubleShooting_20220218\220209_041805\220209_041805.db"

rppReader.workflowHandler(rppLink, False, False, False, outFile, False)
