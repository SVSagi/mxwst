'''
Created on Aug 28, 2015

@author: sarraju
'''
import wx
class AppLogger():
    def __init__(self, appver = ""):
        self.logFile = appver+".log"
        self.appinfo = appver

    def log(self, msg):
        logf = None
        try:
            import time
            logf = open(self.logFile, 'a')
            logf.write(time.strftime("[%Y-%m-%d %H:%M:%S")+"]:\n "+msg+"\n----------End of error log-----------\n\n\n")
            logf.close()
        except Exception as e:
            logErDlg = wx.MessageDialog(None, str(e), self.appinfo+' - Error Logging.', wx.OK | wx.ICON_ERROR)
            logErDlg.ShowModal()
            if logf != None:
                logf.close()