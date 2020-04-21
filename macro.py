import ctypes
import time
import os
import pynput
import tkinter
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import key_translation

PROCESS_PER_MONITOR_DPI_AWARE = 2
movementFraction = 100.0
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
        if len(parameters) == 5:
            self.AddMouseEventFromText(parameters)
        else:
            self.AddKeyboardEventFromText(parameters)    
    
    # Used when adding a keyboard event. delayTime is only provided if adding from text
    def AddKeyboardEvent(self, key, pressed, delayTime = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
        self.lastEventTime = eventTime
        event = KeyboardEvent(delayTime, key, pressed)
        self.events.append(event)
    
    # Used when adding a keyboard event from text
    def AddKeyboardEventFromText(self, params):
        [delay, key, pressed] = params
        delay = float(delay)
        key = key_translation.textToKey[key] if key in key_translation.textToKey else pynput.keyboard.KeyCode.from_char(key)
        pressed = True if pressed == "True" else False
        self.AddKeyboardEvent(key, pressed, delay)
        
    # Used when adding a mouse event. delayTime is only provided if adding from text
    def AddMouseEvent(self, button, pressed, x, y, delayTime = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
        self.lastEventTime = eventTime
        event = MouseEvent(delayTime, button, pressed, x, y)
        self.events.append(event)
        
    # Used when adding a keyboard event from text
    def AddMouseEventFromText(self, params):
        [delay, button, pressed, x, y] = params
        delay = float(delay)
        button = key_translation.textToButton[button]
        pressed = True if pressed == "True" else False
        x = int(x)
        y = int(y)
        self.AddMouseEvent(button, pressed, x, y, delay)
      
    # Return the list of events  
    def GetEvents(self):
        return self.events
    
    # Return a specific event
    def GetEvent(self, which):
        return self.events[which]
    
    # Emulate the mouse and keyboard to recreate the recorded events
    def Playback(self):
        pressedKeys = []
        pressedMouse = []
        keyboard = pynput.keyboard.Controller()
        mouse = pynput.mouse.Controller()
        for event in self.GetEvents():
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
                    
        # Make sure that the mouse and keyboard doesn't leave anything held down
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
    key = None
    pressed = False
    
    # Initialize the keyboard event with a delayTime, which key, and whether it was pressed or released
    def __init__(self, delayTime, key, pressed):
        self.delayTime = delayTime
        self.key = key
        self.pressed = pressed
        
    # Return the delayTime
    def GetDelayTime(self):
        return self.delayTime
    
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
        time.sleep(self.GetDelayTime())
        if self.GetKeyPressed():
            keyboard.press(self.GetKey())
        else:
            keyboard.release(self.GetKey())
           
    # Turn the event into text for saving to a file 
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()), self.GetKeyLabel(), str(self.GetKeyPressed())]) + "\n" 
    
    # Print the contents of the event
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime())
        print("Key:", self.GetKeyLabel())
        print("Pressed:", self.GetKeyPressed())
    
