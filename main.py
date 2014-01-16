from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task
from direct.gui.OnscreenImage import OnscreenImage
from pandac.PandaModules import *
from direct.interval.IntervalGlobal import *
from panda3d.physics import BaseParticleEmitter,BaseParticleRenderer

from panda3d.physics import PointParticleFactory,SpriteParticleRenderer, SphereVolumeEmitter
from direct.particles.Particles import Particles
from direct.particles.ParticleEffect import ParticleEffect
from direct.particles.ForceGroup import ForceGroup
 
from sys import exit as sysExit
from math import pow, tan, radians, sqrt, trunc
from random import randint

from panda3d.core import loadPrcFile

loadPrcFile("configuracio.prc")


class Jugador(DirectObject):
	#Les variables que tinguin un # son canviables, i les que tinguin ## depenen de la nau
	WIN_WIDTH = 800 #
	H_WIDTH = WIN_WIDTH/2
	WIN_HEIGHT = 600 #
	H_HEIGHT = WIN_HEIGHT/2
	
	CAM_FOV = 51.
	CAM_FOV_RAD = radians(CAM_FOV)/2
	CAM_FOV_RAD_TAN = tan(CAM_FOV_RAD)
	
	VEL_MAX_AVIO = 100 ##
	VEL_MIN_AVIO = 30 ##
	VEL_AVIO_RECTE = 40. ##
	VEL_TOMBA_AVIO = 90. ##
	VEL_COSTAT = 30. ##
	ACCELERACIO = 35 ##
	CAMERA_Y = -9 ##
	BALA_VEL_BASE = 500 ##

	QUIT_KEY = "escape" #
	ACCELERATE_KEY = "w" #
	DECELERATE_KEY = "s" #
	RIGHT_KEY = "d" #
	LEFT_KEY = "a" #
	CENTRA_RATA_KEY = "c" #
	SHOOT_KEYS = ["mouse1", "e"] #
	SHOOT_TIME = .15 ##
	
	def __init__(self, base, ini_pos=Point3(0, 100, 100), tipus="kamikaze", wwidth=None, wheight=None):
		DirectObject.__init__(self)
		
		if wwidth and wheight:
			self.WIN_WIDTH = wwidth
			self.H_WIDTH = self.WIN_WIDTH/2
			self.WIN_HEIGHT = wheight
			self.H_HEIGHT = self.WIN_HEIGHT/2
		
		self.keyMap = {"shoot":0, "centerPointer":0, "turn":0}
		self.bulletClock = 0.
		self.overheatClock = 0.
		
		self.BALA_VEL = self.BALA_VEL_BASE+self.VEL_MIN_AVIO
		
		
		ambient = AmbientLight("alight")
		ambientNp = render.attachNewNode(ambient)
		ambient.setColor(VBase4(.3, .3, .3, 1.))
		
		self.avio = render.attachNewNode("avio")
		self.avio.setHpr(randint(0, 359), randint(0, 359), randint(0, 359))
		self.avio.setPos(ini_pos)
		
		self.avioR = self.avio.attachNewNode("avioDum2")
		if tipus == "kamikaze":
			self.modelAvio = base.loader.loadModel('prova/avio1blend')
		else:
			self.modelAvio = base.loader.loadModel('prova/avio1blend')
			
		self.modelAvio.reparentTo(self.avioR)
		self.avioVel = self.VEL_MIN_AVIO
		self.balaDreta = self.modelAvio.find("**/BalaDreta")
		self.balaEsquerra = self.modelAvio.find("**/BalaEsquerra")
		self.avio.setLight(ambientNp)
		self.avio.setAntialias(AntialiasAttrib.MMultisample)
		
		self.modelAvio.setColor(1, 1, 0, 1)
		self.modelAvio.setScale(.51)
		
		lightBales = AmbientLight('dlight')
		self.lightBalesNp = base.camera.attachNewNode(lightBales)
		self.lightBalesNp.setHpr(0, 0, 0)
		
		#-#-#-#-configuracio de camara
		base.disableMouse()
		#~ self.oobe()
		base.camera.reparentTo(self.avio)
		base.camera.setHpr(self.avio, 0, 0, 0)
		base.camera.setPos(self.avio, 0, self.CAMERA_Y, 1.5)
		base.camLens.setFov(self.CAM_FOV*(4./3.), self.CAM_FOV)
		
		self.mirilla2 = OnscreenImage(image="prova/textures/areatir2.png", parent=pixel2d)
		self.mirilla2.setScale(128)              
		self.mirilla2.setTransparency(1)
		self.mirilla2.setPos(self.H_WIDTH, 0, -self.H_HEIGHT)
		
		self.mirilla = base.loader.loadModel("prova/textures/fixador.egg")
		self.mirilla.reparentTo(pixel2d)
		self.mirilla.setScale(64.)
		self.mirilla.setPos(0, 0, 0)
		self.mirilla.find('**/+SequenceNode').node().pose(0)
		
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
	
		
		self.overheats = []
		for i in range(8):
			if i%2==0: self.overheats.append(OnscreenImage(image="prova/textures/overheat1.png", parent = pixel2d))
			else: self.overheats.append(OnscreenImage(image="prova/textures/overheat2.png", parent = pixel2d))
			self.overheats[i].setScale(32., 1., 32.)
			self.overheats[i].setTransparency(1)
			self.overheats[i].hide()
		self.overheats[0].setPos(self.H_WIDTH+36, 0, -self.H_HEIGHT+36)
		self.overheats[0].setHpr(0, 0, 0)
		self.overheats[1].setPos(self.H_WIDTH+36, 0, -self.H_HEIGHT+36)
		self.overheats[1].setHpr(0, 0, 0)
		self.overheats[2].setPos(self.H_WIDTH+36, 0, -self.H_HEIGHT-36)
		self.overheats[2].setHpr(0, 0, 90)
		self.overheats[3].setPos(self.H_WIDTH+36, 0, -self.H_HEIGHT-36)
		self.overheats[3].setHpr(0, 0, 90)
		self.overheats[4].setPos(self.H_WIDTH-36, 0, -self.H_HEIGHT-36)
		self.overheats[4].setHpr(0, 0, 180)
		self.overheats[5].setPos(self.H_WIDTH-36, 0, -self.H_HEIGHT-36)
		self.overheats[5].setHpr(0, 0, 180)
		self.overheats[6].setPos(self.H_WIDTH-36, 0, -self.H_HEIGHT+36)
		self.overheats[6].setHpr(0, 0, -90)
		self.overheats[7].setPos(self.H_WIDTH-36, 0, -self.H_HEIGHT+36)
		self.overheats[7].setHpr(0, 0, -90)
		
		#PARTICLE SYSTEM SETUP
		self.particlesDummy = render.attachNewNode("particlesDummy")
		self.particlesDummy.setPosHprScale(0, 0, 0, 0, 0, 0, 1, 1, 1)
		self.particlesDummy.clearLight(render.find("dlight"))
		self.particlesDummy.setLight(self.lightBalesNp)
		base.enableParticles()

		#COLLISIONS
		base.cTrav = CollisionTraverser()
		base.cTrav.setRespectPrevTransform(True)
		self.balaCol = CollisionNode("balaCol")
		self.balaCol.setIntoCollideMask(BitMask32.allOff())
		self.balaCol.setFromCollideMask(BitMask32(0x00000001))
		balaColSolid = CollisionSphere(0., 0., 0., .2)
		self.balaCol.addSolid(balaColSolid)
		
		self.pickRay = CollisionNode("pickRay")
		self.pickRayNp = base.camera.attachNewNode(self.pickRay)
		self.pickRay.setIntoCollideMask(BitMask32.allOff())
		self.pickRay.setFromCollideMask(BitMask32(0x00000002))
		self.pickRayCHandler = CollisionHandlerQueue()
		
		self.mouseRay = CollisionRay()
		self.pickRay.addSolid(self.mouseRay)
		self.mouseRay.setOrigin(0, 0, 0)
		
		base.cTrav.addCollider(self.pickRayNp, self.pickRayCHandler)
		
		#~ self.nearPlane = CollisionNode("nearPlane")
		#~ self.nearPlaneNp = base.camera.attachNewNode(self.nearPlane)
		#~ base.camRays.setIntoCollideMask(BitMask32(0x00000001))
		#~ self.nearPlaneNp.setPos(0, 1, 0)
		#~ self.nearPlaneColSolid = CollisionPlane(Plane(Vec3(0, -1, 0), Point3(0, 1, 0)))
		#~ self.nearPlane.addSolid(self.nearPlaneColSolid)
		def giraAvio(task):
			timeVar = globalClock.getDt()
			point = base.win.getPointer(0)
			pointerx = point.getX()
			pointery = point.getY()
			self.mouseRay.setFromLens(base.camNode, pointerx, pointery)
			#Cursors de la pantalla
			self.mirilla.setPos(pointerx, 0, -pointery)
			self.cursorGirar.setPos(pointerx, 0, -pointery)
			r = pow(abs(pointery-self.H_HEIGHT), 2) + pow(abs(pointerx-self.H_WIDTH), 2)
			if r > 8000:
				self.mirilla.hide()
				self.cursorGirar.show()
			else:
				self.mirilla.show()
				self.cursorGirar.hide()
			#3D                     
			pointerx = (pointerx - self.H_WIDTH)
			pointery = (pointery - self.H_HEIGHT)
			
			self.avioR.setX(self.avio, -pointerx*3./float(self.WIN_WIDTH))
			self.avioR.setZ(self.avio, pointery*3./(self.WIN_HEIGHT))
			
			self.avio.setH(self.avio, -pointerx*256./self.WIN_WIDTH*timeVar)
			self.avio.setP(self.avio, -pointery*256./self.WIN_HEIGHT*timeVar)
			
			self.avioR.setR(self.avio, pointerx/10.)
			self.avioR.setP(self.avio, pointery/70.)
			self.avioR.setH(self.avio, -pointerx/50.)

			#~ self.avioVel += self.avioAcc*timeVar
			#~ self.avio.setPos(self.avio, self.avioVel*timeVar)
			return task.cont
			
		def propulsaAvio(acceleracio, task):
			self.avioVel += acceleracio*globalClock.getDt()
			if self.avioVel < self.VEL_MIN_AVIO:
				self.avioVel = self.VEL_MIN_AVIO
			elif self.avioVel > self.VEL_MAX_AVIO:
				self.avioVel = self.VEL_MAX_AVIO
			self.BALA_VEL = self.BALA_VEL_BASE+self.avioVel
			#MOSTRA LA VELOCITAT
			pos = float(self.avioVel-self.VEL_MIN_AVIO)/(self.VEL_MAX_AVIO-self.VEL_MIN_AVIO)
			base.camera.setY(self.CAMERA_Y-pos*4)
			#~ self.marcaVelocitat.setX(MARCAVEL_INI_X+pos*137.)
			return task.cont
		
		self.haCremat = False
		def mouAvio(task):
			timeVar = globalClock.getDt()
			self.avio.setPos(self.avio, 0, self.avioVel*timeVar, 0)
			
			if self.keyMap["shoot"] == 1:
				if self.bulletClock <= 0.:
					self.bulletClock = self.SHOOT_TIME	
					if not self.haCremat:
						if self.overheatClock > 16:
							self.haCremat = True
							self.overheatClock = 18
						else:
							self.overheatClock += self.SHOOT_TIME
							shoot()
					
				else:
					self.bulletClock -= timeVar
			else:
				self.bulletClock = 0.
				self.overheatClock -= timeVar
			if self.overheatClock <16: self.haCremat = False
			if self.haCremat: self.overheatClock -= timeVar
				
			if self.overheatClock < 0:
				self.overheatClock = 0
			elif self.overheatClock < 2:
				self.overheats[0].hide()	
			elif self.overheatClock < 4:
				self.overheats[1].hide()
				self.overheats[0].show()
			elif self.overheatClock < 6:
				self.overheats[2].hide()
				self.overheats[1].show()
			elif self.overheatClock < 8:
				self.overheats[3].hide()
				self.overheats[2].show()
			elif self.overheatClock < 10:
				self.overheats[4].hide()
				self.overheats[3].show()
			elif self.overheatClock < 12:
				self.overheats[5].hide()
				self.overheats[4].show()
			elif self.overheatClock < 14:
				self.overheats[6].hide()
				self.overheats[5].show()
				self.overheats[7].hide()
			elif self.overheatClock < 16:
				self.overheats[7].hide()
				self.overheats[6].show()
			else:
				self.overheats[7].show()				
			
			if self.keyMap["turn"] == 1:
				self.avio.setX(self.avio, -self.VEL_COSTAT*timeVar)
			elif self.keyMap["turn"] == -1:
				self.avio.setX(self.avio, self.VEL_COSTAT*timeVar)
				
			return task.cont
			
		
		def avioRecte(task):
			p = self.avio.getP(render)
			if p>170 or p<-170: return task.cont
			timeVar = globalClock.getDt()
			roll = self.avio.getR(render)
			if roll < -self.VEL_AVIO_RECTE*timeVar:
				self.avio.setR(render, roll+self.VEL_AVIO_RECTE*timeVar)
			elif roll <= self.VEL_AVIO_RECTE*timeVar:
				self.avio.setR(render, 0)
			else:
				self.avio.setR(render, roll-self.VEL_AVIO_RECTE*timeVar)
			return task.cont
			
		self.balaPositiu = True
		def shoot():
			bala = self.particlesDummy.attachNewNode("balaDummy")                        
			balaImage = OnscreenImage(image = "prova/textures/bala.png", parent = bala)
			balaImage.setTransparency(1)
			balaImage.setScale(.1, 1., .2)
			balaImage.setBillboardPointEye()
			bala.setQuat(self.modelAvio.getQuat(render))
			if self.balaPositiu:
				bala.setPos(self.balaDreta.getPos(render))
				self.balaPositiu = False
			else:
				bala.setPos(self.balaEsquerra.getPos(render))
				self.balaPositiu = True
			balaSphere = bala.attachNewNode(self.balaCol)
			balaColHandler = CollisionHandlerQueue()
			base.cTrav.addCollider(balaSphere, balaColHandler)
			#~ if type(self.shootPoint) == 'libpanda.Point3':
				#~ bala.lookAt(self.shootPoint)
			#~ else: bala.setH(bala, 180.)
			taskMgr.add(mouBala, "moubala", extraArgs = [bala, balaImage, self.BALA_VEL, balaColHandler], appendTask = True)
		
		def mouBala(bala, balaImage, vel, queue, task):		
			if task.time > 3:
				balaImage.detachNode()
				expbala = ParticleEffect()
				expbala.reparentTo(self.particlesDummy)
				expbala.loadConfig('explosio.ptf')
				expbala.start(bala)
				taskMgr.doMethodLater(.25, suprimir, "suprimir", extraArgs = [bala, expbala])
				return task.done
			if queue.getNumEntries()!=0:
				balaImage.detachNode()
				entry = queue.getEntry(0)
				bala.setPos(entry.getSurfacePoint(self.particlesDummy))
				expbala = ParticleEffect()
				expbala.reparentTo(self.particlesDummy)
				expbala.loadConfig('explosio.ptf')
				expbala.start(bala)
				taskMgr.doMethodLater(.25, suprimir, "suprimir", extraArgs = [bala, expbala])
				return task.done
			bala.setFluidPos(bala, 0, vel*globalClock.getDt(), 0)
			balaImage.setR(balaImage, 1000*globalClock.getDt())
			return task.cont

		def suprimir(bala, expbala):
			bala.detachNode()
			expbala.cleanup()
			expbala.detachNode()
		
		def setKey(key, value):
			self.keyMap[key] = value
		
		def centraRatoli():
			point = base.win.getPointer(0)
			x = point.getX()
			y = point.getY()
			x -= self.H_WIDTH
			y -= self.H_HEIGHT
			r = sqrt(pow(abs(y), 2) + pow(abs(x), 2))
			def centra(t, x, y):
				base.win.movePointer(0, trunc(x*t)+self.H_WIDTH, trunc(y*t)+self.H_HEIGHT)
			
			i = LerpFunc(centra,
				fromData=1.,
				toData=0.,
				duration=r/700.,
				blendType='easeInOut',
				extraArgs=[x, y],
				name="centraRata")
			i.start()
		
		
		self.previousPos = 0
		self.interval01 = LerpPosHprInterval(self.modelAvio, .5, Point3(3, 0, 0),
				VBase3(0, 0, 70), Point3(0, 0, 0),
				VBase3(0, 0, 0), blendType='easeInOut')
		self.interval10 = LerpPosHprInterval(self.modelAvio, .5, Point3(0, 0, 0),
				VBase3(0, 0, 0), Point3(-3, 0, 0),
				VBase3(0, 0, -70), blendType='easeInOut')
		self.interval02 = LerpPosHprInterval(self.modelAvio, .5, Point3(-3, 0, 0),
				VBase3(0, 0, -70), Point3(0, 0, 0),
				VBase3(0, 0, 0), blendType='easeInOut')
		self.interval20 = LerpPosHprInterval(self.modelAvio, .5, Point3(0, 0, 0),
				VBase3(0, 0, 0), Point3(3, 0, 0),
				VBase3(0, 0, 70), blendType='easeInOut')
		self.interval12 = LerpPosHprInterval(self.modelAvio, 1., Point3(-3, 0, 0),
				VBase3(0, 0, -70), Point3(3, 0, 0),
				VBase3(0, 0, 70), blendType='easeInOut')
		self.interval21 = LerpPosHprInterval(self.modelAvio, 1., Point3(3, 0, 0),
				VBase3(0, 0, 70), Point3(-3, 0, 0),
				VBase3(0, 0, -70), blendType='easeInOut')
				
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
			
		def anim1():
			self.mirilla.find('**/+SequenceNode').node().setPlayRate(1.)
			self.mirilla.find('**/+SequenceNode').node().play(0, 3)
		def anim2():
			self.mirilla.find('**/+SequenceNode').node().setPlayRate(1.)
			self.mirilla.find('**/+SequenceNode').node().play(4, 8)
		def anim3():
			self.mirilla.find('**/+SequenceNode').node().setPlayRate(-1.)
			self.mirilla.find('**/+SequenceNode').node().play(0, 3)
		def anim4():
			self.mirilla.find('**/+SequenceNode').node().setPlayRate(-1.)
			self.mirilla.find('**/+SequenceNode').node().play(3, 8)
		#events
		self.accept(self.QUIT_KEY, sysExit, [0])
		self.accept(self.ACCELERATE_KEY, taskMgr.add, [propulsaAvio, "propulsaAvio1", None, [self.ACCELERACIO], None, None, True])
		self.accept(self.ACCELERATE_KEY+"-up", taskMgr.remove, ["propulsaAvio1"])
		
		self.accept(self.DECELERATE_KEY, taskMgr.add, [propulsaAvio, "propulsaAvio2", None, [-self.ACCELERACIO], None, None, True])
		self.accept(self.DECELERATE_KEY+"-up", taskMgr.remove, ["propulsaAvio2"])
		
		for key in self.SHOOT_KEYS:
			self.accept(key, setKey, ["shoot", 1])
			self.accept(key+"-up", setKey, ["shoot", 0])
		
		self.accept(self.RIGHT_KEY, setKey, ["turn", -1])
		self.accept(self.LEFT_KEY, setKey, ["turn", 1])
		self.accept(self.RIGHT_KEY+"-up", setKey, ["turn", 0])
		self.accept(self.LEFT_KEY+"-up", setKey, ["turn", 0])
		
		self.accept(self.CENTRA_RATA_KEY, centraRatoli)
		
		self.accept("n", anim1)
		self.accept("m", anim2)
		self.accept("v", anim3)
		self.accept("b", anim4)
		
		taskMgr.add(giraAvio, "GiraAvio")
		taskMgr.add(mouAvio, "MouAvio")
		taskMgr.add(avioRecte, "avioRecte")
		taskMgr.add(tombaAvio, "tombaAvio")
		
