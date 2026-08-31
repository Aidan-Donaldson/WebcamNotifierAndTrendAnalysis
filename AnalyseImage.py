import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import tensorflow as tf
import cv2
import numpy as np
import matplotlib.pyplot as plt
import Manager
from datetime import datetime

class Model:
    
    def __init__(self, modelName, biasOffset, evntIdDetected):
        self.name = modelName
        self.model = tf.keras.models.load_model(f"Models/{modelName}", compile=False)
        self.biasOffset = biasOffset
        self.eventType = evntIdDetected
        if "G" in modelName:
            self.shape = 1
            self.readMode = cv2.IMREAD_GRAYSCALE
        elif "C" in modelName:
            self.shape = 3
            self.readMode = cv2.IMREAD_COLOR_RGB
        
    def Compile(self):
        self.model.compile(optimizer="adam",
                           loss="binary_crossentropy",
                           metrics=["accuracy"])
        
    def Normalise(self, img_array):
        return img_array/255

    def UndoNormalisation(self, img_array):
        return img_array*255
        
    def Infer(self, img):   
        maxConfidence = 1
        mostCertainImage = []
        
        imgToClassify = cv2.imread(f"{img}", self.readMode)
        imgToClassify = self.Normalise(imgToClassify)
        imgRows = len(imgToClassify)
        imgCols = len(imgToClassify[0])
        viewSize = int(min([imgRows, imgCols])/3.2+1)  #Alternative: 256, 100
        offset = int(viewSize*0.4)
#         for passes in range(2):
#             if maxConfidence != 1:
#                 break
#             if passes == 1:
#                 viewSize = int(viewSize/1.5 + 1)
#                 offset = int(viewSize*0.4)
            
        numFullSubsectionsY = (imgRows-viewSize) // offset + 1
        numFullSubsectionsX = (imgCols-viewSize) // offset + 1
        extraX = offset*numFullSubsectionsX < imgCols
        extraY = offset*numFullSubsectionsY < imgRows
        for subsectionsY in range(numFullSubsectionsY):
            totalOffsetY = subsectionsY*offset
            for subsectionsX in range(numFullSubsectionsX):
                subsection = []
                totalOffsetX = subsectionsX*offset
                for row in imgToClassify[totalOffsetY:viewSize+totalOffsetY]:
                    subsection.append(row[totalOffsetX:viewSize+totalOffsetX])
                maxConfidence, mostCertainImage = self.__SubsectionInference(subsection, maxConfidence, mostCertainImage)
            
            subsection = []
            if extraX:
                for row in imgToClassify[totalOffsetY:viewSize+totalOffsetY]:
                    subsection.append(row[imgCols-viewSize:])
                maxConfidence, mostCertainImage = self.__SubsectionInference(subsection, maxConfidence, mostCertainImage)

        if extraY:
            for subsectionsX in range(numFullSubsectionsX):
                subsection = []
                totalOffsetX = subsectionsX*offset
                for row in imgToClassify[imgRows-viewSize:]:
                    subsection.append(row[totalOffsetX:viewSize+totalOffsetX])
                maxConfidence, mostCertainImage = self.__SubsectionInference(subsection, maxConfidence, mostCertainImage)

            subsection = []
            if extraX:
                for row in imgToClassify[imgRows-viewSize:]:
                    subsection.append(row[imgCols-viewSize:])
                maxConfidence, mostCertainImage = self.__SubsectionInference(subsection, maxConfidence, mostCertainImage)
            
        return mostCertainImage

    def __SubsectionInference(self, subsection, highestConfidence, lastImage):
        toClassify = cv2.resize(np.array(subsection), (150, 150))
        
        toClassify = toClassify.reshape(-1, 150, 150, self.shape)
        prediction = self.model.predict(toClassify)
        confidence = prediction[0][0]
#         print(len(subsection), len(subsection[0]))
#         print(confidence)
#         plt.figure()
#         plt.imshow(subsection, cmap="gray")
#         plt.show()
        if (confidence+self.biasOffset).round() == 0:
            if confidence < highestConfidence: #highest confidence is the lowest number
                print(confidence, self.name)
                return (prediction[0], subsection)
        return (highestConfidence, lastImage)

        

def load_models():
    models = []
    models.append(Model("petclassifierG150_3.keras", 0.4, 2))
    models.append(Model("parcelCC150_1.keras", 0.498, 1))
    models.append(Model("personC150_1.keras", 0.3, 3))  
    return models
    

def Run(user):
    currentDir = os.path.dirname(os.path.realpath(__file__))
    targetFile = currentDir + "/Images"
    models = load_models()
    for model in models:
        model.Compile()
        img = np.array(model.Infer("tempFrame.jpg"))
        if len(img) > 0:
            img = np.uint8(model.UndoNormalisation(img))
            date = datetime.now()
            time = str(date.time())[:5]
            fileId = f"{date}".replace(".", "-").replace(" ", "-").replace(":", "-")
            filename = f"{fileId}.png"
            #print(model.readMode, cv2.IMREAD_COLOR_RGB, model.readMode == cv2.IMREAD_COLOR_RGB)
            if model.readMode == cv2.IMREAD_COLOR_RGB:
                cv2.imwrite(os.path.join(targetFile, filename), cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            else:
                cv2.imwrite(os.path.join(targetFile, filename), img)
            Manager.AddEvent(user, model.eventType, time, filename)

#Run(1)