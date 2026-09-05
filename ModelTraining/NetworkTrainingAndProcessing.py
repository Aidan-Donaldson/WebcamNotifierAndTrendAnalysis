import tensorflow as tf
from tensorflow.keras.datasets import mnist
import matplotlib.pyplot as plt
import numpy as np
import os
import cv2
import pickle
from google.colab import drive

drive.mount("/content/drive")

#---------------------------------------------------------------------------------

def LoadData():
    LOADDIR = "/content/drive/MyDrive/Datasets/ProcessedSets"
    with open(LOADDIR+"/TrainingFeaturesG150_2.pickle","rb") as train_features:
        XTrain = pickle.load(train_features)
    with open(LOADDIR+"/ValidationFeaturesG150_2.pickle","rb") as val_features:
        XVal = pickle.load(val_features)
    with open(LOADDIR+"/TrainingTargetsG150_2.pickle","rb") as train_targets:
        yTrain = pickle.load(train_targets)
    with open(LOADDIR+"/ValidationTargetsG150_2.pickle","rb") as val_targets:
        yVal = pickle.load(val_targets)

    return (XTrain, XVal, yTrain, yVal)

def LoadModel():
    model = tf.keras.models.load_model("/content/drive/MyDrive/Models/PetClassifierG150_2.keras", compile=False)

    model.compile(optimizer = "adam",
              loss="binary_crossentropy",
              metrics=["accuracy"])

    return model

#XTrain, XVal, yTrain, yVal = LoadData()
model = LoadModel()
#print(len(XTrain), len(XVal))

#---------------------------------------------------------------------------------

DIRECTORY = "/content/drive/My Drive/Datasets"
#CLASSES = ["CombinedPets", "EmptyEvent"]
#classTarget = {"CombinedPets" : np.int8(0), "EmptyEvent" : np.int8(1)}
#CLASSES = ["Cardboard", "EmptyEventCardboard"]
#classTarget = {"Cardboard" : np.int8(0), "EmptyEventCardboard" : np.int8(1)}
CLASSES = ["Person", "EmptyPerson"]
classTarget = {"Person" : np.int8(0), "EmptyPerson" : np.int8(1)}
def CreateTrainingData(width, height) -> list[tuple[list[float], str]]:
    #readMode = cv2.IMREAD_GRAYSCALE
    readMode = cv2.IMREAD_COLOR_RGB
    trainingData = []
    i=0
    for imgClass in CLASSES:
      path = DIRECTORY+"/"+imgClass
      print(path)
      for subGroup in os.listdir(path):
        print(subGroup)
        newPath = path+"/"+subGroup
        print(newPath)
        i = 0
        for img in os.listdir(newPath):
            try:
                imgArray = cv2.imread(os.path.join(newPath, img), readMode)
                imgArray = cv2.resize(imgArray, (width, height))   # Try with no interpolation and see if performance is affected
                #imgArray = cv2.resize(imgArray, (width, height)),
                #                       interpolation = cv2.INTER_AREA)
                normalisedImgArray = NormaliseTrainingData(imgArray)
                trainingData.append([normalisedImgArray,
                                      classTarget[imgClass]])
                i += 1
                if i % 100 == 0:
                    print(i)
                if i % 4000 == 0:
                    i = 0
                    break
            except:
                print(f"Error at: {i}")
            #plt.figure()
            #plt.imshow(imgArray/255, cmap="gray")
            #break

    return trainingData

def NormaliseTrainingData(imgArray) -> list[float]:
  return imgArray/255

width = 150
height = 150
trainingData = CreateTrainingData(width, height)
print(len(trainingData))
#print(trainingData[0][1], trainingData[9000][1], trainingData[9001][1])

#---------------------------------------------------------------------------------
DIRECTORY = "/content/drive/My Drive/Datasets"
#CLASSES = ["CombinedPets", "EmptyEvent"]
#CLASSES = ["Cardboard", "EmptyEventCardboard"]
CLASSES = ["Person", "EmptyPerson"]
num = []
for imgClass in CLASSES:
    i = 0
    path = DIRECTORY+"/"+imgClass
    for subGroup in os.listdir(path):
        newPath = path+"/"+subGroup
        print(newPath)
        for img in os.listdir(newPath):
            i += 1
            if i % 4000 == 0:
                break
    num.append(i)

numImages = [num[0], num[1]]
import plotly.express as px
px.pie(names=CLASSES, values=numImages)

#---------------------------------------------------------------------------------
def TrainingDataSplit(trainingData, validationSplit) -> tuple[float, str]:
    np.random.shuffle(trainingData)
    dataPoints = len(trainingData)
    validationSplitIndex = int(dataPoints*validationSplit)
    validationSet = trainingData[:validationSplitIndex]
    trainingSet = trainingData[validationSplitIndex:]
    return trainingSet, validationSet

trainingSet, validationSet = TrainingDataSplit(trainingData, 0.2)
del trainingData

#print(len(trainingData))
print(len(trainingSet))
print(len(validationSet))

XTrain = np.array([i[0] for i in trainingSet])
yTrain = np.array([i[1] for i in trainingSet])

del trainingSet # FREE UP MEMORY

XVal = np.array([i[0] for i in validationSet])
yVal = np.array([i[1] for i in validationSet])

del validationSet

print(XTrain[0])

