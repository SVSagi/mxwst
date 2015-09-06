'''
Created on Aug 22, 2015

@author: sarraju
'''
import wx.html
import decimal, os, ntpath, traceback,threading
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.aui as aui
from ast import literal_eval
#import SettingsManager as settings
import STCEditor as stcE
import SettingsManager
import applogger as al

app_name = "MX WS Tester"
app_version = "2.0"
app_build = "14"
is_beta = True

app_info_string = app_name +' v'+ app_version +' build'+ app_build + ( "beta" if (is_beta) else "") 

settings = None
last_settings = None
setng = None

aplgr = al.AppLogger(app_info_string)
                
class XMLTabsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.blank_file_tab_count = 0
        self.nb = aui.AuiNotebook(self, agwStyle=aui.AUI_NB_CLOSE_ON_ALL_TABS|aui.AUI_NB_SMART_TABS|aui.AUI_NB_WINDOWLIST_BUTTON|aui.AUI_NB_TAB_FIXED_WIDTH|aui.AUI_NB_TAB_MOVE|aui.AUI_NB_SCROLL_BUTTONS)
        self.tmsg = trsMessagePanel(self)
        #self.qf_folder_path = ".\\"

        #self.nb.SetTabCtrlHeight(25)
        #self.nb.SetMinMaxTabWidth(5, 10)
        #self.test = wx.Button(self, label='Welcome')

        if(len(literal_eval(last_settings['last_opened_files'])[0])==0):
            self.defE = stcE.NewSTCEditor(self)
            self.defE.format_tab_spaces = int(settings['format_tab_spaces'])
            self.nb.AddPage(self.defE, "New "+str(self.getBlankTabSeq()))
            self.defE.updateLCInfo(None)
        else:
            self.loadFiles(last_settings['last_opened_files'])
        
        import searchService as search
        self.searchPan = search.SearchPanel(self)
        self.searchPan.Hide()
                
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.closeTab, self.nb)
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.tabChanged, self.nb)
        self.nb.Bind(aui.EVT_AUINOTEBOOK_TAB_RIGHT_DOWN, self.showTabContextMenu, self.nb)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.nb, 40, wx.EXPAND)
        self.sizer.Add(self.tmsg, 0, wx.EXPAND)
        self.sizer.Add(self.searchPan, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.tmsg.Hide()
        #self.nb.SetArtProvider(aui.AuiSimpleTabArt())
        #self.nb.NotebookPreview(200)
    
    def showTabContextMenu(self, event):
        tabCMenu = wx.Menu()
        idx = event.GetSelection()
        close_tab = wx.MenuItem(tabCMenu, 200, 'Close')
        close_all = wx.MenuItem(tabCMenu, 201, 'Close All')
        close_others = wx.MenuItem(tabCMenu, 202, 'Close Others')

        #send.SetBitmap(wx.Bitmap('exit.png'))
        tabCMenu.AppendItem(close_tab)
        tabCMenu.AppendItem(close_all)
        tabCMenu.AppendItem(close_others)

        self.Bind(wx.EVT_MENU, lambda event: self.closeTab(event, idx), close_tab)
        self.Bind(wx.EVT_MENU, self.closeAllTabs, close_all)
        self.Bind(wx.EVT_MENU, lambda event: self.closeOtherTabs(event, idx), close_others)
        
        self.PopupMenu(tabCMenu)
    
    def tabChanged(self, event):
        idx = event.GetSelection()
        self.checkExternalModification(idx)
        self.nb.GetPage(idx).updateLCInfo(event)
        self.GetTopLevelParent().SetTitle( self.nb.GetPage(idx).filePath+ " - "+app_info_string)
        
        if self.nb.GetPage(idx).GetModify():
            self.nb.SetPageTextColour(idx, wx.Colour(20,20,250))
        else:
            self.nb.SetPageTextColour(idx, wx.Colour(0,0,0))
            
    def checkExternalModification(self, idx):
        tab = self.nb.GetPage(idx)
        
        if not os.path.exists(tab.filePath) and not tab.filePath=="":
            FCDlg = wx.MessageDialog(None, 'File '+self.nb.GetPageText(idx)+' was deleted. Remove tab?', 'File deleted', wx.YES_NO | wx.ICON_QUESTION)
            if(FCDlg.ShowModal() == wx.ID_YES):
                self.nb.DeletePage(idx)
                return

        
        if tab.isFileModified():
            FCDlg = wx.MessageDialog(None, 'File '+self.nb.GetPageText(idx)+'was modified externally, reload file?', 'External modification', wx.YES_NO | wx.ICON_QUESTION)
            if(FCDlg.ShowModal() == wx.ID_YES):
                self.nb.Parent.loadFile(tab.filePath, force=True)
    
    def saveXMLFile(self, event, idx = -1):
        if idx == -1:
            curTab = self.nb.GetCurrentPage()
        else:
            curTab = self.nb.GetPage(idx)
        
        if curTab == None:
            return
        
        if curTab.filePath == "":
            self.saveAsFile(event, idx)
        
        if not curTab.GetModify():
            return
        
        curTab.SaveFile(curTab.filePath)
        curTab.setFileProps(curTab.filePath)
        
    def saveAsFile(self, event, pageIndex=-1):
        tabG = self.nb

        if(pageIndex==-1):
            pageIndex = tabG.GetSelection()
        
        if pageIndex == -1:
            return
        
        saveAsFileTab = tabG.GetPage(pageIndex)
       
        saveAsDlg = wx.FileDialog(self, message="Save file as ...", defaultDir=".", defaultFile="", wildcard="*.xml", style=wx.SAVE)
        if  saveAsDlg.ShowModal() == wx.ID_OK:
            saveAsPath = saveAsDlg.GetPath()
            saveAsFileTab.filePath=saveAsPath
            saveAsFileTab.SaveFile(saveAsPath)
            saveAsFileTab.setFileProps(os.path.abspath(saveAsPath))
            tabG.SetPageText(pageIndex, saveAsDlg.GetFilename())

        saveAsDlg.Destroy()
        self.tabChanged(event)        
            
    def canCloseTab(self, event, idx = -1):
        tab = self.nb.GetPage(idx)
 
        if tab.filePath == "":
            if tab.GetText() != "":
                FCDlg = wx.MessageDialog(None, 'Save contents in '+self.nb.GetPageText(idx)+' ?', 'Save contents?', wx.YES_NO | wx.ICON_QUESTION)
                #FCDlg.Center()
                if(FCDlg.ShowModal() == wx.ID_YES):
                    saveAsDlg = wx.FileDialog(self, message="Save file as ...", defaultDir=".", defaultFile="", wildcard="*.xml", style=wx.SAVE)
                    if  saveAsDlg.ShowModal() == wx.ID_OK:
                        saveAsPath = saveAsDlg.GetPath()
                        tab.SaveFile(saveAsPath)
                    saveAsDlg.Destroy()

                FCDlg.Destroy()

        elif tab.GetModify():
                FCDlg = wx.MessageDialog(None, 'Save file: '+self.nb.GetPageText(idx), 'Unsaved changes', wx.YES_NO | wx.ICON_QUESTION)
                #FCDlg.Center()
                if(FCDlg.ShowModal() == wx.ID_YES):
                    tab.SaveFile(tab.filePath)
                
                FCDlg.Destroy()
    
    def closeTab(self, event, idx = -1):
        if idx == -1:
            idx = event.GetSelection()
            
        if idx == -1:
            return

        self.canCloseTab(event, idx)
        
        self.nb.DeletePage(idx)

        evtType = event.GetEventType()
        
        if self.nb.GetPageCount() == 0:
            self.GetTopLevelParent().SetTitle(app_info_string)
        
        if evtType == aui.wxEVT_COMMAND_AUINOTEBOOK_PAGE_CLOSE:
            event.Veto()
    
    def closeAllTabs(self, event):
        tabG = self.nb
        while(tabG.GetPageCount()):
            tabG.SetSelection(0)
            self.closeTab(event, 0)
            
    def closeOtherTabs(self, event, indx):
        tabs = self.nb
        curPage = tabs.GetPage(indx)

        if curPage.filePath == "":
            tab_label = self.nb.GetPageText(indx)
        else:
            tab_label =  ntpath.basename(curPage.filePath)            

        tabs.RemovePage(indx)            
        while(tabs.GetPageCount()!=0):
            tabs.SetSelection(0)
            self.closeTab(event, 0)
                
        tabs.InsertPage(0, curPage, tab_label)            
    
    def getBlankTabSeq(self):
        self.blank_file_tab_count+=1
        return self.blank_file_tab_count
    
    def newTab(self, event):
        self.Freeze()
        self.nb.AddPage(stcE.NewSTCEditor(self), "New "+str(self.getBlankTabSeq()), select=True)
        self.Thaw()
    
    def loadFileDlg(self, event):
        oFile = wx.FileDialog(self, "Select file", "", "", "*.xml", wx.OPEN)
        if oFile.ShowModal() == wx.ID_OK:
            #filename=oFile.GetFilename()
            fullFilePath=oFile.GetPath()
            self.loadFile(fullFilePath)
        
    def loadFile(self, file_path, force = False):
        if not os.path.isfile(file_path):
            self.tmsg.showMsg(None, 'File does not exist\n'+os.path.abspath(file_path), "MSG_WARN")
            return

        tabs = self.nb
        
        (alreadyOpened,index) = self.isFileAlreadyOpened(None, os.path.abspath(file_path))
        if(alreadyOpened):
            if force:
                tabs.GetPage(index).LoadFile(file_path)
                tabs.GetPage(index).setFileProps(os.path.abspath(file_path))
            
            tabs.SetSelection(index)
            #self.qf_folder_path = os.path.dirname(file_path)
            return
        
        self.Freeze()
        newE = stcE.NewSTCEditor(self)
        newE.format_tab_spaces = int(settings['format_tab_spaces'])
        newE.setFileProps(os.path.abspath(file_path))
        self.nb.AddPage(newE, ntpath.basename(file_path), select=True)
        self.Thaw()
        newE.LoadFile(file_path)
        #self.qf_folder_path = os.path.dirname(file_path)
        #newE.updateLCInfo(None)
        
    def getOpenedFiles(self):
        tabs = self.nb
        if tabs.GetSelection() == -1:
            return [], -1
                
        opened_files = []
        valid_openfile_index=-1
        
        for t in range(tabs.GetPageCount()):
            file_path = tabs.GetPage(t).filePath
            if(os.path.isfile(file_path)):
                opened_files.append(file_path)

        current_opened_file = tabs.GetPage(tabs.GetSelection()).filePath
        
        for opf in opened_files:
            valid_openfile_index = valid_openfile_index+1
            if(current_opened_file == opf):
                break

        return opened_files, valid_openfile_index

    def loadFiles(self, file_list, listOnly=False):
        if file_list == '':
            return
        
        if listOnly:
            print 'close current files'#@TODO
        
        toBeLoadedFiles = literal_eval(file_list)
        for file in toBeLoadedFiles[0]:
            if(os.path.isfile(file)):
                self.loadFile(file)

        open_indx = int( literal_eval(file_list)[1] )

        if open_indx >= 0 and open_indx+1 <= self.nb.GetPageCount() :
            self.nb.SetSelection(open_indx)
            self.nb.GetPage(open_indx).updateLCInfo(None)
            self.GetTopLevelParent().SetTitle( self.nb.GetPage(open_indx).filePath+ " - "+app_info_string)

    def isFileAlreadyOpened(self, event, filepath):
        tabs = self.nb

        for i in range(tabs.GetPageCount()):
            if(tabs.GetPage(i).filePath==filepath):
                return True, i

        return False, -1
    
    def validateXML(self, event):
        tabs = self.nb
        curTab = tabs.GetCurrentPage()
        curTab.validateXML(event)
    
    def formatXML(self, event):
        tabs = self.nb
        curTab = tabs.GetCurrentPage()
        curTab.formatXML(event)
        
    def startMacroRecord(self, event):
        tabs = self.nb
        curTab = tabs.GetCurrentPage()
        curTab.StartRecordMacro(event)
        
    def stopMacroRecord(self, event):
        tabs = self.nb
        curTab = tabs.GetCurrentPage()
        curTab.StopRecordMacro(event)      
        
    def playRecMarco(self, event):
        tabs = self.nb
        curTab = tabs.GetCurrentPage()
        curTab.PlayMacro()

class trsMessagePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.TRANSPARENT_WINDOW)
        #print self.CanSetTransparent()
        #self.SetTransparent(80)
        self.resp_msg = wx.StaticText(self, -1, "No messages.", style = wx.ALIGN_CENTER)
        #self.resp_msg.Wrap(10)
        self.closeMsg = wx.Button(self, label='Close')
        self.resp_img = self.GetTopLevelParent().getUIBitMap(self, "DEFAULT")
        mhs= wx.BoxSizer(wx.HORIZONTAL)
        mhs.Add(self.resp_img, 0)
        mhs.Add(self.resp_msg, 10)
        #mhs.Add(self.closeMsg, 0)
        self.SetSizer(mhs)
        self.Bind(wx.EVT_BUTTON, self.hideMsg, self.closeMsg)
    
    def showMsg(self, event, msg, code = None):
        self.resp_msg.SetLabel(msg)
        wx.ToolTip.SetDelay(0)
        #tt = wx.ToolTip(msg)
        #tt.SetAutoPop(10000)
        self.resp_msg.SetToolTip(wx.ToolTip(msg))
        self.resp_msg.Center()
        if not self.IsShown():
            self.Show()
            self.GetParent().GetSizer().Layout()
            
        if code != None:
            self.resp_img.SetBitmap(self.GetTopLevelParent().getUIBitMap(self, code).GetBitmap())
            self.Refresh()
        
        self.GetSizer().Layout()
                    
    def hideMsg(self, event):
        if self.IsShown():
            self.Hide()
            self.GetParent().GetSizer().Layout()
    
    def clearMsg(self):
        self.resp_msg.SetLabel('')
        self.resp_img.SetBitmap(self.GetTopLevelParent().getUIBitMap(self, "DEFAULT"))
        self.Refresh()

class BottomPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.nb = aui.AuiNotebook(self, agwStyle=aui.AUI_NB_DRAW_DND_TAB|aui.AUI_NB_BOTTOM)
        
        self.mea_url = wx.ComboBox(self, -1, size=(40, 20))
        self.mea_srvc = wx.ComboBox(self, -1, size=(40, 20))
        self.auth_img = self.GetTopLevelParent().getUIBitMap(self, "UI_AUTH")
        self.use_auth = wx.CheckBox(self, -1)
        self.openFile = wx.BitmapButton(self, -1, self.GetTopLevelParent().getUIBitMap(self, "FILES_ICON"), size=(20,23))
        self.sendXML = wx.Button(self, label='Send')
        
        self.HZBS1= wx.BoxSizer(wx.HORIZONTAL)
        
        self.HZBS1.Add(self.mea_url, 10)
        self.HZBS1.Add(self.mea_srvc, 12)
        self.HZBS1.Add(self.auth_img, 0)
        self.HZBS1.Add(self.use_auth, 0, flag=wx.CENTER)
        self.HZBS1.Add(self.openFile, 0, flag=wx.CENTER)
        self.HZBS1.Add(self.sendXML,6)
        
        self.respE = stcE.NewSTCEditor(self)
        self.respE.isAppTab = True
        self.msgPn = MessagesPanel(self)
        self.reqPr = PropertiesTab(self)
        self.nb.AddPage(self.respE, "Response")
        self.nb.AddPage(self.msgPn, "Messages")
        self.nb.AddPage(self.reqPr, "Properties")

        self.VTBS2= wx.BoxSizer(wx.VERTICAL)
        self.VTBS2.Add(self.HZBS1, 0, wx.EXPAND)
        self.VTBS2.Add(self.nb, 1, wx.EXPAND)

        self.SetSizerAndFit(self.VTBS2)
        
        self.mea_url.SetItems( literal_eval("("+setng.getUserData("mea_urls")+")") )
        self.mea_srvc.SetItems( literal_eval("("+setng.getUserData("mea_services")+")") )
        self.mea_url.SetValue(last_settings['mea_host_url'])
        self.mea_srvc.SetValue(last_settings['mea_service'])

        self.sendXML.Bind(wx.EVT_BUTTON, self.sendXML2WS)
        self.openFile.Bind(wx.EVT_BUTTON, self.openQuickFileMenu)
    
    def openQuickFileMenu(self, event):
        import fnmatch
        tabCMenu = wx.Menu()
        files = []
        dirs = []
        main_dir = ""
        
        for dirname, dirnames, filenames in os.walk(".\\xmls"): #self.Parent.Parent.XMLED_panel.qf_folder_path
            dirs = dirnames
            main_dir = dirname
            for filename in fnmatch.filter(filenames, '*.xml'):
                files.append(os.path.join(dirname, filename))
            break
        
        file_bm = self.GetTopLevelParent().getUIBitMap(self, "FILE_ICON")
        #folder_bm = self.GetTopLevelParent().getUIBitMap(self, "FOLDER_ICON")
        
        for idx, val in enumerate(files):
            mi = wx.MenuItem(tabCMenu, wx.ID_ANY, ntpath.basename(val))
            mi.SetBitmap(file_bm)           
            tabCMenu.AppendItem(mi)
            self.Bind(wx.EVT_MENU, lambda event, val=val: self.Parent.Parent.XMLED_panel.loadFile(val), mi)
        
        for dir in dirs:
            sm = wx.Menu()
            #sm.SetBitmap(folder_bm)
            for f in  os.listdir(main_dir +'\\'+ dir):
                mit = wx.MenuItem(sm, wx.ID_ANY, f)
                mit.SetBitmap(file_bm) 
                sm.AppendItem(mit)
                self.Bind(wx.EVT_MENU, lambda event, dir=dir, f=f: self.Parent.Parent.XMLED_panel.loadFile(main_dir +'\\'+ dir+'\\'+f), mit)
            
            tabCMenu.AppendSubMenu(sm, "[ ] "+dir)
        
        self.PopupMenu(tabCMenu)
        del tabCMenu  
        
    def test(self):
        print 'highlighted'    
   
    def sendXML2WS(self, event):
        import wsManager as ws
        xmlWS = ws.SoapManager(self.GetTopLevelParent())
        xmlWS.soap_start_tag = settings['soap_env_start'] 
        xmlWS.soap_end_tag = settings['soap_env_end']
        xmlWS.format_response = settings['format_response_xml']
        xmlWS.postXML()
        

class MessagesPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.html_win = wx.html.HtmlWindow(self)
                    
        self.EP_HS = wx.BoxSizer(wx.wx.HORIZONTAL)
        self.EP_HS.Add(self.html_win, 1, flag=wx.EXPAND)
        
        self.EP_VS= wx.BoxSizer(wx.VERTICAL)
        self.EP_VS.Add(self.EP_HS, proportion=1, flag=wx.EXPAND)
        self.SetSizerAndFit(self.EP_VS)
        

class PropertiesTab(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.fgs_prop = wx.FlexGridSizer(5, 2, 5, 5)
        
        self.prop_name_username = wx.TextCtrl(self,-1,'username', style=wx.TE_READONLY)
        self.prop_name_password = wx.TextCtrl(self,-1,'password', style=wx.TE_READONLY)
        self.prop_name_timeout = wx.TextCtrl(self,-1,'timeout', style=wx.TE_READONLY)
        self.prop_name_soapaction = wx.TextCtrl(self,-1,'soapaction', style=wx.TE_READONLY)
        self.prop_name_content_type = wx.TextCtrl(self,-1,'content-type', style=wx.TE_READONLY)
        
        self.prop_value_username = wx.TextCtrl(self, -1, settings['username'])
        self.prop_value_password = wx.TextCtrl(self, -1, settings['password'], style=wx.TE_PASSWORD)
        self.prop_value_timeout = wx.TextCtrl(self, -1, settings['request_timeout'])
        self.prop_value_soapaction = wx.TextCtrl(self, -1, settings['soapaction'])
        self.prop_value_content_type = wx.TextCtrl(self, -1, settings['content-type'])
        
        self.fgs_prop.AddMany([(self.prop_name_username),(self.prop_value_username,1,wx.EXPAND),
                          (self.prop_name_password),(self.prop_value_password,1,wx.EXPAND),
                          (self.prop_name_timeout),(self.prop_value_timeout,1,wx.EXPAND),
                          (self.prop_name_soapaction),(self.prop_value_soapaction,1,wx.EXPAND),                                                        
                          (self.prop_name_content_type),(self.prop_value_content_type,1,wx.EXPAND)])            
                            
        self.fgs_prop.AddGrowableCol(1, 1)
        
        hbox.Add(self.fgs_prop, proportion=1, flag=wx.ALL|wx.EXPAND, border=15)
        self.SetSizer(hbox)
        self.SetAutoLayout(1)
        self.SetupScrolling()
                
class MainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        dh = wx.DisplaySize()[1]
        self.sptr1 = wx.SplitterWindow(self)
        
        self.XMLED_panel = XMLTabsPanel(self.sptr1)
        self.RESED_panel = BottomPanel(self.sptr1)
 
        self.sptr1.SplitHorizontally(self.XMLED_panel, self.RESED_panel)
        self.sptr1.SetMinimumPaneSize(40)#@TODO remove hard coded values
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.sptr1, 1, wx.EXPAND)
        self.SetSizer(sizer)
        
        self.sptr1.SetSashPosition( (dh/decimal.Decimal(last_settings['app_height'])+decimal.Decimal(0.000001))/decimal.Decimal(last_settings['split_position'])+decimal.Decimal(0.000001) )
        
