import socket
import logging

from utils import Serialization

class MainClient:
    #command mappings
    COMMANDS = {
        0: "hold",
        1: "roll",
        2: "singleroll",
        3: "acceptint",
        4: "move",
        5: "acceptstate"
    }
    def __init__(self, address, port, game):
        self.position = 0
        self.game = game

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = self.connect(address, port)

    def connect(self, address, port):
        try:
            self.connection.connect((address, port))
            # Receives joining position from server,
            # decoding data (sockets transfer bytes data)
            self.position = int.from_bytes(
                self.connection.recv(1), 'big')
            logging.info(f"MainClient - Connected to ({address}, {port}) as player {self.position}.")
            return True
        except Exception as e:
            logging.error(f"MainClient - {e}")
            return False

    def stop(self):
        #Closing a socket throws an error
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            logging.info(f"MainClient - MainClient stopped.")
            self.connection.close()

    def receive_commands(self):
        last_command = None
        #Tries to get 1 byte worth of data from buffer
        data = self.connection.recv(1)
        #If data was sent
        if data:
            #Updating last command according to mappings,
            #decoding bytes data 
            last_command = self.COMMANDS[int.from_bytes(data, byteorder='big')]
            #If MainClient is listening for opponent dice rolls values
            if last_command == "acceptint":
                #Updating dice values, listens for 2 bytes max
                #(a 4-6 dice roll is encoded as '46')
                self.set_dice(self.connection.recv(2))
            #If MainClient is listening for changes in the game state
            elif last_command == "acceptstate":
                #Gets first byte from the buffer, this encodes the length
                #of the serialized game state 
                lentgh = int.from_bytes(self.connection.recv(1), 'big')
                #Getting length bytes worth of data 
                raw_state = self.connection.recv(lentgh)
                #Updating game state
                self.set_state(raw_state)

            logging.info(f"MainClient - Received '{last_command}'.")

        return last_command

    def send_data(self, data, length=1, log=True):
        #Encoding and sending data based on its type
        if type(data) is int:
            self.connection.send(int.to_bytes(data, length, 'big'))
        elif type(data) is str:
            self.connection.send(str.encode(data))
        elif type(data) is bytes:
            self.connection.send(data)
        
        if type(log) is str:
            logging.info(f"MainClient - Sending {log}.")
        else:
            logging.info(f"MainClient - Sending {data}.")

    def set_dice(self, raw_dice):
        self.game.gameui.dice_draw = [int(x) for x in raw_dice.decode()]
        self.game.gameui.used_dice_draws = []

    def set_state(self, raw_state):
        state = Serialization.bytes_to_list(raw_state)
        self.game.gameui.game_state = state
        #Updating opponent's score
        opp = int(not self.position)
        opp_score = state[2][opp]
        #Updating score label
        self.game.gameui.labels[3].update_text(str(opp_score))