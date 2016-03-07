import numpy as np
from vtk.util import numpy_support
import vtk
import cv2

# Sets up a three channel empty vtkImageData object
def makeVtkImage(imgDims):
    imData = vtk.vtkImageData()
    imData.SetDimensions(imgDims[0], imgDims[1], 1) #set dimensions as necessary
    imData.SetOrigin(0,0,0) #set origin as necessary
    imData.SetSpacing(1, 1, 1) #set spacing as necessary
    imData.SetNumberOfScalarComponents( 3 )
    imData.SetScalarTypeToUnsignedChar()
    imData.Update()
    return imData

def numpyToVtkImage(numpyData,VTKImageData):
    rgb = cv2.cvtColor(numpyData, cv2.COLOR_BGR2RGB)
    VTK_data = numpy_support.numpy_to_vtk(num_array=rgb[::-1].ravel(),deep=True, array_type=vtk.VTK_CHAR)
    VTKImageData.GetPointData().SetScalars(VTK_data)
    return VTKImageData

def vtkImageToNumpy(VTKImageData,numpyData):
    size = VTKImageData.GetDimensions()
    numpyData = numpy_support.vtk_to_numpy(VTK_data)
    numpyData = numpyData.reshape((size[1],size[0],3))
    return numpyData

def actorFromStl(stlPath):
    # Read in STL file
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stlPath)
    mapper = vtk.vtkPolyDataMapper()
    if vtk.VTK_MAJOR_VERSION <= 5:
        mapper.SetInput(reader.GetOutput())
    else:
        mapper.SetInputConnection(reader.GetOutputPort())
    # Create actor that we will position manually
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor

def setupRenWinForRegistration(renWin,bgImage,actor,camMatrix):
    renWin.SetNumberOfLayers(2)
    # Create foreground renderer for stl object
    ren=vtk.vtkRenderer()
    ren.SetLayer(1)
    renWin.AddRenderer(ren)
    ren.AddActor(actor)
    imgDims = bgImage.GetDimensions()
    renWin.SetSize(imgDims[0],imgDims[1])
    camera = _cameraFromMatrix(camMatrix,imgDims,imgDims)
    ren.SetActiveCamera(camera)
    #ren.SetActiveCamera(camera)

    # Create background renderer for static object
    backgroundRen = vtk.vtkRenderer()
    backgroundRen.SetLayer(0)
    backgroundRen.InteractiveOff()
    backgroundRen.SetBackground(1, 1, 1)
    # Create background object for showing video feed.
    bgCamera, backgroundActor = _makeImagePlane(bgImage)
    # Setup camera
    backgroundRen.AddActor(backgroundActor)
    backgroundRen.SetActiveCamera(bgCamera)
    # Add background renderer to window
    renWin.AddRenderer(backgroundRen)
    
    # Way of getting camera: renWin.GetRenderers().GetFirstRenderer()
    return renWin

# Loads an image and returns a plane object and a camera pointed towards it
def _makeImagePlane(imageData) :
    ''' Takes a vtkImageData object and
        returns a plane textured with that image
        and a camera for the background renderer
        http://www.vtk.org/Wiki/VTK/Examples/Cxx/Images/BackgroundImage
        was the basis for this function
    '''
    imageActor = vtk.vtkImageActor()
    if vtk.VTK_MAJOR_VERSION <= 5 :
      imageActor.SetInput(imageData);
    else :
      imageActor.SetInputData(imageData);

    origin = imageData.GetOrigin()
    spacing = imageData.GetSpacing()
    extent = imageData.GetExtent()

    camera = vtk.vtkCamera()
    camera.ParallelProjectionOn()

    xc = origin[0] + 0.5*(extent[0] + extent[1])*spacing[0]
    yc = origin[1] + 0.5*(extent[2] + extent[3])*spacing[1]
    yd = (extent[3] - extent[2] + 1)*spacing[1];
    d = camera.GetDistance()
    camera.SetParallelScale(0.5*yd)
    camera.SetFocalPoint(xc,yc,0.0)
    camera.SetPosition(xc,yc,d);

    return camera, imageActor

# Sets up a camera based on a camera intrinsics matrix from OpenCV
def _cameraFromMatrix(camMatrix, imageDims, windowDims) :
    ''' Takes a camera matrix derived from OpenCV
        returns a camera for registration
        http://stackoverflow.com/questions/25539898/how-to-apply-the-camera-pose-transformation-computed-using-epnp-to-the-vtk-camer
        was a great help

        Input: 
            camMatrix (np.ndarray) = 4x4 camera intrinsic matrix
            imageDims ((float, float))  = width and height of image to register to
            imageDims ((float, float))  = width and height of render window

        Output:
            camera (vtk.vtkCamera) = camera to use for registration
    '''
    # Initialize camera
    camera = vtk.vtkCamera()

    # Set view angle
    focalLengthY = camMatrix[1,1]
    if( windowDims[1] != imageDims[1] ):
        factor = float(windowDims[1])/float(imageDims[1])
        focalLengthY = camMatrix[1,1] * factor
    viewAngle = 2 * np.arctan( (windowDims[1] / 2.0 ) / focalLengthY ) * 180 / np.pi
    camera.SetViewAngle(viewAngle)

    #Set window center
    py = 0;
    height = 0;

    if imageDims[0] != windowDims[0] or imageDims[1] != windowDims[1] :

        factor = float(windowDims[1])/float(imageDims[1])
        px = factor * camMatrix[0,2]
        width = windowDims[0]
        expectedWindowSize = np.round(factor * float(imageDims[0]));
        if( expectedWindowSize != windowDims[0] ):
            diffX = (windowDims[0] - expectedWindowSize) / 2;
            px = px + diffX

        py = factor * camMatrix[1,2]
        height = windowDims[1]

    else :
        px = camMatrix[0,2]
        width = imageDims[0]

        py = camMatrix[1,2]
        height = imageDims[1]

    cx = width - px;
    cy = py

    windowCenter = [0,0]

    windowCenter[0] = cx / ( ( width-1)/2 ) - 1 
    windowCenter[1] = cy / ( ( height-1)/2 ) - 1

    camera.SetWindowCenter(windowCenter[0],windowCenter[1])

    camera.SetPosition(0,0,0)
    camera.SetFocalPoint(0,0,1)

    return camera