class MouseEvent:
    
    delayTime = 0
    button = None
    pressed = False
    position = (0, 0)
    
    # Initialize the mouse event with a delayTime, which button, whether it was pressed or released, and the position
    def __init__(self, delayTime, button, pressed, x, y):
        self.delayTime = delayTime
        self.button = button
        self.pressed = pressed
        self.position = (x, y)
        
    # Return the delay time
    def GetDelayTime(self):
        return self.delayTime
    
    # Return which button
    def GetButton(self):
        return self.button
    
    # Return whether the button was pressed or released
    def GetButtonPressed(self):
        return self.pressed
    
    # Return the position of the event
    def GetPosition(self):
        return self.position
    
    # Return the text label for the button
    def GetButtonLabel(self):
        return key_translation.buttonToText[self.button]
    
    # Given a virtual mouse, replay the mouse event
    def Playback(self, mouse):
        (startingX, startingY) = mouse.position
        dx = (self.GetPosition()[0] - startingX) / movementFraction
        dy = (self.GetPosition()[1] - startingY) / movementFraction
        intDelay = self.GetDelayTime() / movementFraction

        for interval in range(int(movementFraction)):
            time.sleep(intDelay)
            mouse.position = (startingX + (dx * interval), startingY + (dy * interval))
        mouse.position = self.GetPosition()
        if self.GetButtonPressed():
            mouse.press(self.GetButton())
        else:
            mouse.release(self.GetButton())
            
    # Turn the event into text for saving to a file
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()), self.GetButtonLabel(), str(self.GetButtonPressed()), str(self.GetPosition()[0]), str(self.GetPosition()[1])]) + "\n"
    
    # Print the contents of the event
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime())
        print("Button:", self.GetButtonLabel())
        print("Pressed:", self.GetButtonPressed())
        print("Position:", self.GetPosition())

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
        self.window.title("Do not believe everything you see when you're talking to me, Scam Likely~~")
        
        self.recordingGrid = ttk.Treeview(self.window, columns = ("#", "Type", "Label", "Pressed", "Delay"), selectmode = "browse", height = 12)
        self.recordingGrid.column("#0", width = 0, stretch = tkinter.NO)
        self.recordingGrid.column("#1", width = 30, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#2", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#3", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#4", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        self.recordingGrid.column("#5", width = 100, stretch = tkinter.NO, anchor = tkinter.CENTER)
        
        self.recordingGrid.heading("#1", text = "#", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#2", text = "Type", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#3", text = "Label", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#4", text = "Pressed", anchor = tkinter.CENTER)
        self.recordingGrid.heading("#5", text = "Delay", anchor = tkinter.CENTER)
        
        self.recordingGrid.bind("<ButtonRelease-1>", self.RowSelected)
        self.prevSelection = None
        
        self.recordingGrid.grid(column = 1, row = 0)      
        
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
        self.loopLabel.grid(column = 2, row = 0)
        self.loopEntry = tkinter.Entry(self.buttonFrame, width = 5)
        self.loopEntry.insert(0, "1")
        self.loopEntry.grid(column = 3, row = 0)
        
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
        self.eventInfo.grid(column = 0, row = 3, columnspan = 4)
        
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
        self.xLabel = tkinter.Label(self.eventInfo, text = "X")
        self.xEntry = tkinter.Entry(self.eventInfo, width = 5)
        self.yLabel = tkinter.Label(self.eventInfo, text = "Y")
        self.yEntry = tkinter.Entry(self.eventInfo, width = 5)
        self.ShowHidePosition(self.selectedType.get())        
        
        # Change
        self.selectButton = tkinter.Button(self.eventInfo, text = "Change", command = self.ChangeSelectLabel, width = 10)
        self.selectButton.grid(column = 0, row = 3, columnspan = 5)
        
        # Pressed
        self.pressedValue = tkinter.BooleanVar(self.eventInfo)
        self.pressedLabel = tkinter.Label(self.eventInfo, text = "Pressed", width = 10)
        self.pressedLabel.grid(column = 0, row = 4)
        self.pressedBox = tkinter.Checkbutton(self.eventInfo, variable = self.pressedValue)
        self.pressedBox.grid(column = 1, row = 4, columnspan = 4)
        
        # Delay
        self.delayLabel = tkinter.Label(self.eventInfo, text = "Delay")
        self.delayLabel.grid(column = 0, row = 5)
        self.delayEntry = tkinter.Entry(self.eventInfo, width = 16)
        self.delayEntry.grid(column = 1, row = 5, columnspan = 4)
        
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
        print("Beginning recording, press 'q' to stop")
        self.loadedRecording.ClearRecording()
        self.window.focus()
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
            if type(key) == pynput.keyboard.KeyCode and key.char == 'q':
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
                
        self.RecordingToGrid()
                
        print("Recording has been completed")
      
    # Begin playback of the current recording  
    def PlaybackRecording(self):
        self.window.focus()
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
        
        print("Beginning playback of current recording", loops, "time(s)")
        for x in range(loops):
            self.loadedRecording.Playback()
        print("Finished playback of current recording")

    # Save the current recording to a text file
    def SaveRecording(self):
        if len(self.loadedRecording.GetEvents()) == 0:
            print("Nothing to save")
            return
        filename = filedialog.asksaveasfilename(filetypes = [("MacroRecorder files", "*" + fileExtension)])
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
                    return False
            listener = pynput.mouse.Listener(on_click = on_click)
            listener.start()
        
    # Show or hide the mouse position row depending on the selected event type
    def ShowHidePosition(self, newType):
        if newType == "Keyboard":
            self.positionLabel.grid_forget()
            self.xLabel.grid_forget()
            self.xEntry.grid_forget()
            self.yLabel.grid_forget()
            self.yEntry.grid_forget()
        else:
            self.positionLabel.grid(column = 0, row = 2)
            self.xLabel.grid(column = 1, row = 2)
            self.xEntry.grid(column = 2, row = 2)
            self.yLabel.grid(column = 3, row = 2)
            self.yEntry.grid(column = 4, row = 2)
        self.selectLabel.configure(text = "None")
    
    #
    def RowSelected(self, event):
        if len(self.recordingGrid.selection()) == 0:
            self.prevSelection = None
            return
        [index, inputType, label, pressedData, delay] = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"]
        if index == self.prevSelection:
            self.recordingGrid.selection_remove(self.recordingGrid.selection()[0])
            self.prevSelection = None
            return
        self.prevSelection = index
        if self.selectedType.get() != inputType:
            self.selectedType.set(inputType)
            self.ShowHidePosition(inputType)
        self.selectLabel.configure(text = label)
        self.delayEntry.delete(0, "end")
        self.delayEntry.insert(0, delay)
        if inputType == "Mouse":
            pressedData = pressedData.split(" ")
            self.pressedValue.set(True if pressedData[0] == "Down" else False)
            self.xEntry.delete(0, "end")
            self.yEntry.delete(0, "end")
            self.xEntry.insert(0, pressedData[1].replace("(", "").replace(",", ""))
            self.yEntry.insert(0, pressedData[2].replace(")", ""))
        else:
            self.pressedValue.set(True if pressedData == "Down" else False)
        
    
    # Add another row without modifying the rest of the recording grid
    def AddRow(self, info = None):
        if info == None:
            iType = self.selectedType.get()
            iLabel = self.selectLabel["text"]
            iPressed = "Down" if self.pressedValue.get() else "Up"
            if iType == "Mouse":
                iPressed = iPressed + " " + str((int(self.xEntry.get()), int(self.yEntry.get())))
            iDelay = self.delayEntry.get()
        else:
            (iType, iLabel, iPressed, iDelay) = info
        numRows = len(self.recordingGrid.get_children())
        
        # Make sure all the fields are valid
        if iType != "Keyboard" and iType != "Mouse":
            tkinter.messagebox.showinfo("Error", "Type must be 'keyboard' or 'mouse'")
            return
        error = False
        try:
            iDelay = float(iDelay)
            if iDelay < 0:
                error = True
        except:
            error = True
        if error:
            tkinter.messagebox.showinfo("Error", "Delay must be a non-negative number")
            return
        if iLabel == "None":
            tkinter.messagebox.showinfo("Error", "Make sure a label has been selected")
            return
        
        self.recordingGrid.insert("", "end", text = "", values = (numRows, iType, iLabel, iPressed, iDelay), tags = ("odd" if numRows % 2 == 0 else "even",))
        self.recordingGrid.tag_configure("odd", background = "#E8E8E8")
        self.recordingGrid.tag_configure("even", background = "#DFDFDF")
        
    def UpdateRow(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be updated")
            return
        newNum = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"][0]
        newType = self.selectedType.get()
        newLabel = self.selectLabel["text"]
        newPressed = "Down" if self.pressedValue.get() else "Up"
        if newType == "Mouse":
            newPressed = newPressed + " " + str((int(self.xEntry.get()), int(self.yEntry.get())))
        newDelay = self.delayEntry.get()        
        self.recordingGrid.item(self.recordingGrid.selection()[0], values = (newNum, newType, newLabel, newPressed, newDelay))
        
    def DeleteRow(self):
        if len(self.recordingGrid.selection()) == 0:
            tkinter.messagebox.showinfo("Error", "No row is selected to be deleted")
            return
        deletedNum = self.recordingGrid.item(self.recordingGrid.selection()[0])["values"][0]
        for row in self.recordingGrid.get_children():
            values = self.recordingGrid.item(row)["values"]
            if values[0] > deletedNum:
                self.recordingGrid.item(row, values = (values[0] - 1, values[1], values[2], values[3], values[4]))
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
                self.AddRow(("Keyboard", event.GetKeyLabel(), "Down" if event.GetKeyPressed() else "Up", round(event.GetDelayTime(), 5)))
            else:
                self.AddRow(("Mouse", event.GetButtonLabel(), ("Down " if event.GetButtonPressed() else "Up ") + str(event.GetPosition()), round(event.GetDelayTime(), 5)))
        self.recordingGrid.tag_configure("odd", background = "#E8E8E8")
        self.recordingGrid.tag_configure("even", background = "#DFDFDF")
    
    # Clear the current recording
    def ClearRecording(self):
        for row in self.recordingGrid.get_children():
            self.recordingGrid.delete(row)


if __name__ == "__main__":
    
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    
    dialog = Dialog()
    dialog.window.mainloop()
    
    exit(0)

