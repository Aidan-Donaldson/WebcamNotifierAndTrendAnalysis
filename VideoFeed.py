import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import time
import Manager
import AnalyseImage

NOWEBCAMIMAGE = np.array(cv2.imread(f"NoWebcam.jpg"))

def Setup():
    cv2.namedWindow("CameraView", cv2.WINDOW_NORMAL)
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    video.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    video.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    startTime = time.time()
    
    return (startTime-30, video)

def PerformAnalysis(video, user):
    hasFrame, frame = video.read()
    numpyFrame= np.array(frame)
    maxDifference = 0
    if hasFrame:
        frameDelta = NOWEBCAMIMAGE - numpyFrame + 10
        for row in frameDelta[:20]:
            for col in row:
                if max(col) > maxDifference:
                    maxDifference = max(col)
        
    if hasFrame and maxDifference >= 15:
        cv2.imshow("CameraView", frame)
        cv2.imwrite("tempFrame.jpg", frame)
        AnalyseImage.Run(user)
    else:
        print("No webcam detected")
    
    return hasFrame, frame

if __name__ == "__main__":
    import TkinterWindow as app
    
    user = app.app.user
    running = False
    compareTime = 0
    if user is not None:
        compareTime, video = Setup()
        running = True
        
    while running == True:
        currentTime = time.time()
        timeDelta = time.time() - compareTime
        if timeDelta >= 40:
            compareTime = time.time()
            Manager.Update(user)
            PerformAnalysis(video, user)
                
        exit_key = cv2.waitKey(1)
        if exit_key == 27:
            running = False
            video.release()
            cv2.destroyWindow("CameraView")  