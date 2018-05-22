from vrep_bridge import vrep # for vrep functions
from pyrep.vrep.vrep import simxLoadScene
from pyrep.vrep import vrep as v
from pyrep.common import ReturnCommandError


	
class VrepBridgLoad():

	# Конструктор класса, реализуем связывание Python and V-REP 
	
    def __init__(self):
         
        logging.info('Attempting to connect')
        vrep.simxFinish(-1) # just in case, close all opened connections
        self.__clientID = vrep.simxStart('127.0.0.1', 19997, True, True, 5000, 5) 

        if (self.__clientID == -1):
            logging.error('Failed connecting to remote API server')
            raise()

        logging.info('Connected to remote API server, clientID = %d' % self.__clientID)
		
	def loadScene(self,path):
        clientID=self.id
        res = simxLoadScene(clientID, path, 0xFF, self._def_op_mode)
        print(res)

        if res != v.simx_return_ok:
            raise ReturnCommandError(res)	
		
    def close(self):
        # Закрываем соединение 
        vrep.simxFinish(self.__clientID)
        logging.info("Connection closed")		
		
if __name__ == "__main__":


    bridge = VrepBridge()	
	
	#Указываем путь сцены
	scene_path = '/scenes/Pioneer.ttt'
	
	#Вызываем необходимый метод
	bridge.loadScene(scene_path)
	
	# Закрываем соединение 
	bridge.close()
	
