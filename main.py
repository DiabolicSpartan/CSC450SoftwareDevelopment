#import packages
import cv2
import time
from datetime import datetime
import imutils
from imutils.video import VideoStream
import sys
import argparse
import ctypes

#Globals
startAlertTimer = 0
defaultTimer = 10
currentAlertTimer = defaultTimer
alertTimerThreshold = defaultTimer
statusText = "No movement detected."
previousStatusText = "NULL"
prevprevStatusText = "Null"
alertSent = False
fallDetected = False
personInFrame = False

#This function inizilizes the program
def initializeProgram():
    try:
        createLogFile()
        ap = argparse.ArgumentParser()
        ap.add_argument("-a", "--min-area", type=int, default=4000, help="minimum area size")
        args = vars(ap.parse_args())
        firstFrame= None
        capture = startCapture()
        writeToLog("Program fully initilized!")
        frameWidth = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return args, firstFrame, capture, frameWidth, frameHeight
    except:
        writeToLog("ERROR: Initilization failed!")
        sys.exit()

#This function trys to create a log file
def createLogFile():
    try:
        logFile = open("Test_Event_Log.txt", "a+")
        logFile.write("********************New Initialization********************\n\n")
        logFile.close()
        writeToLog("Event Log Initialized!")
    except:
        print("Log File failed to generate. Terminating program...")
        sys.exit()

#This function is called when an event is needed to be written to a log
def writeToLog(strEvent):
    logFile = open("Test_Event_Log.txt", "a+")
    logFile.write("["+getTimeStamp()+"] - "+strEvent+"\n")
    logFile.close()

#This function acquires a timestamp
def getTimeStamp():
    now = datetime.now()
    now = now.strftime("%d%b%Y %H%M%S")
    return now

#This function trys to initialized the camera feed
def startCapture():
    try:
        capture = cv2.VideoCapture(0)
        writeToLog("Camera feed sucessfully acquired!")
        return capture
    except:
        writeToLog("No camera detected. Closing Program...")
        sys.exit()

#This function implements processes the video
def processVideo(frame, args, firstFrame):
    global statusText, previousStatusText, prevprevStatusText
    prevprevStatusText = previousStatusText
    previousStatusText = statusText
    statusText = "No movement detected."
    frame = imutils.resize(frame, width=500)
    frameGray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    frameBlur = cv2.GaussianBlur(frameGray, (21, 21), 5)
    if firstFrame is None:
        firstFrame = frameBlur
    frameDelta = cv2.absdiff(firstFrame, frameBlur)
    frameThresh = cv2.threshold(frameDelta, 20, 255, cv2.THRESH_BINARY)[1]
    frameDilate = cv2.dilate(frameThresh, None, iterations=15)
    contoursFind = cv2.findContours(frameDilate.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contoursGrab = imutils.grab_contours(contoursFind)
    for c in contoursGrab:
        if cv2.contourArea(c) < args["min_area"]:
            continue
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        monitorSubject(w,h)
    enterExit()
    return frame, firstFrame

#This function monitors a subject when in frame
def monitorSubject(xaxis, yaxis):
    x = int(xaxis)
    y = int(yaxis)
    global statusText, alertSent, alertTimerThreshold, currentAlertTimer, startAlertTimer
    if alertSent == True:
        statusText = "Alert has been Sent. Awaiting help..."
    elif x>y:
        if currentAlertTimer <= 0:
            writeToLog("Alert has been Sent. Awaiting help...")
            startAlertTimer = 0
            currentAlertTimer = alertTimerThreshold
            alertSent = True
        elif startAlertTimer != 0:
            statusText = "Subject appears to have fallen."
            currentAlertTimer = alertTimerThreshold - (time.time() - startAlertTimer)
        else:
            statusText = "Subject appears to have fallen."
            startAlertTimer = time.time()
            writeToLog("Suspected fall has occured. An alert will be sent if subject does not stand back up within 10 seconds.")
    elif x<y:
        if currentAlertTimer < alertTimerThreshold:
            startAlertTimer = 0
            currentAlertTimer = alertTimerThreshold
            writeToLog("Subject has returned to an upright position.")
            statusText = "Subject is safe."
        elif currentAlertTimer == alertTimerThreshold:
            statusText = "Subject is safe."

#Entry/Exit logging. Designed misread frames don't incorrectly log
def enterExit():
    global prevprevStatusText, statusText
    if prevprevStatusText == "No movement detected." and previousStatusText == "No movement detected." and statusText == "Subject is safe.":
        writeToLog("Subject has entered the camera's view.")
    elif prevprevStatusText == "Subject is safe." and previousStatusText == "No movement detected." and statusText == "No movement detected.":
        writeToLog("Subject has left the camera's view.")

#This function sends an alert
def sendAlert():
    statusText = "Awaiting Response..."

#This function displays the Video
def displayVideo(frame):
    #Add timestamp to the video then display
    frame = cv2.putText(frame, "Date/Time: {}".format(getTimeStamp()), (5, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.putText(frame, "Room Status: {}".format(statusText), (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imshow("Fall Alert Detection System", frame)

#This function closes the program
def closeProgram(capture):
    writeToLog("Terminating Program...\n\n\n")
    capture.release()
    cv2.destroyAllWindows()
    sys.exit()

#This is the main function of the program
def main():
    args, firstFrame, capture, frameWidth, frameHeight = initializeProgram()
    while (True):
        ret, frame = capture.read()
        if frame is None:
            break
        frame, firstFrame = processVideo(frame, args, firstFrame)
        displayVideo(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    closeProgram(capture)

#Script
if __name__ == "__main__":
    main()
