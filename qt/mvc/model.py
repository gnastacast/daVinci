import numpy as np
import cv2
from PyQt4 import QtGui
from vtkTools import setupRenWinForRegistration
from vtkTools import makeVtkImage
from vtkTools import actorFromStl

class MainModel(object):
    def __init__(self, imgDims, stlPath, camMatrix):
        self._update_funcs = []

        self.imgDims = imgDims
        self.camMatrix = camMatrix

        # variables for masking
        self.masking = False
        self.rect = (0,0,0,0)
        self.mask = np.ones(imgDims[::-1],np.uint8)*cv2.GC_PR_FGD
        print self.mask.shape
        print self.imgDims

        # variables for video
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3,self.imgDims[0])
        self.cap.set(4,self.imgDims[1])

        # variables for rendering
        self.videoFrame = np.zeros(self.imgDims,np.uint8)
        self.bgImage = makeVtkImage(self.imgDims)
        self.stlActor = actorFromStl(stlPath)
        self.stlActor.GetProperty().SetColor(0,1,0)
        self.stlActor.GetProperty().SetOpacity(1)
        self.stlActor.SetPosition(0,0,.15)
        self.stlActor.SetOrientation(180,0,0)
        # This will be set later using setRenWin
        self.renWin = None

    def setRenWin(self, renWin):
        self.renWin = setupRenWinForRegistration(renWin,
                                                 self.bgImage,
                                                 self.stlActor,
                                                 self.camMatrix)
    # subscribe a view method for updating
    def subscribe_update_func(self, func):
        if func not in self._update_funcs:
            self._update_funcs.append(func)

    # unsubscribe a view method for updating
    def unsubscribe_update_func(self, func):
        if func in self._update_funcs:
            self._update_funcs.remove(func)

    # update registered view methods
    def announce_update(self):
        for func in self._update_funcs:
            func()