import ctypes
import time
import math
import os
import pynput
import random
import tkinter
from ast import literal_eval
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import key_translation

PROCESS_PER_MONITOR_DPI_AWARE = 2
movementFraction = 1000.0
fileExtension = ".mr"

class Recording:
    
    # Initialize the recording with no events and a lastEventTime variable
    def __init__(self):
        self.events = []
        self.lastEventTime = time.time()
        
    # Reset the recording back to no events
    def ClearRecording(self):
        self.events = []
        self.lastEventTime = time.time()
        
    # Used when loading a recording from text
    def AddEventFromText(self, text):
        parameters = (text.strip()).split(" ")
        if len(parameters) == 3:
            self.AddKeyboardEventFromText(parameters)
        else:
            self.AddMouseEventFromText(parameters)
            
    def AddEventFromGrid(self, values):
        if values[1] == "Keyboard":
            self.AddKeyboardEventFromText([values[5], values[2], values[3]])
        else:
            position = literal_eval(values[4])
            self.AddMouseEventFromText([values[5], values[2], values[3], position[0], position[1], position[2], position[3]])
    
    # Used when adding a keyboard event. delayTime is only provided if adding from text
    def AddKeyboardEvent(self, key, pressed, delayTime = None, delayTime2 = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
            delayTime2 = delayTime
        self.lastEventTime = eventTime
        event = KeyboardEvent(delayTime, delayTime2, key, pressed)
        self.events.append(event)
    
    # Used when adding a keyboard event from text
    def AddKeyboardEventFromText(self, params):
        [delay, key, pressed] = params
        [delayTime, delayTime2] = [float(t) for t in delay.split("-")]
        key = key_translation.textToKey[key] if key in key_translation.textToKey else pynput.keyboard.KeyCode.from_char(key)
        pressed = True if pressed == "True" else False
        self.AddKeyboardEvent(key, pressed, delayTime, delayTime2)
        
    # Used when adding a mouse event. delayTime is only provided if adding from text
    def AddMouseEvent(self, button, pressed, x, y, x2 = None, y2 = None, delayTime = None, delayTime2 = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
            delayTime2 = delayTime
        if x2 == None or y2 == None:
            x2 = x
            y2 = y
        self.lastEventTime = eventTime
        event = MouseEvent(delayTime, delayTime2, button, pressed, x, y, x2, y2)
        self.events.append(event)
        
    # Used when adding a keyboard event from text
    def AddMouseEventFromText(self, params):
        [delay, button, pressed, x, y, x2, y2] = params
        [delayTime, delayTime2] = [float(t) for t in delay.split("-")]
        button = key_translation.textToButton[button]
        pressed = True if pressed == "True" else False
        x = int(x)
        y = int(y)
        x2 = int(x2)
        y2 = int(y2)
        self.AddMouseEvent(button, pressed, x, y, x2, y2, delayTime, delayTime2)
      
    # Return the list of events  
    def GetEvents(self):
        return self.events
    
    # Return a specific event
    def GetEvent(self, which):
        return self.events[which]
    
    # Emulate the mouse and keyboard to recreate the recorded events
    def Playback(self, hotkey):
        
        # Listen on the keyboard for the user to press the cancel button
        cancel = False
        def on_press(key):
            nonlocal cancel
            if key == hotkey:
                cancel = True
                return False
        listener = pynput.keyboard.Listener(on_press = on_press)
        listener.start()       
        
        # Track the pressed objects, and mock the mouse and keyboard
        pressedKeys = []
        pressedMouse = []
        keyboard = pynput.keyboard.Controller()
        mouse = pynput.mouse.Controller()
        for event in self.GetEvents():
            if cancel:
                break
            if type(event) == KeyboardEvent:
                event.Playback(keyboard)
                key = event.GetKey()
                if event.GetKeyPressed() and key not in pressedKeys:
                    pressedKeys.append(key)
                elif not event.GetKeyPressed() and key in pressedKeys:
                    pressedKeys.remove(key)
            else:
                event.Playback(mouse)
                button = event.GetButton()
                if event.GetButtonPressed() and button not in pressedMouse:
                    pressedMouse.append(button)
                elif not event.GetButtonPressed() and button in pressedMouse:
                    pressedMouse.remove(button)
                    
        # Make sure that the mouse and keyboard don't leave anything held down
        for key in pressedKeys:
            keyboard.release(key)
        for button in pressedMouse:
            mouse.release(button)
    
    # Print the events in the recording  
    def PrintRecording(self):
        counter = 0
        for event in self.GetEvents():
            print("Event", counter)
            event.PrintEvent()
            counter += 1
    
class KeyboardEvent:
    
    delayTime = 0
    delayTime2 = 0
    key = None
    pressed = False
    
    # Initialize the keyboard event with a delayTime, which key, and whether it was pressed or released
    def __init__(self, delayTime, delayTime2, key, pressed):
        self.delayTime = delayTime
        self.delayTime2 = delayTime2
        self.key = key
        self.pressed = pressed
        
    # Return the delayTime
    def GetDelayTime(self):
        return self.delayTime
    
    def GetDelayTime2(self):
        return self.delayTime2
    
    def GetDelayRange(self):
        return self.delayTime2 - self.delayTime
    
    # Return the key
    def GetKey(self):
        return self.key
     # Return whether the key was pressed or released
    def GetKeyPressed(self):
        return self.pressed
    
    # Return whether the key is a pynput.Key or pynput.KeyCode
    def GetKeyType(self):
        return type(self.key)
    
    # Return the text label for the key
    def GetKeyLabel(self):
        if self.GetKeyType() == pynput.keyboard.KeyCode:
            return self.GetKey().char
        return key_translation.keyToText[self.key]
    
    # Given a virtual keyboard, replay the keyboard event
    def Playback(self, keyboard):
        time.sleep(self.GetDelayTime()) + random.uniform(0, self.GetDelayRange())
        if self.GetKeyPressed():
            keyboard.press(self.GetKey())
        else:
            keyboard.release(self.GetKey())
           
    # Turn the event into text for saving to a file 
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()) + "-" + str(self.GetDelayTime2()), self.GetKeyLabel(), str(self.GetKeyPressed())]) + "\n" 
    
    # Print the contents of the event
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime(), "-", self.GetDelayTime2())
        print("Key:", self.GetKeyLabel())
        print("Pressed:", self.GetKeyPressed())
    
