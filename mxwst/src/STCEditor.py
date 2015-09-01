'''
Created on Aug 22, 2015

@author: sarraju
'''

import wx.stc as stc
import wx
import os.path
import xml.dom.minidom

class NewSTCEditor(stc.StyledTextCtrl):
    def __init__(self, parent, style=wx.SIMPLE_BORDER):
        stc.StyledTextCtrl.__init__(self, parent, style=style)
        self.parent = parent
        self.filePath = ""
        self.file_lmd = ""#last modified date
        self.isAppTab = False
        self.appTabName = ""
        self.search_pos = -1
        self.format_tab_spaces = 4
        #self.macro = []
        #self._macro = list()
              
        faces = { 
                  'times': 'Times New Roman',
                  'mono' : 'Courier New',
                  'helv' : 'Arial',
                  'other': 'Consolas',
                  'size' : 10,
                  'size1' : 9,
                  'size2': 8,
                }
        
        #self.SetScrollWidth(100)#@TODO remove hard coded values

        self.SetLexer(stc.STC_LEX_XML)
        self.StyleSetForeground (stc.STC_H_TAG,  wx.Colour(0,0,150))
        self.StyleSetForeground (stc.STC_H_ATTRIBUTE,  wx.Colour(128,0,0))
        self.StyleSetForeground (stc.STC_H_VALUE,  wx.Colour(0, 102, 0))
        self.StyleSetForeground (stc.STC_H_DOUBLESTRING,  wx.Colour(128,0,128))
        
        #self.StyleSetSpec(stc.STC_H_VALUE,"bold")
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(other)s,size:%(size1)d" % faces)
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#C0C0C0,face:%(other)s,size:%(size2)d" % faces)
        
        self.StyleSetSpec(stc.STC_H_DEFAULT,  "fore:#008A2E,normal,face:%(other)s,size:%(size)d" % faces) 

        self.SetMargins(0,0)
        self.SetFoldFlags(16)
        
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.SetMarginType(1, stc.STC_MARGIN_SYMBOL)

        self.SetMarginMask(1, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(1, True)
        
        self.SetMarginWidth(0, 44)
        self.SetMarginWidth(1, 16)
        
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,    "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,  "white", "black")
        self.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS, "white", "black")
        
        self.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        #self.Bind(stc.EVT_STC_MACRORECORD, self.OnRecordMacro)# not working :(
        
        self.Bind(wx.EVT_RIGHT_UP, self.onRightUp)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.onLeftUp)
        self.Bind(wx.EVT_KEY_UP, self.onKeyUp)
        #self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.SetProperty("fold", "1")
        self.SetProperty("fold.html", "1")
     
    #thanks pyface    
    def OnMarginClick(self, evt):
            # fold and unfold as needed
            if evt.GetMargin() == 1:
                if evt.GetShift() and evt.GetControl():
                    self.FoldAll()
                else:
                    lineClicked = self.LineFromPosition(evt.GetPosition())
                    if self.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                        if evt.GetShift():
                            self.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 1)
                        elif evt.GetControl():
                            if self.GetFoldExpanded(lineClicked):
                                self.SetFoldExpanded(lineClicked, False)
                                self.Expand(lineClicked, False, True, 0)
                            else:
                                self.SetFoldExpanded(lineClicked, True)
                                self.Expand(lineClicked, True, True, 100)
                        else:
                            self.ToggleFold(lineClicked)
  
  
    def FoldAll(self):
        lineCount = self.GetLineCount()
        expanding = True
  
        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.GetFoldExpanded(lineNum)
                break;
  
        lineNum = 0
        while lineNum < lineCount:
            level = self.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:
  
                if expanding:
                    self.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.GetLastChild(lineNum, -1)
                    self.SetFoldExpanded(lineNum, False)
                    if lastChild > lineNum:
                        self.HideLines(lineNum+1, lastChild)
  
            lineNum = lineNum + 1
  
    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.GetLastChild(line, level)
        line = line + 1
        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.ShowLines(line, line)
                else:
                    self.HideLines(line, line)
            else:
                if doExpand:
                    self.ShowLines(line, line)
  
            if level == -1:
                level = self.GetFoldLevel(line)
  
            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.SetFoldExpanded(line, True)
                    else:
                        self.SetFoldExpanded(line, False)
                    line = self.Expand(line, doExpand, force, visLevels-1)
  
                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1;
  
        return line
    
    def OnKeyDown(self, event):
        pass
                
    def onKeyUp(self,event):
        self.updateLCInfo(event)
        event.Skip(True)
    
    def onLeftDown(self, event):
        if hasattr( self.parent, 'tmsg'):
            self.parent.tmsg.hideMsg(event)
        
        self.updateLCInfo(event)
        
        event.Skip(True)
    
    def onLeftUp(self, event):
        self.updateLCInfo(event)
        #self.highlight_selection(event) # need to figure out styling
        event.Skip(True)
    
    def onRightUp(self, event):
        menu1 = wx.Menu()
        sendOp = wx.MenuItem(menu1, 100, 'Send')
        formatXML = wx.MenuItem(menu1, 101, 'Format')
        validateXML = wx.MenuItem(menu1, 102, 'Validate')
        wrap_txt = "Wrap" if (self.GetWrapMode()==0) else "Un Wrap"
        wrapToggle = wx.MenuItem(menu1, 103, wrap_txt)
        showLastMsg = wx.MenuItem(menu1, 104, 'Show last message')
        
        self.Bind(wx.EVT_MENU, self.onSendXML, id=100)
        self.Bind(wx.EVT_MENU, self.formatXML, id=101)
        self.Bind(wx.EVT_MENU, self.validateXML, id=102)
        self.Bind(wx.EVT_MENU, self.toggleWrap, id=103)
        self.Bind(wx.EVT_MENU, self.showLastMSG, id=104)
        

        if(not self.isAppTab):
            menu1.AppendItem(sendOp)
            
        menu1.AppendItem(formatXML)
        menu1.AppendItem(validateXML)
        menu1.AppendItem(wrapToggle)
        menu1.AppendItem(showLastMsg)
        # self.Bind(wx.EVT_MENU_HIGHLIGHT, self.showItemHelp, id=100)# not working :( works only for menubar menu
        self.PopupMenu(menu1, event.GetPosition())

    def showLastMSG(self, event):
        if self.isAppTab:
            self.Parent.Parent.Parent.Parent.XMLED_panel.tmsg.Show()
            self.Parent.Parent.Parent.Parent.XMLED_panel.GetSizer().Layout()            
        else:
            self.Parent.Parent.tmsg.Show()
            self.Parent.Parent.GetSizer().Layout()
     
    def updateLCInfo(self, event):
        curPage = self.parent.nb.GetCurrentPage()
        cur_idx = self.parent.nb.GetSelection()
        
        self.search_pos = self.parent.nb.GetCurrentPage().GetCurrentPos()
        self.GetTopLevelParent().status_bar.SetStatusText("Line:%s   Col:%s" % (self.GetCurrentLine()+1, self.GetColumn(self.GetCurrentPos())), number=0)
        self.GetTopLevelParent().status_bar.SetStatusText("Length: %s Sel: %s" % (self.GetLength(), len(self.GetSelectedText())), number=1)
        
        if not self.isAppTab:
            if curPage.GetModify():
                self.Parent.SetPageTextColour(cur_idx, wx.Colour(20,20,250))
            else:
                self.Parent.SetPageTextColour(cur_idx, wx.Colour(0,0,0))         
        
    def onSendXML(self, event):
        self.GetTopLevelParent().main_panel.RESED_panel.sendXML2WS(None)
    
    def toggleWrap(self, event):
        cur_wm = self.GetWrapMode()
        self.SetWrapMode(1-cur_wm)

    def highlight_selection(self,event):
        self.StyleClearAll()
        #self.StyleSetSpec(40, "color:#FF0000" )
        self.StyleSetSpec(40, "bold,cordial,fore:#0000FF")
        selected_text = self.GetSelectedText()
        fAt = 0
        if selected_text == '':
            self.StyleClearAll()
            pass
        else:
            while fAt!=-1:
                fAt = self.findText(event, fAt+len(self.GetSelectedText()))
                if fAt !=-1:
                    self.StartStyling(fAt, 0xffff)
                    self.SetStyling( len(self.GetSelectedText()), 40 )
                    #self.SetStyle(fAt, fAt+len(selected_text), highlight_style)
    
    def findText(self, event, fAt):
        xmlString = self.GetText()
        searchString = self.GetSelectedText()
        self.find =  xmlString.find(searchString, fAt, len( xmlString ) )
        return self.find
                    
    def validateXML(self, event):
        tabs = self.parent.nb
        curTabPanel = tabs.GetCurrentPage()
        self.GetTopLevelParent().main_panel.RESED_panel.msgPn.html_win.SetPage("")
        try:
            xml.dom.minidom.parseString(curTabPanel.GetText())
        except Exception as e:
            #l,c = eval(((str(e)[str(e).index('line'):]).replace('line', '')).replace('column', ''))
            self.showMessage(e, True)           
            #aplgr.log("validateXML: "+str(traceback.format_exc()))
            return
        
        self.showMessage('XML Validation passed')

    def formatXML(self, event):
        import re
        tabG = self.parent.nb
        curTabPanel = tabG.GetCurrentPage()
        self.GetTopLevelParent().main_panel.RESED_panel.msgPn.html_win.SetPage("")
        tab_spaces = self.format_tab_spaces
        try:
            xml.dom.minidom.parseString(curTabPanel.GetText())
            fields = re.split('(<.*?>)',curTabPanel.GetText())
            level = 0
            fxml = ""
            last_str = ""
            
            for f in fields:
                if f.strip() == '': continue
                
                if f[:5] == '<?xml' and f[-2:] =='?>':
                    fxml += f +"\n"
                    continue

                if f[0]=='<' and f[1] != '/':
                    fxml += ' '*(level*tab_spaces) + f +"\n"
                    level = level + 1
                    if f[-2:] == '/>':
                        level = level - 1
                elif f[:2]=='</':
                    level = level - 1
                    if fxml[-2:] == '>\n':
                        p_tag = last_str[1:len(f[2:-1])+1]
                        l_char = last_str[len(f[2:-1])+1:len(f[2:-1])+2]
                        if f[2:-1] == p_tag and (l_char=='>' or l_char==' '):
                            fxml = fxml[:-1]
                            fxml += f + "\n"
                        else:    
                            fxml += ' '*(level*tab_spaces) + f +"\n"
                    else:
                        fxml += f +"\n"        
                else:
                    if f[0]!='<':
                        fxml = fxml[:-1] + f
                    else:    
                        fxml +=  f +"\n"                    
                last_str=f
                      
            if fxml[-1:] == '\n':
                fxml =fxml[:-1]
            
            curTabPanel.SetText(fxml)
            
        except Exception as e:
            self.showMessage(e, True)
        
    
    def showMessage(self, msg, error=False):
        msgr = self.Parent.Parent.tmsg 
        if error:
            if self.isAppTab:
                msgr.showMsg(None, str(msg), "MSG_WARN")
            else:
                msgr.showMsg(None, str(msg), "MSG_WARN")
        else:
            if self.isAppTab:
                msgr.showMsg(None, str(msg), "MSG_OK")
            else:
                msgr.showMsg(None, str(msg), "MSG_OK")            
                
    def isFileModified(self):
        if(not os.path.isfile(self.filePath)):
            return False
        if self.filePath == "":
            return False
        
        if self.file_lmd == "":#saveas
            return False
        
        return self.file_lmd != os.path.getmtime(self.filePath)
    
    def contentChanged(self):
        #return False
        editor_content = self.GetTextUTF8()
        file_obj = open(self.filePath, 'r')
        file_content = file_obj.read()
        file_obj.close()
        
        return editor_content != file_content
            
    def setFileProps(self, fpath):
        self.filePath = fpath
        self.file_lmd = os.path.getmtime(fpath)
        
'''        
    def OnRecordMacro(self, event):
        if self.recording:
            msg = event.GetMessage()
            if msg == 2170:
                pos = self.GetCurrentPos()
                lparam = self.GetTextRange(pos-1, pos)
            else:
                lparam = event.GetLParam()
            macro = (msg, event.GetWParam(), lparam)
            self.macro.append(macro)
        else:
            event.Skip()

    def StartRecordMacro(self, event):
        self.recording = True
        self.StartRecord()

    def StopRecordMacro(self, event):
        self.recording = False
        self.StopRecord()
        
    def PlayMacro(self):
        for msg in self._macro:
            if msg[0] == 2170:
                self.AddText(msg[2])
            elif msg[0] == 2001:
                self.AddText(self.GetEOLChar() + u' ' * (msg[1] - 1))
            else:
                self.SendMsg(msg[0], msg[1], msg[2])
        self.EndUndoAction()        
'''
        