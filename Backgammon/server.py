import socket
import logging

from utils import Serialization

class Server:
    """A class to represent the server in a MainClient-server connection."""
    MAX_CONNECTIONS = 2
    # Command to int mappings
    COMMANDS = {
        "hold": (0).to_bytes(1, 'big'),
        "roll": (1).to_bytes(1, 'big'),
        "singleroll": (2).to_bytes(1, 'big'),
        "acceptint": (3).to_bytes(1, 'big'),
        "move": (4).to_bytes(1, 'big'),
        "acceptstate": (5).to_bytes(1, 'big')
    }
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = []

    def start(self):
        try: 
            # Binds to given (IP address, port)
            self.server.bind((self.address, self.port))
            # Listens to incoming connections
            self.server.listen(self.MAX_CONNECTIONS)
        except Exception as e:
            logging.error(f"SERVER - {e}")
            return False
        else:
            logging.info(
                f"SERVER - Server started on ({self.address}, {self.port}).")
            return True

    def stop(self):
        #Closing the socket throws an error
        try:
            self.server.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            logging.info(f"SERVER - Server stopped.")
            self.server.close()

    def handle_connections(self):
        for _ in range(self.MAX_CONNECTIONS):
            #Waits for a client to connect
            conn, addr = self.server.accept()
            self.clients.append((conn, addr))
            #Sending to client its join position
            #0 for first player, 1 for second player
            conn.send((len(self.clients) - 1).to_bytes(1, 'big'))
            #Sending hold command
            conn.send(self.COMMANDS["hold"])
            logging.info(f"SERVER - MainClient {addr} connected.")

    def set_starting_player(self):
        logging.info(
            f"SERVER - Setting first player, waiting for dice rolls..")
        same_value = True
        #Loops if the two players get the same value
        while same_value:
            max_val = 0
            same_value = False
            #For each client
            for i, (player, addr) in enumerate(self.clients):
                #Sending single roll command
                player.send(self.COMMANDS["singleroll"])
                data = None
                #Loops until client sends dice roll data
                while True:
                    #Listens for 2 bytes worth of data
                    #representing dice rolls values
                    data = player.recv(2)
                    if data:
                        decoded = data.decode()
                        #If client sends 0, its turn is over
                        if int(decoded) == 0:
                            break
                        #Getting only last value
                        val = int(decoded[-1])
                        other_player = (i + 1) % len(self.clients)
                        #Sending other player command to accept dice values
                        other_player_conn = self.clients[other_player][0]
                        other_player_conn.send(self.COMMANDS["acceptint"])
                        #Sending data to other player
                        other_player_conn.send(data)
                        logging.info(f"SERVER - Received {val} from {addr}.")

                #Compares values
                if val == max_val:
                    same_value = True
                else:
                    same_value = False
                if val > max_val:
                    starting_player = player, addr
                    max_val = val
                
                player.send(self.COMMANDS["hold"])
                logging.info(f"SERVER - Player {i} draw: {val}.")

        #Repositions clients in list
        starting_player_obj = self.clients.pop(
            self.clients.index(starting_player))
        self.clients.insert(0, starting_player_obj)
        logging.info(
            f"SERVER - Setting {starting_player[1]} as starting player.")

    def game_loop(self):
        gameover = False
        while not gameover:
            #For each player, handle its turn
            for i, (player, addr) in enumerate(self.clients):
                #Sends roll command to current player
                player.send(self.COMMANDS["roll"])
                #Sends hold command to other player
                other_player, _ = self.clients[(i + 1) % len(self.clients)]
                other_player.send(self.COMMANDS["hold"])

                #Handles dice rolls for current player
                draws = self.handle_dice_rolls(player, addr, i)
                logging.info(f"SERVER - Player {i} draw: {draws}.")

                #Sends move command to current player
                player.send(self.COMMANDS["move"])
                #Loop to give updated version of game state to other player
                while True:
                    # Getting 1 bytes worth of data from buffer
                    data = player.recv(1)
                    if data:
                        #The first byte encodes the length
                        #of the serialized game state
                        length = int.from_bytes(data, 'big')
                        #If the first byte is a 0, the turn is over
                        if length == 0: break
                        #Getting length bytes worth of data
                        gamestate = player.recv(length)
                        #Deserializes received serialized game state 
                        deserialized = Serialization.bytes_to_list(gamestate)
                        logging.info(f"SERVER - Received state: {deserialized} from {addr}.")

                        #Re-serializes game state, reversing points
                        #(and bar) to show flipped game board to other player
                        serialized, length = Serialization.list_to_bytes(
                            [deserialized[0][::-1], deserialized[1][::-1], deserialized[2]])
                        #Sends accept state command to other player
                        other_player.send(self.COMMANDS["acceptstate"])
                        #Sends first byte as length of the
                        #flipped game state, finally sending the state
                        other_player.send(length.to_bytes(1, 'big'))
                        other_player.send(serialized)

    def handle_dice_rolls(self, player, addr, i):
        """Loops to send given player dice values to other player."""
        #See set_starting_player's while True loop
        data = None
        while True:
            data = player.recv(2)
            if data:
                decoded = data.decode()
                if int(decoded) == 0:
                    break
                vals = list(int(x) for x in decoded)
                other_player = (i + 1) % len(self.clients)
                other_player_conn = self.clients[other_player][0]
                other_player_conn.send(self.COMMANDS["acceptint"])
                other_player_conn.send(data)
                logging.info(f"SERVER - Received {vals} from {addr}.")

        return vals