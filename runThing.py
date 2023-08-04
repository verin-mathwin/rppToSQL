import rppReader

rppLink = r"D:\Upload_Temp\20230523_USQ\230522_235612\230522_235612.rpp"
outFile = r"D:\Upload_Temp\20230523_USQ\230522_235612\230522_235612.db"

rppReader.workflowHandler(rppLink, False, False, False, outFile, False)
