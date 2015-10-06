'''
Created on Aug 27, 2015

@author: sarraju
'''

import wx
class SearchPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.SIMPLE_BORDER)
        self.Tabs = self.Parent.nb
        #self.respTab = self.Parent.Parent.Parent.RESED_panel

        self.search_responseCB = wx.CheckBox(self, -1, label='Search Response')
        self.matchCaseCB = wx.CheckBox(self, -1, label='Match Case')
        self.wrapSearchCB = wx.CheckBox(self, -1, label='Wrap Search')        
        self.findString = wx.TextCtrl(self,-1)
        self.replaceString = wx.TextCtrl(self,-1)
        self.findBtn = wx.Button(self, label='Find')
        self.replaceBtn = wx.Button(self, label='Replace')
        self.replaceAllBtn = wx.Button(self, label='Replace All')
        self.close_search = wx.Button(self, label='Close')

        self.sHB1= wx.BoxSizer(wx.HORIZONTAL)
        self.sHB2= wx.BoxSizer(wx.HORIZONTAL)

        self.sHB1.Add(self.search_responseCB)
        self.sHB1.Add(self.matchCaseCB)
        self.sHB1.Add(self.wrapSearchCB)

        self.sHB2.Add(self.findString)
        self.sHB2.Add(self.replaceString)
        self.sHB2.Add(self.findBtn)
        self.sHB2.Add(self.replaceBtn)
        self.sHB2.Add(self.replaceAllBtn)
        self.sHB2.Add(self.close_search)

        self.sVB1= wx.BoxSizer(wx.VERTICAL)

        self.sVB1.Add(self.sHB1)
        self.sVB1.Add(self.sHB2)

        self.SetSizerAndFit(self.sVB1)

        self.findBtn.Bind(wx.EVT_BUTTON, self.onFind)
        self.replaceBtn.Bind(wx.EVT_BUTTON, self.onReplace)
        self.replaceAllBtn.Bind(wx.EVT_BUTTON, self.onReplaceAll)
        self.close_search.Bind(wx.EVT_BUTTON, self.hideShowSearchPanel)

    def hideShowSearchPanel(self, event):        
        if self.Parent.searchPan.IsShown():
            self.Parent.sizer.Hide(self.Parent.searchPan)
            self.Parent.GetSizer().Layout()
        else:
            self.Parent.sizer.Show(self.Parent.searchPan)
            self.Parent.GetSizer().Layout()
    
    def onFind(self, event):
        self.findText(event)
        
    def onReplace(self, event):
        searchInResp = self.search_responseCB.GetValue()
        
        if searchInResp:
            self.GetTopLevelParent().status_bar.SetStatusText("Replace in response is not supported", number=1)
            return
            
        cur_tab = self.Tabs.GetCurrentPage()
        cur_editor = cur_tab
        searchString = self.findString.GetValue()
        selected_text = cur_editor.GetSelectedText()

        if cur_editor.GetCurrentPos() == cur_editor.search_pos and searchString == selected_text:
            foundAt = cur_editor.search_pos
        else:
            foundAt = self.findText(event)
        
        if foundAt != -1:
            #cur_editor.Replace(foundAt, foundAt+len(searchString), self.replaceString.GetValue())
            cur_editor.ReplaceSelection(self.replaceString.GetValue())
            tmp = cur_editor.search_pos
            self.findText(event)
            cur_editor.search_pos = tmp
            return foundAt
        else:
            return -1        
        
    def onReplaceAll(self, event):
        searchInResp = self.search_responseCB.GetValue()
        
        if searchInResp:
            self.GetTopLevelParent().status_bar.SetStatusText("Replace in response is not supported", number=1)
            return
        
        cur_tab = self.Tabs.GetCurrentPage()
        cur_editor = cur_tab
        cur_editor.BeginUndoAction()
        cur_editor.search_pos = 0
        repCount = 0
        while True:
            if self.onReplace(event) == -1:
                break
            repCount = repCount + 1        
        cur_editor.EndUndoAction()
        
    def findText(self, event):
        searchInResp = self.search_responseCB.GetValue()

        if searchInResp:
            cur_editor = self.GetTopLevelParent().main_panel.RESED_panel.nb.GetPage(0)
        else:
            cur_tab = self.Tabs.GetCurrentPage()
            #cur_editor = cur_tab.GetText()
            cur_editor = cur_tab
            
        xmlString = cur_editor.GetText()
        searchString = self.findString.GetValue()
        selected_text = cur_editor.GetSelectedText()
        
        if searchString == '' and selected_text !='':
            self.findString.SetValue(selected_text)
            searchString = selected_text
        
        matchCase = self.matchCaseCB.GetValue()
        wrapSearch = self.wrapSearchCB.GetValue()
        
        if not matchCase:
            xmlString = xmlString.lower()
            searchString = searchString.lower()
            selected_text = selected_text.lower()
        
        if cur_editor.search_pos == 0:
            pass
        elif cur_editor.search_pos != -1:
            cur_editor.search_pos = cur_editor.search_pos+len(searchString)
        else:
            cur_editor.search_pos = cur_editor.GetCurrentPos()
        self.find =  xmlString.find(searchString, cur_editor.search_pos, len( xmlString ) )
        
        if self.find != -1:
            cur_editor.SetSelection(self.find, self.find+len( searchString ))
        else:
            cur_editor.SetSelection(0,0)
            
        if self.find == -1 and cur_editor.search_pos != -1:
            if wrapSearch:
                cur_editor.search_pos = 0
                self.GetTopLevelParent().status_bar.SetStatusText("Wrapping Search", number=1)
            else:    
                self.GetTopLevelParent().status_bar.SetStatusText("End of Search", number=1)
        elif self.find == -1 and cur_editor.search_pos == 0:
            self.GetTopLevelParent().status_bar.SetStatusText("Search string '"+searchString+"'not found", number=1)    
        else:
            self.GetTopLevelParent().status_bar.SetStatusText("", number=1)    
        
        if cur_editor.search_pos != 0:
            cur_editor.search_pos = self.find
        elif cur_editor.search_pos == 0 and self.find != -1:
            cur_editor.search_pos = self.find
            
        return self.find