class MainFrame(wx.Frame):

    def __init__(self):
        dw,dh = wx.DisplaySize()

        wx.Frame.__init__(self, None, title=app_info_string, size=(dw/decimal.Decimal(last_settings['app_width']), dh/decimal.Decimal(last_settings['app_height'])), pos=(dw/decimal.Decimal(last_settings['app_position_x']), dh/decimal.Decimal(last_settings['app_position_y'])))
        
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetFieldsCount(3)
        self.status_bar.SetStatusWidths([140,150,-1])
        self.main_panel = MainPanel(self)
 
        self.Show()
        
        self.xmlPan = self.main_panel.XMLED_panel
        
        self.menuBar = wx.MenuBar()

        fileMenu = wx.Menu()
        searchMenu = wx.Menu()
        #viewMenu = wx.Menu()
        toolsMenu = wx.Menu()
        aboutMenu = wx.Menu()
        
        ''' dead for now
        macroMenu = wx.Menu()
        macroMenu.AppendItem(wx.MenuItem(macroMenu, 61, 'Start Recording'))
        macroMenu.AppendItem(wx.MenuItem(macroMenu, 62, 'Stop Recording'))
        macroMenu.AppendItem(wx.MenuItem(macroMenu, 63, 'Play Recording\tCtrl+Shift+P'))
        '''
        
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 11, '&New\tCtrl+N'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 12, '&Open\tCtrl+O'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 13, '&Save\tCtrl+S'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 14, '&Save As'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 15, '&Close\tCtrl+W'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 16, '&Close All'))
        fileMenu.AppendItem(wx.MenuItem(fileMenu, 17, '&Exit\tAlt+F4'))

        searchMenu.AppendItem(wx.MenuItem(searchMenu, 22, '&Find\tCtrl+F'))
        searchMenu.AppendItem(wx.MenuItem(searchMenu, 23, '&Find\tF3'))

       
        toolsMenu.AppendItem(wx.MenuItem(toolsMenu, 41, '&Validate XML'))
        toolsMenu.AppendItem(wx.MenuItem(toolsMenu, 42, '&Format XML'))
        #toolsMenu.AppendItem(wx.MenuItem(toolsMenu, 43, '&Format Output XML'))
        #toolsMenu.AppendSubMenu(macroMenu, 'Macro')
        
        aboutMenu.AppendItem(wx.MenuItem(toolsMenu, 53, '&About'))
        
        self.menuBar.Append(fileMenu,    "&File")
        self.menuBar.Append(searchMenu,  "&Search")
        #menuBar.Append(viewMenu,    "&View")
        self.menuBar.Append(toolsMenu,   "&Tools")
        self.menuBar.Append(aboutMenu,   "&Help")

        self.Bind(wx.EVT_MENU, self.xmlPan.newTab, id=11)        
        self.Bind(wx.EVT_MENU, self.xmlPan.loadFileDlg, id=12)
        self.Bind(wx.EVT_MENU, self.xmlPan.saveXMLFile, id=13)
        self.Bind(wx.EVT_MENU, self.xmlPan.saveAsFile, id=14)
        self.Bind(wx.EVT_MENU, self.xmlPan.closeTab, id=15)
        self.Bind(wx.EVT_MENU, self.xmlPan.closeAllTabs, id=16)
        self.Bind(wx.EVT_MENU, self.ExitApp, id=17)
        
        self.Bind(wx.EVT_MENU, self.xmlPan.validateXML, id=41)
        self.Bind(wx.EVT_MENU, self.xmlPan.formatXML, id=42)
        #self.Bind(wx.EVT_MENU, self.xmlPan.formatResponseXML, id=43)
        
        self.Bind(wx.EVT_MENU, self.toggleSearchPanel, id=22)
        
        self.Bind(wx.EVT_MENU, self.showAboutinfo, id=53)
        
        #self.Bind(wx.EVT_MENU, self.xmlPan.startMacroRecord, id=61)  
        #self.Bind(wx.EVT_MENU, self.xmlPan.stopMacroRecord, id=62)  
        #self.Bind(wx.EVT_MENU, self.xmlPan.playRecMarco, id=63)  
        
        wx.EVT_CLOSE(self, self.ExitApp)
        
        self.SetMenuBar(self.menuBar)
        
        if(os.path.isfile("ws.ico")):
            appicon = wx.Icon('ws.ico', wx.BITMAP_TYPE_ICO, 16, 16)
            self.SetIcon(appicon)
        
        self.close_after_update = False
        self.update_ver = ""
        self.update_changes = ""            
        self.upd_thread = None
        try:
            if(settings['check_for_update_onstart']=='1'):
                self.checkUpdate()
        except Exception:
            pass

    def ExitApp(self, event):
        setng.saveSettings()
        self.main_panel.XMLED_panel.closeAllTabs(event)
        if self.upd_thread != None:
            if self.upd_thread.isAlive():
                self.HideWithEffect(wx.SHOW_EFFECT_BLEND, 500)
                self.close_after_update = True
                return
        self.Destroy()
    
    def showAboutinfo(self, event):
        info = wx.AboutDialogInfo()
        #info.SetName('Maximo Web Service Tester')
        info.SetVersion(app_info_string)
        info.SetDescription('Test Maximo web services')
        info.SetCopyright('(C) 2012-2015 Sarraju V Sagi')
        info.SetWebSite('http://sourceforge.net/projects/pymxwst/')
        info.SetLicence("This application is for internal usage only. Please contact application owner for license.")
        info.AddDeveloper('Sarraju V Sagi')
        wx.AboutBox(info)
    
    def getUIBitMap(self, parent, code = "DEFAULT"):
        import resourceManager as rm
        imgrm = rm.Resourcer(parent)
        
        bm = imgrm.getBitMapImg(code)
        del imgrm
        return bm
    
    def toggleSearchPanel(self, event):
        if self.xmlPan.searchPan.IsShown():
            self.xmlPan.searchPan.Hide()
        else:
            self.xmlPan.searchPan.Show()
            
        self.xmlPan.GetSizer().Layout()

    def checkUpdate(self):
        if self.upd_thread != None and self.upd_threadisAlive():
            return
        
        import mxwsapp_updater as upd
        ut = upd.AppUpdate(self, app_version, app_build, is_beta)
        self.upd_thread = threading.Thread(target=ut.notifyInApp)
        self.upd_thread.start()
     
    def showUpdate(self, event):
        updateDlg = wx.AboutDialogInfo()
        updateDlg.SetName('Maximo Web Service Tester Update')
        updateDlg.SetDescription("Update Information:\nVersion: "+self.update_ver +"\n\nChanges:\n"+ self.update_changes )
        updateDlg.SetWebSite('http://sourceforge.net/projects/pymxwst/files/')
        wx.AboutBox(updateDlg)
        
if __name__ == "__main__":
    app = wx.App(False)
    try:
        setng = SettingsManager.Settings(None)
        setng.loadSettings()
        setng.loadLastUsedSettings()
        settings = setng.props
        last_settings = setng.last_props
    except Exception as e:
        aplgr.log(str(traceback.format_exc()))
    
    try:
        frame = MainFrame()
        setng.parent = frame
    except Exception as e:
        aplgr.log(str(traceback.format_exc()))
        errDlg = wx.MessageDialog(None, str(e)+"\n Report this error with logs. See file 'readme.txt' for reporting.", app_info_string+' - Error initializing', wx.OK | wx.ICON_ERROR)
        errDlg.ShowModal()
    app.MainLoop()