#XTrain = XTrain.reshape(-1, width, height, 1) #For Greyscal
#XVal = XVal.reshape(-1, width, height, 1) # For Greyscale

XTrain = XTrain.reshape(-1, width, height, 3) # For RGB
XVal = XVal.reshape(-1, width, height, 3) # For RGB

with open("TrainingFeaturesPersonC150_1.pickle", "wb") as train_features:
    pickle.dump(XTrain, train_features)
with open("ValidationFeaturesPersonC150_1.pickle", "wb") as val_features:
    pickle.dump(XVal, val_features)
with open("TrainingTargetsPersonC150_1.pickle", "wb") as train_targets:
    pickle.dump(yTrain, train_targets)
with open("ValidationTargetsPersonC150_1.pickle", "wb") as val_targets:
    pickle.dump(yVal, val_targets)

#---------------------------------------------------------------------------------

#!cp TrainingFeaturesPersonC150_1.pickle /content/drive/MyDrive/Datasets/ProcessedSets
#!cp ValidationFeaturesPersonC150_1.pickle /content/drive/MyDrive/Datasets/ProcessedSets
#!cp TrainingTargetsPersonC150_1.pickle /content/drive/MyDrive/Datasets/ProcessedSets
#!cp ValidationTargetsPersonC150_1.pickle /content/drive/MyDrive/Datasets/ProcessedSets

#---------------------------------------------------------------------------------
def CreateModel():
    model = tf.keras.models.Sequential([
        tf.keras.layers.InputLayer(shape=XTrain.shape[1:]),
        tf.keras.layers.Conv2D(128, (3,3), activation="relu"),
        tf.keras.layers.MaxPooling2D(3,3),
        tf.keras.layers.Conv2D(64, (10,10), activation="relu"),
        tf.keras.layers.MaxPooling2D(6,6),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid")])
    return model

model = CreateModel()
model.compile(optimizer="adam",
              loss="binary_crossentropy",
              metrics=["accuracy"])

#model.fit(XTrain, yTrain, epochs=3)
model.fit(XTrain, yTrain, batch_size=32, epochs=6)

#---------------------------------------------------------------------------------
valLoss, valAcc = model.evaluate(XVal, yVal)
print(valLoss, valAcc)
print(XTrain.shape)

#---------------------------------------------------------------------------------
predictions = model.predict([XVal])
print(yTrain, len(yVal))
event = 0
notEvent = 0
for i in range(len(predictions)):
    prediction = (predictions[i]+0.15).round()
    if prediction != yVal[i]:
        if prediction == 0:
            event +=1
        else:
            notEvent +=1
        #plt.figure()
        #plt.imshow(XVal[i], cmap="gray")
        #plt.title(f'Prediction: {prediction}')
        #plt.show()
print(pet, notPet)

#---------------------------------------------------------------------------------
model.save("personC150_1.keras")

!cp personC150_1.keras /content/drive/MyDrive/Models
print("Saved Model!")

#---------------------------------------------------------------------------------
# INFER IN ANALYSEIMAGE.PY IS AN UPDATED AND MORE ACCURATE VERSION. BELOW CODE   # USED FOR QUICK TESTING IN COLAB
def NormaliseTrainingData(imgArray) -> list[float]:
    return imgArray/255

def videoInference(data):
    viewSize = 200
    offset = 70
    imgToClassify = cv2.imread(f"/content/{data}", cv2.IMREAD_COLOR_RGB)
    imgToClassify = NormaliseTrainingData(imgToClassify)
    imgRows = len(imgToClassify)
    imgCols = len(imgToClassify[0])
    numFullSubsectionsY = (imgRows-viewSize) // offset
    numFullSubsectionsX = (imgCols-viewSize) // offset

    for subsectionsY in range(numFullSubsectionsY):
        totalOffsetY = subsectionsY*offset
        for subsectionsX in range(numFullSubsectionsX):
            subsection = []
            totalOffsetX = subsectionsX*offset
            for row in imgToClassify[totalOffsetY:viewSize+totalOffsetY]:
                subsection.append(row[totalOffsetX:viewSize+totalOffsetX])
            PredictSubset(subsection)

        subsection = []
        if offset*numFullSubsectionsX < imgCols:
            for row in imgToClassify[totalOffsetY:viewSize+totalOffsetY]:
                subsection.append(row[imgCols-viewSize:])
            PredictSubset(subsection)

    if offset*numFullSubsectionsY < imgRows:
        for subsectionsX in range(numFullSubsectionsX):
            subsection = []
            totalOffsetX = subsectionsX*offset
            for row in imgToClassify[imgRows-viewSize:]:
                subsection.append(row[totalOffsetX:viewSize+totalOffsetX])
            PredictSubset(subsection)

        subsection = []
        if offset*numFullSubsectionsX < imgCols:
            for row in imgToClassify[imgRows-viewSize:]:
                subsection.append(row[imgCols-viewSize:])
            PredictSubset(subsection)

def PredictSubset(subsection):
    toClassify = cv2.resize(np.array(subsection), (150, 150))
    toClassify = toClassify.reshape(-1, 150, 150, 3)
    prediction = model.predict([toClassify])
    print(prediction)
    #plt.figure()
    #plt.imshow(subsection, cmap="gray")
    if (prediction[0]+0.4).round() == 0:
        plt.figure()
        plt.imshow(subsection, cmap="gray")
        print(prediction[0])

videoInference("ClassificationTestLarge2.jpg")
