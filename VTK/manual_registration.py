#!/usr/bin/env python
 
import vtk
import random

camStatic = vtk.vtkCamera()
camStatic.SetFocalPoint(0,0,0)
camStatic.SetPosition(0,0,200)
camStatic.SetViewUp(0,1,0)

# Performs manual registration of an STL file
def register(stlPath="suzanne.stl", imagePath=None, camera=None):
	''' Helper function for rough user registration of an .stl file

		Optional Input:
		      stlPath = path to an STL file to register
		      imagePath = path to an image to register the STL again
		      camera = camera being used

		Output:
		      actorMatrix (vtkMatrix4x4) = transform from camera to object

		- The default stlPath is "suzanne.stl"
		- If no image path is specified the object will be rendered at a
		  random orientation and position
		- If no camera is specified the camera will be placed at (0,0,300)
		  facing (0,0,0) with an up vector of (0,1,0) 

		Example:

		   import manual_registration
		   print manual_registration.register("suzanne.stl","suzanne.jpg")

		Version 1.0 2015-November-04 N. Zevallos
	'''
	global camStatic
	# Read in STL file
	reader = vtk.vtkSTLReader()
	reader.SetFileName(stlPath)
	mapper = vtk.vtkPolyDataMapper()
	if vtk.VTK_MAJOR_VERSION <= 5:
		mapper.SetInput(reader.GetOutput())
	else:
		mapper.SetInputConnection(reader.GetOutputPort())
	
	if camera != None :
		camStatic.SetFocalPoint(camera.GetFocalPoint())
		camStatic.SetPosition(camera.GetPosition())
		camStatic.SetViewUp(camera.GetViewUp())

	# Create render window and interactor
	renWin = vtk.vtkRenderWindow()
	renWin.SetSize(640, 480)
	renWin.SetNumberOfLayers(2)
	iren = vtk.vtkRenderWindowInteractor()
	iren.SetRenderWindow(renWin)
	iren.SetInteractorStyle(RegistrationInteractorStyle())

	# Create renderer for interaction
	ren=vtk.vtkRenderer()
	ren.SetLayer(1)
	renWin.AddRenderer(ren)
	# Setup camera
	ren.GetActiveCamera().SetFocalPoint(camStatic.GetFocalPoint())
	ren.GetActiveCamera().SetPosition(camStatic.GetPosition())
	ren.GetActiveCamera().SetViewUp(camStatic.GetViewUp())

	# Create actor that we will position manually
	mainActor = vtk.vtkActor()
	mainActor.SetMapper(mapper)
	mainActor.GetProperty().SetColor(0,1,0)
	mainActor.GetProperty().SetOpacity(0.5);
	# Add the actor
	ren.AddActor(mainActor)

	# If there is no image provided, make one up
	if imagePath == None :
		# Create background renderer for static object
		backgroundRen = vtk.vtkRenderer()
		backgroundRen.SetLayer(0)
		backgroundRen.InteractiveOff()
		backgroundRen.SetBackground(1, 1, 1)
		renWin.AddRenderer(backgroundRen)
		# Setup camera
		backgroundRen.GetActiveCamera().SetFocalPoint(camStatic.GetFocalPoint())
		backgroundRen.GetActiveCamera().SetPosition(camStatic.GetPosition())
		backgroundRen.GetActiveCamera().SetViewUp(camStatic.GetViewUp())

		# Create static background actor
		backgroundActor = vtk.vtkActor()
		backgroundActor.SetMapper(mapper)
		backgroundActor.GetProperty().SetColor(1,0,0)
		backgroundActor.SetPosition(random.random()*100-100,
									random.random()*100-100,
									random.random()*200-200)
		backgroundActor.SetOrientation(random.random()*360-180,
									   random.random()*360-180,
									   random.random()*360-180)
		#backgroundActor.SetOrientation(0,0,0)
		#backgroundActor.SetPosition(0,0,0)
		# Add the actor
		backgroundRen.AddActor(backgroundActor)
	
	# This allows the interactor to initalize itself. It has to be
	# called before an event loop.
	iren.Initialize()
	renWin.Render()

	print(backgroundActor.GetMatrix())

	iren.Start()

	actorTransform = vtk.vtkTransform()
	actorTransform.SetMatrix(camStatic.GetViewTransformMatrix())
	actorTransform.Inverse()
	camMatrix = ren.GetActiveCamera().GetViewTransformMatrix()
	actorTransform.Concatenate(camMatrix)

	print(actorTransform.GetMatrix())

# Class defining a modified interactor style for manual registration
class RegistrationInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
 
	def __init__(self,parent=None):
		self.AddObserver("KeyPressEvent", self.keyPressEvent)

	def keyPressEvent(self,obj,event):
		global camStatic
		inter = self.GetInteractor()
		key = inter.GetKeyCode()
		if key=='c' or key =='C':
			ren = self.GetCurrentRenderer()
			ren.GetActiveCamera().SetFocalPoint(camStatic.GetFocalPoint())
			ren.GetActiveCamera().SetPosition(camStatic.GetPosition())
			ren.GetActiveCamera().SetViewUp(camStatic.GetViewUp())
			inter.Render()

if __name__ == "__main__":
	register()