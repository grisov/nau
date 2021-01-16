# coding: utf-8
import appModuleHandler
from api import getForegroundObject
from NVDAObjects.behaviors import Dialog, FocusableUnfocusableContainer
from NVDAObjects.IAccessible import IAccessible, ListviewPane, sysListView32
from controlTypes import ROLE_PANE, ROLE_BUTTON, ROLE_WINDOW
import controlTypes
import speech
from displayModel import DisplayModelTextInfo
from textInfos import POSITION_FIRST, POSITION_ALL
from scriptHandler import script
from tones import beep
import ui
import inputCore
import keyboardHandler


class NauDialog(Dialog):

	def _get_role(self):
		return ROLE_PANE

	def getDialogText(self, *args, **kwargs):
		text = super(NauDialog, self).getDialogText(*args, **kwargs) or ''
		if not text or text.isspace():
			dModel = DisplayModelTextInfo(self, POSITION_FIRST)
			dModel.includeDescendantWindows=False
			text = dModel.text
		return text

class NauCheckBox(IAccessible):

	def _get_role(self):
		return controlTypes.ROLE_CHECKBOX


class NauButton(IAccessible):
	isFocusable = True
	#hasFocus = True
	isPresentableFocusAncestor = True

	def _get_role(self):
		return ROLE_BUTTON


class FUC(FocusableUnfocusableContainer):

	def _get_role(self):
		return ROLE_WINDOW

	def _get_children(self):
		return [ch for ch in self.recursiveDescendants]

	def _get_next(self):
		return self.parent.simpleNext

	def _get_previous(self):
		return self.parent.simplePrevious

	firstChild = None

class NauListView(sysListView32.List):
	role = controlTypes.ROLE_LIST


class NauListViewItem(sysListView32.ListItem):
	role = controlTypes.ROLE_LIST
	shouldAllowIAccessibleFocusEvent = True
	index = 0
	items = []

	def event_becomeNavigatorObject(self):
		inputCore.manager.emulateGesture(keyboardHandler.KeyboardInputGesture.fromName("home"))
		self.items = [item for item in DisplayModelTextInfo(self, POSITION_ALL).text.split('t') if item.strip()!='']

	@script(gestures=["kb:upArrow", "kb:downArrow", "kb:home", "kb:end"])
	def script_listViewNavigator(self, gesture):
		if "upArrow" in gesture.mainKeyName:
			self.index = max(self.index-1, 0)
		elif "downArrow" in gesture.mainKeyName:
			self.index = min(self.index+1, len(self.items)-1)
		elif "home" in gesture.mainKeyName:
			self.index=0
		elif "end" in gesture.mainKeyName:
			self.index=len(self.items)-1
		gesture.send()
		if self.index in range(len(self.items)):
			ui.message("%d - %d - %s" % (len(self.items), self.index, self.items[self.index]))

	def asd(self):
		self.name = 'test'
		if self.name:
			speakList=[]
			if controlTypes.STATE_SELECTED in self.states:
				speakList.append(controlTypes.stateLabels[controlTypes.STATE_SELECTED])
			speakList.append(self.name.split("\\")[-1])
			speech.speakMessage(" ".join(speakList))
		else:
			super(NauMainList, self).reportFocus()

	def event_stateChange(self):
		beep(3000, 15)


import controlTypes
import NVDAObjects.IAccessible
import windowUtils
import api
import winUser
from NVDAObjects.window import Window

def getDocument():
	try:
		document = NVDAObjects.IAccessible.getNVDAObjectFromEvent(
			windowUtils.findDescendantWindow(api.getForegroundObject().windowHandle, className='TNAUMain'),
			winUser.OBJID_CLIENT, 0)
		return document
	except LookupError:
		return None

class EPW(Window):

	def event_gainFocus(self):
		document = getDocument()
		if document:
			document.setFocus()

class Panel(IAccessible):
	pass


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

		elif obj.windowClassName == "TPanel":
			#clsList.insert(0, Panel)
			pass
		elif obj.windowClassName == "TdxWinXPBar":
			#clsList.insert(0, NauButton)
			pass
		elif obj.windowClassName == "TNAUMain":
			#clsList.insert(0, EPW)
			pass
			#beep(777, 50)
