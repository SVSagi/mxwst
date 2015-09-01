'''
Created on Aug 22, 2015

@author: sarraju
'''
import wx,os,decimal
import ConfigParser
import applogger as al

aplgr = al.AppLogger("MXWST_Settings")

class Settings():
    def __init__(self, parent):
        self.props = {'app_height':'', 'app_width':'', 'app_pos_point':'', 'tabs_at_top':'','show_password':'', 'load_last_session_files':'', 'show_line_numbers':'', 'request_timeout':'', 'username':'', 'password':'', 'content-type':'', 'soapaction':'', 'soap_env_start':'', 'soap_env_end':'', 'format_response_xml':'', 'format_tab_spaces':'', 'check_for_update_onstart':'1', 'check_for_update_onstart':'' }
        self.last_props = {'app_height':'', 'app_width':'', 'app_position_x':'', 'app_position_y':'', 'split_position':'', 'last_opened_files':'', 'mea_host_url':'', 'mea_service':'','use_authentication':''}
        self.parent = parent
    def loadSettings(self, settings_file = "mxwst-settings.cfg"):
        if(not os.path.isfile(settings_file)):
            aplgr.log('Settings file does not exist: '+settings_file)
            self.loadDefaultSettings() 
            return

        config = ConfigParser.ConfigParser()
        config.read(settings_file)
        
        for key in self.props:
            try:
                if key=='password':
                    psji = SimpleCryption()
                    self.props[key] = psji.decode("@==L/;',?##--|?S.&?%##%$|/*@!+_~~zM??m0O0$\\l1L11sWLOO0", config.get("settings", key))
                else:
                    self.props[key] = config.get("settings", key)
            except ConfigParser.NoOptionError:
                continue
            except Exception:
                aplgr.log('Error loading password.')
            
    def loadDefaultSettings(self):
            self.props['tabs_at_top']     = 0
            self.props['show_password']   = 0
            self.props['load_last_session_files'] = 1
            self.props['show_line_numbers'] = 1
    
    def loadDefaultLastUsedSettings(self, settings_file = "mxwst-settings.cfg"):
            dw,dh = wx.DisplaySize()
            self.last_props['app_width']        = dh/1.6
            self.last_props['app_height']       = dh/2.5
            self.last_props['split_position']  = dh/2.5
            self.last_props['app_position_x']   = dw/2-(dw/2.5)/2
            self.last_props['app_position_y']   = dh/2-(dh/1.6)/2
            self.last_props['last_opened_files']   = '([], -1)'
    
    def loadLastUsedSettings(self, settings_file = "mxwst-settings.cfg"):
        
        if(not os.path.isfile(settings_file)):
            aplgr.log('Settings file does not exist: '+settings_file)
            self.loadDefaultLastUsedSettings() 
            return
    
        config = ConfigParser.ConfigParser()
        config.read(settings_file)
        
        for key in self.last_props:
            try:
                self.last_props[key] = config.get("last_used_settings", key)
            except ConfigParser.NoOptionError:
                continue

    def saveSettings(self, settings_file = "mxwst-settings.cfg"):
        try:
            config = ConfigParser.ConfigParser()
            config.read(settings_file)
            
            if not config.has_section('last_used_settings'):
                config.add_section('last_used_settings')

            if not config.has_section('settings'):
                config.add_section('settings')
            sr_width, sr_height =  wx.GetDisplaySize()
            
            config.set('last_used_settings', 'mea_host_url', self.parent.main_panel.RESED_panel.mea_url.GetValue())
            config.set('last_used_settings', 'mea_service', self.parent.main_panel.RESED_panel.mea_srvc.GetValue())                      
            config.set('last_used_settings', 'app_width',       str( sr_width/decimal.Decimal(self.parent.GetSize()[0]+0.000001)) )
            config.set('last_used_settings', 'app_height',      str( sr_height/decimal.Decimal(self.parent.GetSize()[1]+0.000001)) )
            config.set('last_used_settings', 'app_position_x',  str( sr_width/decimal.Decimal(self.parent.GetPosition()[0]+0.000001)) )
            config.set('last_used_settings', 'app_position_y',  str( sr_height/decimal.Decimal(self.parent.GetPosition()[1]+0.000001)) )
            config.set('last_used_settings', 'split_position',  str( decimal.Decimal(self.parent.GetSize()[1])/decimal.Decimal(self.parent.main_panel.sptr1.GetSashPosition()+0.000001) ) )
            config.set('last_used_settings', 'last_opened_files', self.parent.main_panel.XMLED_panel.getOpenedFiles())
            
            config.set('settings', 'request_timeout', self.parent.main_panel.RESED_panel.reqPr.prop_value_timeout.GetValue())
            config.set('settings', 'username',        self.parent.main_panel.RESED_panel.reqPr.prop_value_username.GetValue())
            config.set('settings', 'content-type',    self.parent.main_panel.RESED_panel.reqPr.prop_value_content_type.GetValue())
            config.set('settings', 'soapaction',      self.parent.main_panel.RESED_panel.reqPr.prop_value_soapaction.GetValue())

            try:
                pmsji = SimpleCryption()
                config.set('settings', 'password', pmsji.encode("@==L/;',?##--|?S.&?%##%$|/*@!+_~~zM??m0O0$\\l1L11sWLOO0", self.parent.main_panel.RESED_panel.reqPr.prop_value_password.GetValue()) )
            except Exception:
                aplgr.log('Error encrypting password')
                
            with open(settings_file, 'wb') as configfile:
                config.write(configfile)
            
        except Exception as e:
            aplgr.log('Error saving settings.\n'+e)
            
    def getUserData(self, option, dataFile = "mxwst-userdb.cfg"):
        
            config = ConfigParser.ConfigParser()
            config.read(dataFile)
            
            if not config.has_section('user_data'):
                config.add_section('user_data')
                config.set("user_data", "mea_urls", "")
                config.set("user_data", "mea_services", "")
                with open(dataFile, 'wb') as configfile:
                    config.write(configfile)
                return ''
            
            return config.get("user_data", option)
            
    def saveUserData(self, dataFile = "mxwst-userdb.cfg"):
        
            config = ConfigParser.ConfigParser()
            config.read(dataFile)
            
            if not config.has_section('user_data'):
                config.add_section('user_data')
                config.set("user_data", "mea_urls", "")
                config.set("user_data", "mea_services", "")
                with open(dataFile, 'wb') as configfile:
                    config.write(configfile)

class SimpleCryption():
    def encode(self, key, clear):
        from base64 import urlsafe_b64encode
        enc = []
        for i in range(len(clear)):
            key_c = key[i % len(key)]
            enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
            enc.append(enc_c)
        return urlsafe_b64encode("".join(enc))
    
    def decode(self, key, enc):
        from base64 import urlsafe_b64decode
        dec = []
        enc = urlsafe_b64decode(enc)
        for i in range(len(enc)):
            key_c = key[i % len(key)]
            dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
            dec.append(dec_c)
        return "".join(dec)                           
'''
if __name__ == "__main__":
    sett = Settings(None)
    sett.loadSettings()
    print sett.prop['load_last_session_files']
'''