class JocAvions(ShowBase):
	FULLSCREEN = False
	
	WIN_WIDTH = 800
	H_WIDTH = WIN_WIDTH/2
	WIN_HEIGHT = 600
	H_HEIGHT = WIN_HEIGHT/2
	
	def __init__(self):
		ShowBase.__init__(self)
		#Coses de propietats, colors, etc.
		
		while base.win.isClosed(): pass
		props = WindowProperties()
		props.setTitle("Joc Avions v.alfa")
		props.setSize(self.WIN_WIDTH, self.WIN_HEIGHT)
		props.setFixedSize(True)
		props.setCursorHidden(True)
		#~ props.setUndecorated(True)
		props.setFullscreen(self.FULLSCREEN)
		base.win.requestProperties(props)
		
		self.terreny = base.loader.loadModel('prova/Terreny/terrenysimple.egg')
		self.terreny.setScale(5)
		self.terreny.reparentTo(render)
		self.terrenyCol = self.terreny.find("**/Colisio")
		self.terrenyCol.node().setIntoCollideMask(BitMask32(0x00000001))
		
		mat = Material()
		mat.setDiffuse(VBase4(0.5, 1, 0, 1))
		mat.setAmbient(VBase4(0.5, 1, 0, 1))
		mat.setShininess(0.5)
		self.terreny.setMaterial(mat)
		
		gingerMan = base.loader.loadModel('prova/gingerbreadMan.egg')
		gingerMan.reparentTo(render)
		gingerMan.find("**/Colisio").node().setIntoCollideMask(BitMask32(0x00000003))
		int1 = gingerMan.posInterval(10,
				Point3(-10, -10, 500),
				startPos=Point3(10, 10, 500))
		int2 = gingerMan.posInterval(10,
				Point3(10, 10, 500),
				startPos=Point3(-10, -10, 500))
				
		seq = Sequence(int1, int2, name="sequenciaGingerMan")
		seq.loop()

		dlight = DirectionalLight('dlight')
		dlightnp = render.attachNewNode(dlight) 
		dlightnp.setHpr(10, -45, 0)
		render.setLight(dlightnp)
		
		expfog = Fog("Scene-wide exponential Fog object")
		expfog.setColor(126/255., 240/255., 1.)
		self.setBackgroundColor(126/255., 240/255., 1.)
		expfog.setExpDensity(0.001)
		render.setFog(expfog)
		jugador = Jugador(self)
JocAvions()
run()
