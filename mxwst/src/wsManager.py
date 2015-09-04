'''
Created on Aug 24, 2015

@author: sarraju
'''

from base64 import b64encode

class SoapManager():
    def __init__(self, parent):
        self.webservice = None
        self.parent = parent
        self.isHTTPS = False
        self.format_response = 0
        self.xmlPan = parent.main_panel.XMLED_panel
        self.btPan = parent.main_panel.RESED_panel
        
        self.srvr = self.btPan.mea_url.GetValue()
        self.srvc = self.btPan.mea_srvc.GetValue()
        self.timeout = self.btPan.reqPr.prop_value_timeout.GetValue()
        
        self.soap_start_tag = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:max="http://www.ibm.com/maximo"><soapenv:Header/><soapenv:Body>'
        self.soap_end_tag = '</soapenv:Body></soapenv:Envelope>'
        
        try:
            if self.srvr.startswith('http://'):
                self.srvr = self.srvr[self.srvr.index("://")+3:]
            elif(self.srvr.startswith('https://')):
                self.isHTTPS = True
                parent.srvr = self.srvr[self.srvr.index("://")+3:]
                
            self.host = self.srvr[:self.srvr.index("/")]
            self.mea_path = self.srvr[self.srvr.index("/"):]

        except Exception as urle:
            self.xmlPan.tmsg.showMsg(None, 'Error in host url format.\nExpected format: http(s)://servername:port/meaweb/services/', "MSG_WARN")
        
    def postXML(self, id=-1):
        self.btPan.respE.SetText('')
        import socket, httplib
        self.btPan.sendXML.SetLabel('Sending...')
        #self.xmlPan.tmsg.clearMsg()
        #self.xmlPan.tmsg.showMsg(None, 'Sending...' ,"DEFAULT")
        
        tabs = self.xmlPan.nb
        cur_tab_xml = tabs.GetCurrentPage().GetText()
        
        try:
            socket.setdefaulttimeout( int(self.timeout) )
            self.request_xml = self.soap_start_tag + cur_tab_xml + self.soap_end_tag
            
            if(self.isHTTPS == True):
                self.webservice = httplib.HTTPS(self.host)
            else:    
                self.webservice = httplib.HTTP(self.host)
            
            self.webservice.putrequest("POST", self.mea_path+self.btPan.mea_srvc.GetValue())
            self.webservice.putheader("Host", self.host)
            self.webservice.putheader("Content-length", "%d" % len(self.request_xml))
            self.setHeaders()
            self.webservice.endheaders()
            self.webservice.send(self.request_xml)
            self.statuscode, self.statusmessage, self.header = self.webservice.getreply()
            result = self.webservice.getfile().read()
        except httplib.socket.gaierror as gaie:
            self.btPan.sendXML.SetLabel('Send')
            self.xmlPan.tmsg.showMsg(None, str(gaie), "MSG_WARN")
            return
        except httplib.socket.timeout as toe:
            self.btPan.sendXML.SetLabel('Send')
            self.xmlPan.tmsg.showMsg(None, str(toe), "MSG_WARN")
            return
        except Exception as er:
            self.btPan.sendXML.SetLabel('Send')
            self.xmlPan.tmsg.showMsg(None, str(er), "MSG_WARN")
            #aplgr.log("sendXML" + str(traceback.format_exc()))
            return
        
        self.btPan.sendXML.SetLabel('Send')
        if(self.statuscode==200):
            
            self.btPan.respE.SetText(result)
            
            if self.format_response == '1':
                self.btPan.respE.formatXML(None)
            
            self.btPan.nb.SetSelection(0)
            rmsg = str(self.getErrorMsg(result))
            self.xmlPan.tmsg.showMsg(None, 'Response: '+str(self.statuscode)+" - "+str(self.statusmessage) +"\n"+ ( "" if rmsg=='None' else rmsg ), "MSG_OK")
            self.onSendSuccess()
        else:
            #self.btPanel.sendXML.SetLabel('Send')
            if(self.header.get('Content-Type').find('text/html')!=-1):
                self.btPan.nb.SetSelection(1)
                self.xmlPan.tmsg.showMsg(None, str(self.statuscode)+" - "+str(self.statusmessage) +"\n"+ self.getErrorMsg(result), "MSGWARN")#SDlg = wx.MessageDialog(None, 'Error\n'+self.getErrorMsg(result), 'Response: '+str(self.statuscode)+" - "+str(self.statusmessage), wx.OK | wx.wx.ICON_ERROR)
                self.btPan.msgPn.html_win.SetPage(result)
            else:
                self.btPan.respE.SetText(result)
                self.btPan.nb.SetSelection(0)
                self.xmlPan.tmsg.showMsg(None, str(self.statuscode)+" - "+str(self.statusmessage) +"\n"+ self.getErrorMsg(result), "MSGWARN")#SDlg = wx.MessageDialog(None, 'Error\n'+self.getErrorMsg(result), 'Response: '+str(self.statuscode)+" - "+str(self.statusmessage), wx.OK | wx.wx.ICON_ERROR)
                #SDlg.ShowModal()
                
    def getErrorMsg(self,error_xml):
        import xml.dom.minidom
        exml = xml.dom.minidom.parseString(error_xml.encode('utf-8'))
        if exml.getElementsByTagName("faultstring").length > 0:
            return exml.getElementsByTagName("faultstring")[0].firstChild.wholeText
     
    def setHeaders(self):
        try:
            prop_values = self.btPan.reqPr
            username      =  prop_values.prop_value_username.GetValue()
            dwpd          =  prop_values.prop_value_password.GetValue()
            content_type  =  prop_values.prop_value_content_type.GetValue()
            soap_action   =  prop_values.prop_value_soapaction.GetValue()
        
            #self.webservice.putheader("User-Agent",app_name+" v"+app_version)
            self.webservice.putheader("Content-type", content_type) 
            self.webservice.putheader("SOAPAction", soap_action)

            if(self.btPan.use_auth.IsChecked()):
                self.webservice.putheader("Authorization", "Basic %s" % b64encode(b""+username+":"+dwpd).decode("ascii"))
            
        except Exception as hse:
            self.btPan.nb.SetSelection(1)
            raise Exception('Error setting headers: '+str(hse))
    
    def onSendSuccess(self):
        try:
            import ConfigParser
            from ast import literal_eval
            config = ConfigParser.ConfigParser()
            config.read("mxwst-userdb.cfg")
            
            if not config.has_section('user_data'):
                config.add_section('user_data')
            
            saved_urls = config.get("user_data", "mea_urls")
            saved_srvcs = config.get("user_data", "mea_services")
            meaurls = literal_eval("("+saved_urls+")")
            measrvc = literal_eval("("+saved_srvcs+")")
            
            if not self.srvr in meaurls:
                config.set('user_data', 'mea_urls', "'"+self.srvr +"',\n"+ saved_urls)
                
            if not self.srvc in measrvc:
                config.set('user_data', 'mea_services', "'"+self.srvc +"',\n"+ saved_srvcs)

            with open("mxwst-userdb.cfg", 'wb') as configfile:
                config.write(configfile)
        
        except ConfigParser.NoOptionError:
            pass
        except Exception:
            pass