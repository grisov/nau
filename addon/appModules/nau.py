# coding: utf-8
# A part of the NVDA NAU Enhancements add-on
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2021 Olexandr Gryshchenko <grisov.nvaccess@mailnull.com>

import appModuleHandler
import api
import controlTypes
import textInfos
from NVDAObjects.behaviors import Dialog, FocusableUnfocusableContainer
from NVDAObjects.IAccessible import IAccessible, sysListView32
from displayModel import DisplayModelTextInfo
from speech import speakMessage, cancelSpeech
from scriptHandler import script
from tones import beep


def getNauStatusBarText() -> str:
	try:
		info = api.getForegroundObject().appModule.statusBarTextInfo
	except (NotImplementedError, AttributeError,):
		info = api.getForegroundObject().flatReviewPosition
		if info:
			info.expand(textInfos.UNIT_STORY)
			info.collapse(True)
			info.expand(textInfos.UNIT_LINE)
	if info:
		return info.text.strip()
	return ''

def getCurrentItemIndex() -> int:
	try:
		return int(getNauStatusBarText().split(":")[1])-1
	except (TypeError, ValueError, IndexError,):
		return -1

def getItemsCount() -> int:
	try:
		return int(getNauStatusBarText().split(":")[0])
	except (TypeError, ValueError,):
		return -1

def parseItemsFromString(text: str, count: int) -> list:
	separator = 't'
	items = [item for item in text.split(separator) if item.strip()!='']
	if len(items)==count:
		return items
	items = []
	for index in range(count):
		while len(text)>0 and text[-1]==separator:
			text = text[:-1]
		if index==count-1:
			items.insert(0, text)
			break
		cap = False
		for i in range(len(text)-1, -1, -1):
			if text[i]==separator:
				items.insert(0, text[i+1:])
				text = text[:i]
				break
			if not text[i].isascii() and text[i].islower() and cap:
				items.insert(0, text[i+1:])
				text = text[:i+1]
				break
			cap = text[i].isupper()
	return items



class NauDialog(Dialog):
	role = controlTypes.ROLE_PANE

	def getDialogText(self, *args, **kwargs):
		text = super(NauDialog, self).getDialogText(*args, **kwargs) or ''
		if not text or text.isspace():
			dModel = DisplayModelTextInfo(self, textInfos.POSITION_FIRST)
			dModel.includeDescendantWindows=False
			text = dModel.text
		return text


class NauCheckBox(IAccessible):
	role = controlTypes.ROLE_CHECKBOX


class NauButton(IAccessible):
	role = controlTypes.ROLE_BUTTON
	isFocusable = True


class NauListView(sysListView32.List):
	role = controlTypes.ROLE_LIST

	def _get_rowCount(self):
		return getItemsCount()


class NauListViewItem(sysListView32.ListItem):
	role = controlTypes.ROLE_LIST
	shouldAllowIAccessibleFocusEvent = True
	items = []
	lastItem = 0

	def _get_rowCount(self):
		return getItemsCount()

	def _get_rowNumber(self):
		return getCurrentItemIndex()

	@script(gesture="kb:nvda+shift+i")
	def script_announceNumberAndCount(self, gesture):
		speakMessage("%d of %d" % (self.rowNumber+1, self.rowCount))

	def _get_displayText(self):
		return DisplayModelTextInfo(self, textInfos.POSITION_ALL).text

	def event_becomeNavigatorObject(self, isFocus):
		self.items = parseItemsFromString(self.displayText, self.rowCount)

	def _get_value(self):
		for i in range(10):
			try:
				return self.items[self.rowNumber]
			except IndexError:
				self.items = parseItemsFromString(self.displayText, self.rowCount)
		return self.displayText

	@script(gestures=["kb:upArrow", "kb:control+upArrow", "kb:shift+upArrow",
		"kb:home", "kb:control+home", "kb:shift+home"])
	def script_moveToPreviousRow(self, gesture):
		gesture.send()
		if self.rowNumber==0 and self.lastItem==0:
			beep(500, 15)
		self.lastItem = self.rowNumber
		speakMessage(self.value)

	@script(gestures=["kb:downArrow", "kb:control+downArrow", "kb:shift+downArrow",
		"kb:end", "kb:control+end", "kb:shift+end"])
	def script_moveToNextRow(self, gesture):
		gesture.send()
		if self.rowNumber==self.rowCount-1 and self.lastItem==self.rowCount-1:
			beep(1000, 15)
		self.lastItem = self.rowNumber
		speakMessage(self.value)

	def event_mouseMove(self, x, y):
		left,top,width,height = self.location
		if left<x<left+width and top<y<top+height:
			cancelSpeech()
			speakMessage(self.displayText)


class NauToolBarContainer(FocusableUnfocusableContainer):
	role = controlTypes.ROLE_GROUPING

	def event_becomeNavigatorObject(self, isFocus):
		self.firstChild.firstChild .setFocus()

	def _get_name(self):
		return None


class NauToolBar(IAccessible):
	role = controlTypes.ROLE_TOOLBAR


class AppModule(appModuleHandler.AppModule):

	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
		if obj.windowClassName == "TMessageForm" and obj.role==controlTypes.ROLE_PANE:
			clsList.insert(0, NauDialog)
		elif obj.windowClassName == "TCheckBox":
			clsList.insert(0, NauCheckBox)
		elif obj.windowClassName == "TButton":
			clsList.insert(0, NauButton)
		elif obj.windowClassName == "TRichView":
			clsList.insert(0, NauListView if obj.role==controlTypes.ROLE_WINDOW else NauListViewItem)
		elif obj.windowClassName == "TdxContainer" and obj.role==controlTypes.ROLE_PANE:
			clsList.insert(0, NauToolBarContainer)
		elif obj.windowClassName == "TdxWinXPBar":
			clsList.insert(0, NauToolBar if obj.role==controlTypes.ROLE_WINDOW else NauToolBar)
