from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.gui.OnscreenImage import OnscreenImage
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *


from sys import exit as sysExit
from math import pow, tan, radians, sqrt, trunc

from panda3d.core import loadPrcFile
 
loadPrcFile("configuracio.prc")

WIN_WIDTH = 800
H_WIDTH = WIN_WIDTH/2
WIN_HEIGHT = 600
H_HEIGHT = WIN_HEIGHT/2

CAM_FOV = 51.
CAM_FOV_RAD = radians(CAM_FOV)/2
CAM_FOV_RAD_TAN = tan(CAM_FOV_RAD)
#~ GRAV = 0
VEL_MAX_AVIO = 100
VEL_MIN_AVIO = 30
VEL_AVIO_RECTE = 40.
VEL_TOMBA_AVIO = 90.
ACC_TOMBA_AVIO = 150.
MARCAVEL_INI_X = 12
ACCELERACIO = 35
CAMERA_Y = 9
BALA_VEL_BASE = -600

QUIT_KEY = "escape"
ACCELERATE_KEY = "w"
DECELERATE_KEY = "s"
RIGHT_KEY = "d"
LEFT_KEY = "a"
CENTRA_RATA_KEY = "c"
SHOOT_KEYS = ["mouse1", "e"]
SHOOT_TIME = .1
class myApp(ShowBase, DirectObject):
	def __init__(self):
		ShowBase.__init__(self)
		DirectObject.__init__(self)
		
		self.keyMap = {"shoot":0, "centerPointer":0, "turn":0}
		self.bulletClock = 0.
		
		self.BALA_VEL = BALA_VEL_BASE-VEL_MIN_AVIO
		#Coses de propietats, colors, etc.
		
		while self.win.isClosed(): pass
		props = WindowProperties()
		props.setTitle("Behold!, the sword of the thousand truths")
		props.setSize(WIN_WIDTH, WIN_HEIGHT)
		props.setFixedSize(True)
		props.setCursorHidden(True)
		props.setUndecorated(True)
		props.setFullscreen(False)
		self.win.requestProperties(props)
		
		self.terreny = self.loader.loadModel('prova/Terreny/terrenym.egg')
		self.terreny.setScale(5)
		self.terreny.reparentTo(render)
		self.terreny.node().setIntoCollideMask(BitMask32(0x00000001))
		
		self.avio = render.attachNewNode("avio")
		self.avioR = self.avio.attachNewNode("avioDum2")
		self.modelAvioambCollide = self.loader.loadModel('prova/thund_amb_collide')
		self.modelAvio = self.modelAvioambCollide.find("**/thund")
		self.modelAvio.reparentTo(self.avioR)
		self.avioVel = VEL_MIN_AVIO
		self.modelAvioCollide = self.modelAvioambCollide.find("**/thundCollide")
		self.modelAvioCollide.node().setIntoCollideMask(BitMask32(0x00000000))
		self.modelAvioCollide.hide()	
		
		mat = Material()
		mat.setDiffuse(VBase4(0.5, 1, 0, 1))
		mat.setAmbient(VBase4(0.5, 1, 0, 1))
		mat.setShininess(0.5)
		self.modelAvio.setColor(1, 1, 0, 1)
		self.modelAvio.setMaterial(mat)
		self.terreny.setMaterial(mat)
		self.avio.reparentTo(render)
		self.avio.setPos(0, 0, 100)
		
		dlight = DirectionalLight('dlight')
		dlightnp = render.attachNewNode(dlight) 
		dlightnp.setHpr(10, -45, 0)
		render.setLight(dlightnp)
		
		expfog = Fog("Scene-wide exponential Fog object")
		expfog.setColor(126/255., 240/255., 1.)
		self.setBackgroundColor(126/255., 240/255., 1.)
		expfog.setExpDensity(0.001)
		render.setFog(expfog)


		#-#-#-#-configuracio de camara
		self.disableMouse()
		#~ self.oobe()
		self.camera.reparentTo(self.avio)
		self.camera.setHpr(self.avio, 180, 0, 0)
		self.camera.setPos(self.avio, 0, CAMERA_Y, 1.5)
		self.modelAvio.setScale(.14)
		self.camLens.setFov(CAM_FOV*(4./3.), CAM_FOV)
		
		
		self.mirilla2 = OnscreenImage(image="prova/textures/mira2.PNG", parent=pixel2d)
		self.mirilla2.setScale(32.)		
		self.mirilla2.setTransparency(1)
		self.mirilla2.setPos(H_WIDTH, 0, -H_HEIGHT)
		
		self.mirilla = OnscreenImage(image="prova/textures/mira1.PNG", parent=pixel2d)
		self.mirilla.setTransparency(1)
		self.mirilla.setScale(16.)
		self.mirilla.setPos(0, 0, 0)
		
		self.velocimetre = OnscreenImage(image="prova/textures/barravel.png", parent=pixel2d)
		self.velocimetre.setScale(128., 1., 32.)
		self.velocimetre.setTransparency(1)
		self.velocimetre.setPos(79, 0, -WIN_HEIGHT+17+5+20)
		
		self.marcaVelocitat = OnscreenImage(image="prova/textures/marcadorvel.png", parent=pixel2d)
		self.marcaVelocitat.setScale(8., 1., 16.)
		self.marcaVelocitat.setTransparency(1)
		self.marcaVelocitat.setPos(MARCAVEL_INI_X, 0, -WIN_HEIGHT+10)
		
		
		self.cursorGirar = pixel2d.attachNewNode("cursorGirar")
		self.cursorGirarImage = OnscreenImage(image="prova/textures/fletxa.png", parent=self.cursorGirar)
		self.cursorGirarImage.setScale(16./2, 1., 32./2)
		self.cursorGirarImage.setPos(0, 0, 0)
		self.cursorGirarImage.setHpr(-90, 0, -90)
		self.cursorGirarImage.setTransparency(1)
		
		cursorGirarEffect = BillboardEffect.make(
			up_vector = Vec3(0, 0, 1),
			eye_relative = False,
			axial_rotate = False, 
			offset = 0.,
			look_at = self.mirilla2,
			look_at_point = Point3(0,0,0))

		
		self.cursorGirar.setEffect(cursorGirarEffect)
		
		self.cTrav = CollisionTraverser()
		def giraAvio(task):
			timeVar = globalClock.getDt()
			point = self.win.getPointer(0)
			pointerx = point.getX()
			pointery = point.getY()
			#Cursors de la pantalla
			self.mirilla.setPos(pointerx, 0, -pointery)
			self.cursorGirar.setPos(pointerx, 0, -pointery)
			r = pow(abs(pointery-H_HEIGHT), 2) + pow(abs(pointerx-H_WIDTH), 2)
			if r > 400:
				self.mirilla.hide()
				self.cursorGirar.show()
			else:
				self.mirilla.show()
				self.cursorGirar.hide()
			#3D			
			pointerx = (pointerx - H_WIDTH)
			pointery = (pointery - H_HEIGHT)
			
			self.avioR.setX(self.avio, pointerx*3./float(WIN_WIDTH))
			self.avioR.setZ(self.avio, pointery*3./(WIN_HEIGHT))
			
			self.avio.setH(self.avio, -pointerx*256./WIN_WIDTH*timeVar)
			self.avio.setP(self.avio, pointery*256./WIN_HEIGHT*timeVar)
			
			self.avioR.setR(self.avio, -pointerx/10.)
			self.avioR.setP(self.avio, pointery/70.)
			self.avioR.setH(self.avio, -pointerx/50.)

			#~ self.avioVel += self.avioAcc*timeVar
			#~ self.avio.setPos(self.avio, self.avioVel*timeVar)
			return task.cont
			
		def propulsaAvio(acceleracio, task):
			self.avioVel += acceleracio*globalClock.getDt()
			if self.avioVel < VEL_MIN_AVIO:
				self.avioVel = VEL_MIN_AVIO
			elif self.avioVel > VEL_MAX_AVIO:
				self.avioVel = VEL_MAX_AVIO
			self.BALA_VEL = BALA_VEL_BASE-self.avioVel
			#MOSTRA LA VELOCITAT
			pos = float(self.avioVel-VEL_MIN_AVIO)/(VEL_MAX_AVIO-VEL_MIN_AVIO)
			self.camera.setY(CAMERA_Y+pos*4)
			self.marcaVelocitat.setX(MARCAVEL_INI_X+pos*137.)
			return task.cont
		
		def mouAvio(task):
			timeVar = globalClock.getDt()
			if self.keyMap["turn"] == 0:
				self.avio.setPos(self.avio, 0, -self.avioVel*timeVar, 0)
			else:
				self.avio.setPos(self.avio, self.avioVel/2.*self.keyMap["turn"]*timeVar, -self.avioVel*timeVar, 0)
			
			if self.keyMap["shoot"] == 1:
				if self.bulletClock <= 0.:
					self.bulletClock = SHOOT_TIME
					shoot()
					
				else:
					self.bulletClock -= timeVar
			else:
				self.bulletClock = 0.
			return task.cont
			
		
		def avioRecte(task):
			p = self.avio.getP(render)
			if p>170 or p<-170: return task.cont
			timeVar = globalClock.getDt()
			roll = self.avio.getR(render)
			if roll < -VEL_AVIO_RECTE*timeVar:
				self.avio.setR(render, roll+VEL_AVIO_RECTE*timeVar)
			elif roll <= VEL_AVIO_RECTE*timeVar:
				self.avio.setR(render, 0)
			else:
				self.avio.setR(render, roll-VEL_AVIO_RECTE*timeVar)
			return task.cont
			
		self.balaPositiu = True
		def shoot():
			bala = self.loader.loadModel('prova/bala')
			balaCol = CollisionNode("balaSphere")
			balaCol.setFromCollideMask(BitMask32(0x00000001))
			CHandler = CollisionHandlerQueue()
			balaColNp = bala.attachNewNode(balaCol)
			
			balaColSolid = CollisionSphere(0, 0, 0, 0.5)
			
			balaCol.addSolid(balaColSolid)
			bala.setPos(self.modelAvio.getPos(render))
			bala.setQuat(self.modelAvio.getQuat(render))
			self.cTrav.addCollider(balaColNp, CHandler)
			if self.balaPositiu:
				bala.setX(bala, 2.2*.14)
				self.balaPositiu = False
			else:
				bala.setX(bala, -2.2*.14)
				self.balaPositiu = True
			#~ if type(self.shootPoint) == 'libpanda.Point3':
				#~ bala.lookAt(self.shootPoint)
			#~ else: bala.setH(bala, 180.)
			taskMgr.add(mouBala, "moubala", extraArgs = [bala, self.BALA_VEL, CHandler], appendTask = True)
			
		def mouBala(bala, vel, CHandler, task):
			self.cTrav.traverse(render)
			#~ for i in range(CHandler.getNumEntries()):
				#~ entry = CHandler.getEntry(i)
			#~ print CHandler.getNumEntries()
			if task.time > 6:
				bala.detachNode()
				return task.done
			bala.setY(bala, vel*globalClock.getDt())
			return task.cont		
		
		def setKey(key, value):
			self.keyMap[key] = value
		
		def centraRatoli():
			point = self.win.getPointer(0)
			x = point.getX()
			y = point.getY()
			x -= H_WIDTH
			y -= H_HEIGHT
			r = sqrt(pow(abs(y), 2) + pow(abs(x), 2))
			def centra(t, x, y):
				self.win.movePointer(0, trunc(x*t)+H_WIDTH, trunc(y*t)+H_HEIGHT)
			
			i = LerpFunc(centra,
				fromData=1.,
				toData=0.,
				duration=r/700.,
				blendType='easeInOut',
				extraArgs=[x, y],
				name="centraRata")
			i.start()
		
		def apunta(task):
			if self.shootRayCHandler.getNumEntries()==0:
				self.shootPoint = None
			else:
				self.shootRayCHandler.sortEntries()
				entry = self.shootRayCHandler.getEntry(0)
				self.shootRayCHandler.clearEntries()
				self.shootPoint = entry.getSurfacePoint(render)
			return task.cont
		
		self.previousPos = 0
		self.interval01 = LerpPosHprInterval(self.modelAvio, .5, Point3(-3, 0, 0),
				VBase3(0, 0, 80), Point3(0, 0, 0),
				VBase3(0, 0, 0), blendType='easeInOut')
		self.interval10 = LerpPosHprInterval(self.modelAvio, .5, Point3(0, 0, 0),
				VBase3(0, 0, 0), Point3(3, 0, 0),
				VBase3(0, 0, -80), blendType='easeInOut')
		self.interval02 = LerpPosHprInterval(self.modelAvio, .5, Point3(3, 0, 0),
				VBase3(0, 0, -80), Point3(0, 0, 0),
				VBase3(0, 0, 0), blendType='easeInOut')
		self.interval20 = LerpPosHprInterval(self.modelAvio, .5, Point3(0, 0, 0),
				VBase3(0, 0, 0), Point3(-3, 0, 0),
				VBase3(0, 0, 80), blendType='easeInOut')
		self.interval12 = LerpPosHprInterval(self.modelAvio, 1., Point3(3, 0, 0),
				VBase3(0, 0, -80), Point3(-3, 0, 0),
				VBase3(0, 0, 80), blendType='easeInOut')
		self.interval21 = LerpPosHprInterval(self.modelAvio, 1., Point3(-3, 0, 0),
				VBase3(0, 0, 80), Point3(3, 0, 0),
				VBase3(0, 0, -80), blendType='easeInOut')
				
		def allIntervalsStopped():
			if self.interval01.isStopped() and self.interval10.isStopped() and self.interval02.isStopped() and self.interval20.isStopped() and self.interval12.isStopped() and self.interval21.isStopped():
				return True
			else: return False
		
		def tombaAvio(task):
			if self.keyMap["turn"]==0 and self.previousPos != 0 and allIntervalsStopped():
				if self.previousPos == 1: self.interval10.start()
				else: self.interval20.start()
				self.previousPos = 0
			elif self.keyMap["turn"]==-1 and self.previousPos != -1 and allIntervalsStopped():
				if self.previousPos == 0: self.interval01.start()
				else: self.interval21.start()
				self.previousPos = -1
			elif self.keyMap["turn"]==1 and self.previousPos != 1 and allIntervalsStopped():
				if self.previousPos == 0: self.interval02.start()
				else: self.interval12.start()
				self.previousPos = 1
			return task.cont
			
		#events
		self.accept(QUIT_KEY, sysExit, [0])
		self.accept(ACCELERATE_KEY, taskMgr.add, [propulsaAvio, "propulsaAvio1", None, [ACCELERACIO], None, None, True])
		self.accept(ACCELERATE_KEY+"-up", taskMgr.remove, ["propulsaAvio1"])
		
		self.accept(DECELERATE_KEY, taskMgr.add, [propulsaAvio, "propulsaAvio2", None, [-ACCELERACIO], None, None, True])
		self.accept(DECELERATE_KEY+"-up", taskMgr.remove, ["propulsaAvio2"])
		
		#~ self.accept("q", taskMgr.add, [avioRecte, "avioRecte"])
		#~ self.accept("q-up", taskMgr, [avioRecte, "avioRecte"])
		
		#~ self.accept"p", tas
		#~ self.accept("d", taskMgr.add, [rodaAvio, "rodaAvio2", None, [100], None, None, True])
		#~ self.accept("d-up", taskMgr.remove, ["rodaAvio2"])
		for key in SHOOT_KEYS:
			self.accept(key, setKey, ["shoot", 1])
			self.accept(key+"-up", setKey, ["shoot", 0])
		
		self.accept(RIGHT_KEY, setKey, ["turn", -1])
		self.accept(LEFT_KEY, setKey, ["turn", 1])
		self.accept(RIGHT_KEY+"-up", setKey, ["turn", 0])
		self.accept(LEFT_KEY+"-up", setKey, ["turn", 0])
		
		self.accept(CENTRA_RATA_KEY, centraRatoli)
		
		taskMgr.add(giraAvio, "GiraAvio")
		taskMgr.add(mouAvio, "MouAvio")
		taskMgr.add(avioRecte, "avioRecte")
		taskMgr.add(tombaAvio, "tombaAvio")
		self.render.setAntialias(AntialiasAttrib.MAuto)
myApp()
run()