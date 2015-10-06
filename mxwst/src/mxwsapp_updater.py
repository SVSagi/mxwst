'''
Created on Aug 30, 2015

@author: sarraju
'''

import urllib2, decimal
import ConfigParser
import applogger as al

aplgr = al.AppLogger("MXWST_Settings")

class AppUpdate():
    def __init__(self, parent, cur_app_version, cur_app_build, cur_app_isbeta):
        self.parent = parent
        self.has_check_error = False
        self.update_check_url = 'http://sourceforge.net/projects/pymxwst/files/update_check.inf/download'
        self.config = ConfigParser.ConfigParser()
        self.newData = None

        self.cur_app_version = cur_app_version
        self.cur_app_build = cur_app_build
        self.cur_app_isbeta = cur_app_isbeta
        
        self.notify_msg = ""
        
        self.get_update_fail = False
        
    
    def setUpdateData(self):    
        try:
            req = urllib2.Request(self.update_check_url)
            response = urllib2.urlopen(req, timeout=4)
            self.newData = response.read()
        except Exception as e:
            self.get_update_fail = True
            aplgr.log('Error fetching update '+str(e))
        
        if self.parent.close_after_update:
            self.parent.Destroy()


    def getUpdateValue(self, section, option):
        if self.newData == None or self.get_update_fail == True:
            return None
        
        import StringIO
        buf = StringIO.StringIO(self.newData)
        self.config.readfp(buf)
        
        return self.config.get(section, option)
        
    def notifyInApp(self):
        self.setUpdateData()
        
        if self.newData == None or self.get_update_fail == True:
            return
               
        update_string = ""
        update_changes = ""
        
        update_final_ver = self.getUpdateValue("updates","latest_final_main")
        update_final_build = self.getUpdateValue("updates","latest_final_build")
        update_beta_ver = self.getUpdateValue("updates","latest_beta_main")
        update_beta_build = self.getUpdateValue("updates","latest_beta_build")

        if bool(self.getUpdateValue("updates","update")):
            if bool(self.cur_app_isbeta):
                if decimal.Decimal(update_beta_ver) > decimal.Decimal(self.cur_app_version):
                    update_string = update_beta_ver +"b"+ update_beta_build
                    update_changes = self.getUpdateValue("updates","beta_changes")
                
                if decimal.Decimal(update_beta_build) > decimal.Decimal(self.cur_app_build):
                    update_string = update_beta_ver +"b"+ update_beta_build
                    update_changes = self.getUpdateValue("updates","beta_changes")
            else:
                if decimal.Decimal(update_final_ver) > decimal.Decimal(self.cur_app_version):
                    update_string = update_final_ver + "b" +update_final_build
                    update_changes = self.getUpdateValue("updates","final_changes")
                
                if decimal.Decimal(update_final_build) > decimal.Decimal(self.cur_app_build):
                    update_string = update_final_ver + "b" +update_final_build
                    update_changes = self.getUpdateValue("updates","final_changes")

        if bool(self.getUpdateValue("updates","notification")):
            self.notify_msg = self.getUpdateValue("updates","notification_msg")

        if self.parent.close_after_update:
            self.parent.Destroy()

        if update_string != "":
            from wx import Menu, MenuItem, EVT_MENU
            
            self.parent.update_ver = update_string + ("beta" if self.cur_app_isbeta else "")
            self.parent.update_changes = ("\n".join(update_changes.split('\\n')))

            updateMenu = Menu()
            updateMenu.AppendItem(MenuItem(updateMenu, 300, 'Version '+update_string))
            self.parent.Bind(EVT_MENU, self.parent.showUpdate, id=300)  
            self.parent.menuBar.Append(updateMenu, "Update Available ")
            
        if self.parent.close_after_update:
            self.parent.Destroy()

#up = AppUpdate(1, 1, True)
#print up.notifyInApp()
            
        