class MouseEvent:
    
    delayTime = 0
    delayTime2 = 0
    button = None
    pressed = False
    position = (0, 0, 0, 0)
    
    # Initialize the mouse event with a delayTime, which button, whether it was pressed or released, and the position
    def __init__(self, delayTime, delayTime2, button, pressed, x, y, x2, y2):
        self.delayTime = delayTime
        self.delayTime2 = delayTime2
        self.button = button
        self.pressed = pressed
        self.position = (x, y, x2, y2)
        
    # Return the delay time
    def GetDelayTime(self):
        return self.delayTime
    
    def GetDelayTime2(self):
        return self.delayTime2
    
    def GetDelayRange(self):
        return self.delayTime2 - self.delayTime
    
    # Return which button
    def GetButton(self):
        return self.button
    
    # Return whether the button was pressed or released
    def GetButtonPressed(self):
        return self.pressed
    
    # Return the position of the event
    def GetPosition(self):
        return (self.position[0], self.position[1])
    
    def GetFullPosition(self):
        return self.position
    
    # Return the text label for the button
    def GetButtonLabel(self):
        return key_translation.buttonToText[self.button]
    
    def MouseMovement(self, x, allowance):
        if x == 0:
            return 0
        sigma = 3
        fraction = 1 / (1 + ((x / (1 - x)) ** (-1 * sigma)))
        return fraction * allowance
    
    # Given a virtual mouse, replay the mouse event
    def Playback(self, mouse):
        (startingX, startingY) = mouse.position
        fullPosition = self.GetFullPosition()
        if fullPosition[0] != fullPosition[2]:
            if self.GetButtonPressed():
                destinationX = random.randrange(fullPosition[0], fullPosition[2])
            else:
                destinationX = mouse.position[0]
        else:
            destinationX = fullPosition[0]
        if fullPosition[1] != fullPosition[3]:
            if self.GetButtonPressed():
                destinationY = random.randrange(fullPosition[1], fullPosition[3])
            else:
                destinationY = mouse.position[1]
        else:
            destinationY = fullPosition[1]
            
        totalDelay = self.GetDelayTime() + random.uniform(0, self.GetDelayRange())
        intDelay = (totalDelay) / movementFraction
        xDist = destinationX - startingX
        yDist = destinationY - startingY
        
        for interval in range(int(movementFraction)):
            time.sleep(intDelay)
            mouseX = startingX + self.MouseMovement(interval / movementFraction, xDist)
            mouseY = startingY + self.MouseMovement(interval / movementFraction, yDist)
            mouse.position = (mouseX, mouseY)
            
        mouse.position = (destinationX, destinationY)
        if self.GetButtonPressed():
            mouse.press(self.GetButton())
        else:
            mouse.release(self.GetButton())
            
    # Turn the event into text for saving to a file
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()) + "-" + str(self.GetDelayTime2()), self.GetButtonLabel(), str(self.GetButtonPressed()), " ".join(str(coord) for coord in self.GetFullPosition()) + "\n"])
    
    # Print the contents of the event
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime(), "-", self.GetDelayTime2())
        print("Button:", self.GetButtonLabel())
        print("Pressed:", self.GetButtonPressed())
        print("Position:", self.GetFullPosition())

