import ctypes
import time
import os
import pynput
import tkinter
from tkinter import ttk
from tkinter import filedialog

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
        
        # Create the frame that will hold the grid displaying the recording
        self.gridContainer = tkinter.Frame(self.window)
        self.gridCanvas = tkinter.Canvas(self.gridContainer, width = 500)
        self.gridScrollbar = tkinter.Scrollbar(self.gridContainer, orient = "vertical", command = self.gridCanvas.yview)
        self.gridScrollableFrame = tkinter.Frame(self.gridCanvas)
        self.gridScrollableFrame.bind("<Configure>", lambda e: self.gridCanvas.configure(scrollregion = self.gridCanvas.bbox("all")))
        self.gridCanvas.create_window((0, 0), window = self.gridScrollableFrame, anchor = "nw")
        self.gridCanvas.configure(yscrollcommand = self.gridScrollbar.set)
        
        # Create the grid to display the recording
        self.recordingGrid = []
        gridLabels = ["Type", "Label", "Pressed", "Delay"]
        self.recordingGridLabels = []
        for x in range(len(gridLabels)):
            tkLabel = tkinter.Label(self.gridScrollableFrame, text = gridLabels[x])
            tkLabel.grid(column = x, row = 0)
            self.recordingGridLabels.append(tkLabel)
        
        # Initialize the grid with one empty row
        self.ResizeGrid(1)
        
        self.gridContainer.grid(column = 0, row = 0)
        self.gridCanvas.pack(side = "left", fill = "both", expand = True)
        self.gridScrollbar.pack(side = "right", fill = "y")
        
        # Update the window so the other objects are aware of the grid's shape
        self.window.update()
        
        # Add a frame to hold the main buttons
        self.buttonFrame = tkinter.Frame(self.window, width = self.gridContainer.winfo_width(), height = self.gridContainer.winfo_height())
        self.buttonFrame.grid(column = 1, row = 0)      
        
        # Add the record button, which will begin a recording
        self.recordButton = tkinter.Button(self.buttonFrame, text = "Record", command = self.BeginRecording)
        self.recordButton.grid(column = 0, row = 0)
        
        # Add the playback button, which will replay the current recording
        self.playButton = tkinter.Button(self.buttonFrame, text = "Playback", command = self.PlaybackRecording)
        self.playButton.grid(column = 1, row = 0)
        
        # Add the save button, which will save the current recording to a text file
        self.saveButton = tkinter.Button(self.buttonFrame, text = "Save", command = self.SaveRecording)
        self.saveButton.grid(column = 0, row = 1)
        
        # Add the load button, which will read a text file into the loaded recording
        self.loadButton = tkinter.Button(self.buttonFrame, text = "Load", command = self.LoadRecording)
        self.loadButton.grid(column = 1, row = 1)
        
        # Add the clear button, which will clear the current recording
        self.clearButton = tkinter.Button(self.buttonFrame, text = "Clear", command = self.ClearRecording)
        self.clearButton.grid(column = 0, row = 2)
        
        # Add the add row button, which will add an additional row to the current recording grid
        self.addRowButton = tkinter.Button(self.buttonFrame, text = "Add Row", command = self.AddRow)
        self.addRowButton.grid(column = 1, row = 2)

    # Records mouse and keyboard clicks into the recording object
    def BeginRecording(self):
        print("Beginning recording, press 'q' to stop")
        self.loadedRecording.ClearRecording()
        
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
        print("Beginning playback of current recording")
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
    
    # Replace the text of a tkinter.Entry (field) with new (text)
    def ReplaceText(self, field, text):
        field.delete(0, tkinter.END)
        field.insert(0, text)
    
    # Resize the recording grid to the correct number of rows
    def ResizeGrid(self, rows):
        for row in self.recordingGrid:
            for cell in row:
                cell.destroy()
        self.recordingGrid.clear()
        for row in range(rows):
            recordingRow = []
            for column in range(4):
                text = tkinter.Entry(self.gridScrollableFrame, width = 20, state = "normal")
                text.grid(column = column, row = row + 1)
                recordingRow.append(text)
            self.recordingGrid.append(recordingRow)
    
    # Add another row without modifying the rest of the recording grid
    def AddRow(self):
        row = []
        for column in range(4):
            text = tkinter.Entry(self.gridScrollableFrame, width = 20, state = "normal")
            text.grid(column = column, row = len(self.recordingGrid) + 1)
            row.append(text)
        self.recordingGrid.append(row)
    
    # Populate the recording grid in the UI with the loaded recording's events
    def RecordingToGrid(self):
        self.ResizeGrid(len(self.loadedRecording.GetEvents()))
        for x in range(len(self.loadedRecording.GetEvents())):
            event = self.loadedRecording.GetEvent(x)
            row = self.recordingGrid[x]
            if type(event) == KeyboardEvent:
                self.ReplaceText(row[0], "Keyboard")
                self.ReplaceText(row[1], event.GetKeyLabel())
                self.ReplaceText(row[2], "Down" if event.GetKeyPressed() else "Up")
                self.ReplaceText(row[3], event.GetDelayTime())
            else:
                self.ReplaceText(row[0], "Mouse")
                self.ReplaceText(row[1], event.GetButtonLabel())
                self.ReplaceText(row[2], ("Down " if event.GetButtonPressed() else "Up ") + str(event.GetPosition()))
                self.ReplaceText(row[3], event.GetDelayTime()) 
    # Clear the current recording
    def ClearRecording(self):
        self.loadedRecording.ClearRecording()
        self.ResizeGrid(1)


if __name__ == "__main__":
    
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    
    dialog = Dialog()
    dialog.window.mainloop()
    
    exit(0)

