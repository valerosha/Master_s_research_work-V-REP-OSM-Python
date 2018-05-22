from vrep_bridge import vrep # for vrep functions
import logging
import colorlog 
from enum import IntEnum
import time 
import numpy # for matrix multiplication (rotation matrix)
from math import sin, cos # for rotation matrix

class SignalType(IntEnum):

    getState = 1
    setState = 2

class IndexSignalSend(IntEnum):

    type   = 0
    uid    = 1
    motion = 2
    led_r  = 3
    led_g  = 4
    led_b  = 5


class IndexSignalReceive(IntEnum):


    uid             = 0
    ambient_light   = 1

class Motion(IntEnum):

    
    stop    = 0
    forward = 1
    left    = 2
    right   = 3


class Led_rgb():

    red       = [3, 0, 0]
    green     = [0, 3, 0]
    blue      = [0, 0, 3]
    white     = [3, 3, 3]
    turquoise = [0, 3, 1]
    orange    = [3, 3, 0]
    magenta   = [3, 0, 3]
    cyan      = [0, 3, 3]
    yellow    = [3, 3, 0]


class SpawnType(IntEnum):

    ox_plus      = 1
    oy_plus      = 2
    circular     = 3



SpawnTypeNames = {
    "ox_plus": SpawnType.ox_plus,
    "oy_plus": SpawnType.oy_plus,
    "circular": SpawnType.circular
}

def getClonePosRot(stepNr, nr, spawnType = SpawnType.ox_plus):
    # Функця для получения позиции вновь созданного робота (клона)
    position = [0] * 3
    rotation = [0] * 3

    if (spawnType == SpawnType.ox_plus):
        position = [(stepNr + 1) * 0.05, 0, 0]
        rotation = [0, 0, 0]
    elif (spawnType == SpawnType.oy_plus):
        position = [0, (stepNr + 1) * 0.05, 0]
        rotation = [0, 0, 0]
    elif (spawnType == SpawnType.circular):
        angle = numpy.radians((stepNr / (nr)) * 360)
        rot_matrix = numpy.array([  [cos(angle), -sin(angle)], [sin(angle), cos(angle)] ])
        pos = numpy.dot(numpy.array([0, 0.061 * (nr / 10)]), rot_matrix)
        position = list(pos) + [0]
        rotation = [0, 0, 0]

    return position, rotation


class VrepBridge():

	# Конструктор класса, реализуем связывание Python and V-REP 

    def __init__(self):
         
        self.clonedRobotHandles = [] # used to store object handles of copy-pasted robots
        logging.info('Attempting to connect')
        vrep.simxFinish(-1) # just in case, close all opened connections
        self.__clientID = vrep.simxStart('127.0.0.1', 19997, True, True, 5000, 5) # Connect to V-REP

        if (self.__clientID == -1):
            logging.error('Failed connecting to remote API server')
            raise()

        logging.info('Connected to remote API server, clientID = %d' % self.__clientID)


    def __waitForCmdReply(self):
        while True:
            result,string=vrep.simxReadStringStream(self.__clientID, 'reply_signal', vrep.simx_opmode_streaming)
            if (result == vrep.simx_return_ok and len(string) > 0)
                return string


    def sendSignal(self, params):
"
		#Отправляем сгенерированные данные в симулятор 
        packedData=vrep.simxPackInts(params)
        
        vrep.simxWriteStringStream(self.__clientID, "signal", packedData, vrep.simx_opmode_oneshot) 
        logging.debug("Sent %s" % params)
        reply = self.__waitForCmdReply()

        return reply


    def getState(self, uid):
	# Получаем позицию робота 
        send = [-1] * 2 # initialize an array with -1
        send[IndexSignalSend.type] = SignalType.getState
        send[IndexSignalSend.uid] = uid

        logging.debug("getState() robot_uid = %d" % uid)

        # get a reply of the form [uid, ambient_light] | distance_keys | distance_values
        recv = self.sendSignal(send)
        #logging.debug("Received %s" % recv)
        recv = recv.split(b'|')
        for i in range(len(recv)):
            # unpack ints in place
            recv[i] = vrep.simxUnpackInts(recv[i])
            logging.debug("recv[%d] = %s" % (i, recv[i]))
        
        if (recv[0][IndexSignalReceive.uid] != uid):
            logging.critical("received the state from the wrong robot (req.uid = %d, response.uid = %d)" % (uid, recv[0][IndexSignalReceive.uid]))
            exit(1)

        # construct the distances dictionary (robot_uid: current_distance)
        distances = {recv[1][i]: recv[2][i] for i in range(len(recv[1]))}
        # remove distance from myself, as it is always 0 and is not needed
        del distances[uid]

        return {
                'uid' : recv[0][IndexSignalReceive.uid],
                'light' : recv[0][IndexSignalReceive.ambient_light],
                'distances' : distances}
    #end getState()

    def setState(self, uid, motion, light):

		# Задаем текущее положение робота
        send = [-1] * 6
        send[IndexSignalSend.type] = SignalType.setState
        send[IndexSignalSend.uid] = uid
        send[IndexSignalSend.motion] = motion
        send[IndexSignalSend.led_r] = light[0]
        send[IndexSignalSend.led_g] = light[1]
        send[IndexSignalSend.led_b] = light[2]

        recv = vrep.simxUnpackInts(self.sendSignal(send))


    def spawnRobots(self, sourceRobotName = "Kilobot#", nr = 2, spawnType = SpawnType.ox_plus):
		# Функция для создания роботов
        returnCode, sourceHandle = vrep.simxGetObjectHandle(self.__clientID, sourceRobotName, vrep.simx_opmode_oneshot_wait)

       #В цикле создаем роботов равное 
	   for i in range(nr): nr
            
            returnCode, auxhandles = vrep.simxCopyPasteObjects(self.__clientID, [sourceHandle], vrep.simx_opmode_oneshot_wait)
            self.clonedRobotHandles.append(auxhandles[0])
            # Получаем позицию созданного робота
            position, rotation = getClonePosRot(i, nr, spawnType)
            # Переносим созданного робота на другую позцию
            vrep.simxSetObjectPosition(self.__clientID, self.clonedRobotHandles[-1], sourceHandle, position, vrep.simx_opmode_oneshot_wait)
            # Поворачиваем робота 
            vrep.simxSetObjectOrientation(self.__clientID, self.clonedRobotHandles[-1], self.clonedRobotHandles[-1], rotation, vrep.simx_opmode_oneshot_wait)

   
    def removeRobots(self):
        #Функция для удаления созданных (склонированных) роботов
        #Если сцена пустая
        if (len(self.clonedRobotHandles) <= 0):
            return;

        for handle in self.clonedRobotHandles: 
            vrep.simxRemoveModel(self.__clientID, handle, vrep.simx_opmode_oneshot_wait)

    
    def close(self):
        # Закрываем соединение 
        vrep.simxFinish(self.__clientID)
        logging.info("Connection closed")


if __name__ == "__main__":

    bridge = VrepBridge()
    bridge.spawnRobots(nr = 10, spawnType = SpawnType.circular)

    bridge.getState(0)
    bridge.setState(0, Motion.forward, [0, 2, 0])

    bridge.getState(1)
    bridge.setState(1, Motion.left, [2, 0, 0])

    bridge.getState(2)
    bridge.setState(2, Motion.right, [0, 0, 2])
    time.sleep(5)
    bridge.removeRobots()
    bridge.close()