class Dialog:
    
    # self.loadedRecording = macro.Recording
    # self.window = tkinter.TK
    # self.gridContainer = tkinter.Frame
    # self.gridCanvas = tkinter.Canvas
    # self.gridScrollbar = tkinter.Scrollbar
    # self.gridScrollableFrame = tkinter.Frame
    # self.recordingGrid = [][]tkinter.Entry
    # self.recordingGridLabels = []tkinter.Label
    # self.buttonFrame = tkinter.Frame
    # self.recordButton = tkinter.Button
    # self.playButton = tkinter.Button
    # self.saveButton = tkinter.Button
    # self.loadButton = tkinter.Button
    # self.clearButton = tkinter.Button
    
    # Initialize the dialog
    def __init__(self):
        
        # Initialize the loaded recording as an empty recording
        self.loadedRecording = Recording()
        
        # Create the main dialog window
        self.window = tkinter.Tk()
        self.window.title("Macro Recorder by Dan H. (hayned2)")
        
        # Create the grid to show the events of the recording
        self.recordingGrid = ttk.Treeview(self.window, columns = ("#", "Type", "Label", "Pressed", "Area", "Delay"), selectmode = "browse", height = 15)
        self.recordingGrid.column("#0", width = 0, stretch = tkinter.NO)
        self.recordingGrid.column("#1", width = 30, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#2", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#3", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#4", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#5", width = 120, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#6", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.heading("#1", text = "#", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#2", text = "Type", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#3", text = "Label", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#4", text = "Pressed", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#5", text = "Area", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#6", text = "Delay", anchor = tkinter.CENTER)
        
        # When a row in the grid is clicked, update the event info in the UI
        self.recordingGrid.bind("<ButtonRelease-1>", self.RowSelected)
        self.prevSelection = None
        
        self.recordingGrid.grid(column = 1, row = 0)      
        
        # Add a scrollbar for longer recordings
        self.recordingGridScrollbar = tkinter.Scrollbar(self.window, orient = "vertical", command = self.recordingGrid.yview)
        self.recordingGridScrollbar.configure(command = self.recordingGrid.yview)
        self.recordingGrid.configure(yscrollcommand = self.recordingGridScrollbar.set)
        self.recordingGridScrollbar.grid(column = 2, row = 0, sticky = "NSW")
        
        # Add a frame to hold the main buttons
        self.buttonFrame = tkinter.Frame(self.window, width = 500, height = 500)
        self.buttonFrame.grid(column = 0, row = 0)
        
        # Add the record button, which will begin a recording
        self.recordButton = tkinter.Button(self.buttonFrame, text = "Record", command = self.BeginRecording)
        self.recordButton.grid(column = 0, row = 0)
        
        # Add the playback button, which will replay the current recording
        self.playButton = tkinter.Button(self.buttonFrame, text = "Playback", command = self.PlaybackRecording)
        self.playButton.grid(column = 1, row = 0)
        
        # Add the loops field and label, which specifies how many times to playback the recording
        self.loopLabel = tkinter.Label(self.buttonFrame, text = "Loops")
        self.loopLabel.grid(column = 2, row = 0, columnspan = 1)
        self.loopEntry = tkinter.Entry(self.buttonFrame, width = 5)
        self.loopEntry.insert(0, "1")
        self.loopEntry.grid(column = 3, row = 0, columnspan = 2)
        
        # Start/Stop Hotkey Label
        self.hotkey = pynput.keyboard.Key.alt_gr
        self.hotkeyLabel = tkinter.Label(self.buttonFrame, text = "Stop", width = 7)
        self.hotkeyLabel.grid(column = 2, row = 1)
        self.hotkeyDisplay = tkinter.Label(self.buttonFrame, text = "alt_r", width = 10)
        self.hotkeyDisplay.grid(column = 3, row = 1)  
        
        # Change Hotkey Button
        self.changeHotkeyButton = tkinter.Button(self.buttonFrame, text = "Change", command = self.ChangeHotkey, width = 10)
        self.changeHotkeyButton.grid(column = 2, row = 2, columnspan = 2)
        
        # Add the save button, which will save the current recording to a text file
        self.saveButton = tkinter.Button(self.buttonFrame, text = "Save", command = self.SaveRecording)
        self.saveButton.grid(column = 0, row = 1)
        
        # Add the load button, which will read a text file into the loaded recording
        self.loadButton = tkinter.Button(self.buttonFrame, text = "Load", command = self.LoadRecording)
        self.loadButton.grid(column = 1, row = 1)
        
        # Add the clear button, which will clear the current recording
        self.clearButton = tkinter.Button(self.buttonFrame, text = "Clear", command = self.ClearRecording)
        self.clearButton.grid(column = 0, row = 2)
        
        # Add the event group box
        self.eventInfo = tkinter.LabelFrame(self.buttonFrame, text = "Event Info", padx = 5, pady = 5)
        self.eventInfo.grid(column = 0, row = 4, columnspan = 4)
        
        # Type
        self.selectedType = tkinter.StringVar(self.eventInfo)
        self.selectedType.set("Keyboard")
        self.eventTypeLabel = tkinter.Label(self.eventInfo, text = "Type", width = 10)
        self.eventTypeLabel.grid(column = 0, row = 0)
        self.eventTypeBox = tkinter.OptionMenu(self.eventInfo, self.selectedType, "Keyboard", "Mouse", command = self.ShowHidePosition)
        self.eventTypeBox.grid(column = 1, row = 0, columnspan = 4)
        
        # Label
        self.labelLabel = tkinter.Label(self.eventInfo, text = "Label", width = 10)
        self.labelLabel.grid(column = 0, row = 1)
        self.selectLabel = tkinter.Label(self.eventInfo, text = "None", width = 10)
        self.selectLabel.grid(column = 1, row = 1, columnspan = 4)
        
        # Position
        self.positionLabel = tkinter.Label(self.eventInfo, text = "Position")
        self.xLabel = tkinter.Label(self.eventInfo, text = "X1")
        self.xEntry = tkinter.Entry(self.eventInfo, width = 5)
        self.yLabel = tkinter.Label(self.eventInfo, text = "Y1")
        self.yEntry = tkinter.Entry(self.eventInfo, width = 5)
        self.x2Label = tkinter.Label(self.eventInfo, text = "X2")
        self.x2Entry = tkinter.Entry(self.eventInfo, width = 5)
        self.y2Label = tkinter.Label(self.eventInfo, text = "Y2")
        self.y2Entry = tkinter.Entry(self.eventInfo, width = 5) 
          
        # Change
        self.selectButton = tkinter.Button(self.eventInfo, text = "Change", command = self.ChangeSelectLabel, width = 10)
        self.selectButton.grid(column = 0, row = 4, columnspan = 2)
        self.selectButton2 = tkinter.Button(self.eventInfo, text = "Change X2/Y2", command = self.ChangeX2Y2, width = 15)
        self.selectButton2.grid(column = 2, row = 4, columnspan = 3)
        
        self.ShowHidePosition()    
        
        # Pressed
        self.pressedValue = tkinter.BooleanVar(self.eventInfo)
        self.pressedLabel = tkinter.Label(self.eventInfo, text = "Pressed", width = 10)
        self.pressedLabel.grid(column = 0, row = 5)
        self.pressedBox = tkinter.Checkbutton(self.eventInfo, variable = self.pressedValue)
        self.pressedBox.grid(column = 1, row = 5, columnspan = 4)
        
        # Delay
        self.delayLabel = tkinter.Label(self.eventInfo, text = "Delay")
        self.delayLabel.grid(column = 0, row = 6)
        self.delayEntry = tkinter.Entry(self.eventInfo, width = 8)
        self.delayEntry.grid(column = 1, row = 6, columnspan = 1)
        self.dashLabel = tkinter.Label(self.eventInfo, text = "-")
        self.dashLabel.grid(column = 2, row = 6)
        self.delayEntry2 = tkinter.Entry(self.eventInfo, width = 8)
        self.delayEntry2.grid(column = 3, row = 6, columnspan = 2)
        
        # Add the add row button, which will add an additional row to the current recording grid
        self.addRowButton = tkinter.Button(self.eventInfo, text = "Add Row", command = self.AddRow)
        self.addRowButton.grid(column = 0, row = 10)
        
        # Add the update row button, which will update the selected row with the event info
        self.updateRowButton = tkinter.Button(self.eventInfo, text = "Update", command = self.UpdateRow)
        self.updateRowButton.grid(column = 1, row = 10)
        
        # Add the delete row button, which will delete the selected row
        self.deleteRowButton = tkinter.Button(self.eventInfo, text = "Delete", command = self.DeleteRow)
        self.deleteRowButton.grid(column = 2, row = 10)
        
        # Add the up and down buttons, which will let you move a row up and down the list
        self.upButton = tkinter.Button(self.eventInfo, text = "\u2191", command = self.MoveRowUp)
        self.downButton = tkinter.Button(self.eventInfo, text = "\u2193", command = self.MoveRowDown)
        self.upButton.grid(column = 3, row = 10)
        self.downButton.grid(column = 4, row = 10)

    # Records mouse and keyboard clicks into the recording object
    def BeginRecording(self):
        print("Beginning recording, press the hotkey to stop")
        self.loadedRecording.ClearRecording()
        self.window.focus()
        self.window.iconify()
        pressedMouse = []
        pressedKeys = []
        
        # Function for tracking a keyboard button press
        def on_press(key):
            nonlocal pressedKeys
            if key in pressedKeys:
                return True
            pressedKeys.append(key)
            return RegisterKeystroke(key, True)
            
        # Function for tracking a keyboard button release
        def on_release(key):
            nonlocal pressedKeys
            if key not in pressedKeys:
                return True
            pressedKeys.remove(key)
            return RegisterKeystroke(key, False)
            
        # Function for recording a keyboard event
        def RegisterKeystroke(key, pressed):
            if key == self.hotkey:
                return False
            self.loadedRecording.AddKeyboardEvent(key, pressed)
            return True
        
        # Function for recording a mouse button click
        def on_click(x, y, button, pressed):
            nonlocal pressedMouse
            if pressed:
                if button not in pressedMouse:
                    pressedMouse.append(button)
                else:
                    return True
            else:
                if button in pressedMouse:
                    pressedMouse.remove(button)
                else:
                    return True
            self.loadedRecording.AddMouseEvent(button, pressed, x, y)
              
        
        # Begins the recording here, stops when on_click or on_press returns False
        with pynput.mouse.Listener(on_click = on_click) as listener:
            with pynput.keyboard.Listener(on_press = on_press, on_release = on_release) as listener:
                listener.join()
                
        self.window.deiconify()
        self.RecordingToGrid()
                
        print("Recording has been completed")
      
    # Begin playback of the current recording  
    def PlaybackRecording(self):
        
        self.GridToRecording()
        self.window.focus()
        
        # Figure out how many times to loop through the recording, defaulting to 1
        if self.loopEntry.get() == "":
            loops = 1
            self.loopEntry.delete(0, "end")
            self.loopEntry.insert(0, 1)
        else:
            try:
                loops = int(self.loopEntry.get())
            except:
                tkinter.messagebox.showinfo("Error", "Loops must be a non-negative integer")
                return
        self.window.iconify()
        print("Beginning playback of current recording", loops, "time(s)")
        for x in range(loops):
            self.loadedRecording.Playback(self.hotkey)
        print("Finished playback of current recording")
        self.window.deiconify()

    # Save the current recording to a text file
    def SaveRecording(self):
        self.GridToRecording()
        if len(self.loadedRecording.GetEvents()) == 0:
            print("Nothing to save")
            return
        filename = filedialog.asksaveasfilename(filetypes = [("MacroRecorder files", "*" + fileExtension)])
        if not filename.endswith(fileExtension):
            filename += fileExtension
        file = open(filename, "w")
        for event in self.loadedRecording.GetEvents():
            file.write(event.GetFileText())
        file.close()
        print("Finished saving recording", filename)

    # Read a text file into the current recording
    def LoadRecording(self):
        filename = filedialog.askopenfilename(filetypes = [("MacroRecorder files", "*" + fileExtension)])
        if filename == "":
            return
        self.loadedRecording.ClearRecording()
        file = open(filename, "r")
        readEvents = file.readlines()
        for event in readEvents:
            self.loadedRecording.AddEventFromText(event)
        file.close()
        self.RecordingToGrid()
        print("Successfully loaded recording", filename)
        
    #
    def ChangeHotkey(self):
        self.hotkeyDisplay.configure(text = "Listening...")
        self.window.focus()
        def on_press(key):
            if type(key) == pynput.keyboard.Key:
                self.hotkeyDisplay.configure(text = key_translation.keyToText[key])
            else:
                if key.vk >= 96 and key.vk <= 111:
                    self.hotkeyDisplay.configure(text = key_translation.charFromVK[key.vk])
                else:
                    self.hotkeyDisplay.configure(text = key.char)
            self.hotkey = key
            return False
        listener = pynput.keyboard.Listener(on_press = on_press)
        listener.start()
        
    # Record the next mouse / keyboard event when the user wants to edit an event
    def ChangeSelectLabel(self):
        self.selectLabel.configure(text = "Listening...")
        self.window.focus()
        if self.selectedType.get() == "Keyboard":
            def on_press(key):
                if type(key) == pynput.keyboard.Key:
                    self.selectLabel.configure(text = key_translation.keyToText[key])
                else:
                    if key.vk >= 96 and key.vk <= 111:
                        self.selectLabel.configure(text = key_translation.charFromVK[key.vk])
                    else:
                        self.selectLabel.configure(text = key.char)
                return False
            listener = pynput.keyboard.Listener(on_press = on_press)
            listener.start()
        else:
            def on_click(x, y, button, pressed):
                if pressed == False:
                    self.selectLabel.configure(text = key_translation.buttonToText[button])
                    self.xEntry.delete(0, "end")
                    self.yEntry.delete(0, "end")
                    self.xEntry.insert(0, x)
                    self.yEntry.insert(0, y)
                    self.x2Entry.delete(0, "end")
                    self.y2Entry.delete(0, "end")
                    self.x2Entry.insert(0, x)
                    self.y2Entry.insert(0, y)
                    return False
            listener = pynput.mouse.Listener(on_click = on_click)
            listener.start()
            
            
    def ChangeX2Y2(self):
        self.window.focus()
        def on_click(x, y, button, pressed):
            if pressed == False:
                self.x2Entry.delete(0, "end")
                self.y2Entry.delete(0, "end")
                self.x2Entry.insert(0, x)
                self.y2Entry.insert(0, y)
                return False
        listener = pynput.mouse.Listener(on_click = on_click)
        listener.start()
        
    # Show or hide the mouse position row depending on the selected event type
    def ShowHidePosition(self, newType = None):
        if newType == None:
            newType = self.selectedType.get()
        if newType == "Keyboard":
            self.positionLabel.grid_forget()
            self.xLabel.grid_forget()
            self.xEntry.grid_forget()
            self.yLabel.grid_forget()
            self.yEntry.grid_forget()
            self.x2Label.grid_forget()
            self.x2Entry.grid_forget()
            self.y2Label.grid_forget()
            self.y2Entry.grid_forget()
            self.selectButton.grid(column = 0, row = 4, columnspan = 5)
            self.selectButton2.grid_forget()
        else:
            self.positionLabel.grid(column = 0, row = 2)
            self.xLabel.grid(column = 1, row = 2)
            self.xEntry.grid(column = 2, row = 2)
            self.yLabel.grid(column = 3, row = 2)
            self.yEntry.grid(column = 4, row = 2)
            self.x2Label.grid(column = 1, row = 3)
            self.x2Entry.grid(column = 2, row = 3)
            self.y2Label.grid(column = 3, row = 3)
            self.y2Entry.grid(column = 4, row = 3)
            self.selectButton.grid(column = 0, row = 4, columnspan = 2)
            self.selectButton2.grid(column = 2, row = 4, columnspan = 3)
        self.selectLabel.configure(text = "None")
    
    #
    def RowSelected(self, event):
        if len(self.recordingGrid.selection()) == 0:
            self.prevSelection = None
            return
        [index, inputType, label, pressedData, position, delay] = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"]
        if index == self.prevSelection:
            self.recordingGrid.selection_remove(self.recordingGrid.selection()[0])
            self.prevSelection = None
            return
        self.prevSelection = index
        if self.selectedType.get() != inputType:
            self.selectedType.set(inputType)
            self.ShowHidePosition()
        self.selectLabel.configure(text = label)
        [delayTime, delayTime2] = delay.split("-")
        self.delayEntry.delete(0, "end")
        self.delayEntry.insert(0, delayTime)
        self.delayEntry2.delete(0, "end")
        self.delayEntry2.insert(0, delayTime2)
        self.pressedValue.set(True if pressedData == "True" else False)
        if inputType == "Mouse":
            position = literal_eval(position)
            self.xEntry.delete(0, "end")
            self.yEntry.delete(0, "end")
            self.x2Entry.delete(0, "end")
            self.y2Entry.delete(0, "end")
            self.xEntry.insert(0, position[0])
            self.yEntry.insert(0, position[1])
            self.x2Entry.insert(0, position[2])
            self.y2Entry.insert(0, position[3])
    
    # Add another row without modifying the rest of the recording grid
    def AddRow(self, info = None):
        if info == None:
            iType = self.selectedType.get()
            iLabel = self.selectLabel["text"]
            iPressed = "True" if self.pressedValue.get() else "False"
            if iType == "Mouse":
                iPosition = str((int(self.xEntry.get()), int(self.yEntry.get()), int(self.x2Entry.get()), int(self.y2Entry.get())))
            else:
                iPosition = "N/A"
            if self.delayEntry2.get() == "":
                self.delayEntry2.insert(0, self.delayEntry.get())
            iDelay = self.delayEntry.get() + "-" + self.delayEntry2.get()
        else:
            (iType, iLabel, iPressed, iPosition, iDelay) = info
        numRows = len(self.recordingGrid.get_children())
        
        # Make sure all the fields are valid
        if iType != "Keyboard" and iType != "Mouse":
            tkinter.messagebox.showinfo("Error", "Type must be 'keyboard' or 'mouse'")
            return
        error = False
        try:
            [delayTime, delayTime2] = [float(t) for t in iDelay.split("-")]
            if delayTime < 0 or delayTime2 < 0:
                error = True
        except:
            error = True
        if error:
            tkinter.messagebox.showinfo("Error", "Delay must be a non-negative number")
            return
        if iLabel == "None":
            tkinter.messagebox.showinfo("Error", "Make sure a label has been selected")
            return
        
        self.recordingGrid.insert("", "end", text = "", values = (numRows, iType, iLabel, iPressed, iPosition, iDelay), tags = ("odd" if numRows % 2 == 0 else "even",))
        self.recordingGrid.tag_configure("odd", background = "#E8E8E8")
        self.recordingGrid.tag_configure("even", background = "#DFDFDF")
        
    def UpdateRow(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be updated")
            return
        newNum = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"][0]
        newType = self.selectedType.get()
        newLabel = self.selectLabel["text"]
        newPressed = "True" if self.pressedValue.get() else "False"
        if newType == "Mouse":
            newPosition = str((int(self.xEntry.get()), int(self.yEntry.get()), int(self.x2Entry.get()), int(self.y2Entry.get())))
        else:
            newPosition = "N/A"
        if self.delayEntry2.get() == "":
            self.delayEntry2.insert(0, self.delayEntry.get())
        newDelay = self.delayEntry.get() + "-" + self.delayEntry2.get()     
        self.recordingGrid.item(self.recordingGrid.selection()[0], values = (newNum, newType, newLabel, newPressed, newPosition, newDelay))
        
    def DeleteRow(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be deleted")
            return
        deletedNum = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"][0]
        for row in self.recordingGrid.get_children():
            values = self.recordingGrid.item(row)["values"]
            if values[0] > deletedNum:
                self.recordingGrid.item(row, values = (values[0] - 1, values[1], values[2], values[3], values[4], values[5]))
        self.recordingGrid.delete(self.recordingGrid.selection()[0])
        
    def MoveRowUp(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be moved")
            return
        row = self.recordingGrid.selection()[0]
        rowValues = self.recordingGrid.item(row)["values"]
        rowValues[0] -= 1
        prevRow = self.recordingGrid.prev(row)
        if prevRow == "":
            return
        prevRowValues = self.recordingGrid.item(prevRow)["values"]
        prevRowValues[0] += 1
        self.recordingGrid.item(row, values = rowValues)
        self.recordingGrid.item(prevRow, values = prevRowValues)
        self.recordingGrid.move(row, self.recordingGrid.parent(row), self.recordingGrid.index(row) - 1)
    
    def MoveRowDown(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be moved")
            return
        row = self.recordingGrid.selection()[0]
        rowValues = self.recordingGrid.item(row)["values"]
        rowValues[0] += 1
        nextRow = self.recordingGrid.next(row)
        if nextRow == "":
            return
        nextRowValues = self.recordingGrid.item(nextRow)["values"]
        nextRowValues[0] -= 1
        self.recordingGrid.item(row, values = rowValues)
        self.recordingGrid.item(nextRow, values = nextRowValues)
        self.recordingGrid.move(row, self.recordingGrid.parent(row), self.recordingGrid.index(row) + 1)        
    
    # Populate the recording grid in the UI with the loaded recording's events
    def RecordingToGrid(self):
        self.ClearRecording()
        for x in range(len(self.loadedRecording.GetEvents())):
            event = self.loadedRecording.GetEvent(x)
            if type(event) == KeyboardEvent:
                self.AddRow(("Keyboard", event.GetKeyLabel(), "True" if event.GetKeyPressed() else "False", "N/A", str(round(event.GetDelayTime(), 5)) + "-" + str(round(event.GetDelayTime2(), 5))))
            else:
                self.AddRow(("Mouse", event.GetButtonLabel(), "True" if event.GetButtonPressed() else "False", str(event.GetFullPosition()), str(round(event.GetDelayTime(), 5)) + "-" + str(round(event.GetDelayTime2(), 5))))
        self.recordingGrid.tag_configure("odd", background = "#E8E8E8")
        self.recordingGrid.tag_configure("even", background = "#DFDFDF")
        
    def GridToRecording(self):
        self.loadedRecording.ClearRecording()
        for row in self.recordingGrid.get_children():
            self.loadedRecording.AddEventFromGrid(self.recordingGrid.item(row)["values"])

    # Clear the current recording
    def ClearRecording(self):
        for row in self.recordingGrid.get_children():
            self.recordingGrid.delete(row)

if __name__ == "__main__":
    
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    
    dialog = Dialog()
    dialog.window.mainloop()
    
    exit(0)

