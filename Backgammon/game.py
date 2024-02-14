""" To run the programme, type "Python game.py" """

import sys
import time
import ctypes
import _thread
import socket
import logging

import pygame as pg

from menus import *
from game_ui import GameUI
from logic import GameLogic
from utils import Mouse
from MainClient import MainClient
from server import Server
from settings import *

class Game:
    def __init__(self, render_resolution):
        #Initializes game window, clock, mouse util and menu views
        self.render_resolution = render_resolution
        ctypes.windll.user32.SetProcessDPIAware() # Ignore
        #Initializes screen and clock
        self.screen = pg.display.set_mode(self.render_resolution)
        self.clock = pg.time.Clock()
        #Creates mouse utility
        self.mouse = Mouse(RESOLUTION, self.render_resolution)
        pg.display.set_caption("Backgammon")
        #Initializes menus
        self.reset_views()
        self.back_to_menu()

    def reset_views(self):
        self.menu = GameMenu(self)
        self.connectionmenu = SelectConnectionMenu(self)
        self.hostmenu = HostMenu(self)
        self.guestmenu = GuestMenu(self)
        self.gamelogic = GameLogic()
        self.gameui = GameUI(self)
        self.gameovermenu = GameoverMenu(self)
    
        self.server = None
        self.MainClient = None
        self.finished = False

    def back_to_menu(self):
        #Switches current view to title menu
        #Stops MainClient-server connections if created
        if self.server is not None:
            self.server.stop()
            self.server = None
        if self.MainClient is not None:
            self.MainClient.stop()
    
        self.reset_views()
        #Switches view
        self.current_view = self.menu

    def run(self):
        #Handles the main game loop
        self.running = True
        while self.running:
            #Limits refresh rate
            dt = self.clock.tick(FPS)
            #Checks for user inputs
            self.check_events()
            #Handles current view
            self.handle_view(self.current_view)
            
            pg.display.flip()

        #Quits
        pg.quit()
        sys.exit()

    def quit(self):
        self.running = False

    def check_events(self):
        #Checks for keyboard inputs.
        for event in pg.event.get():
            #Closing window
            if event.type == pg.QUIT:
                self.quit()
            #Keyboard inputs
            elif event.type == pg.KEYUP:
                #Quits if pressing ESC
                if event.key == pg.K_ESCAPE:
                    self.quit()
                #Handles input for connection menu
                self.handle_connection_input(event)

    def handle_connection_input(self, event):
        #Handles guest menu inputs
        if self.current_view == self.guestmenu:
            current_label = self.guestmenu.labels[self.guestmenu.l]

            # If user is pressing a digit or a dot
            if event.key in self.guestmenu.DIGITS_KEY_CODES:
                # Updates IP/Port label
                # Updates label text by mapping event.key to a char
                char = self.guestmenu.DIGITS_KEY_CODES[event.key]
                updated_text = current_label.text + char
                current_label.update_text(updated_text)
            # If user wants to delete digits
            elif event.key == pg.K_BACKSPACE:
                # If text > label base text length
                base_length =  self.guestmenu.lengths[self.guestmenu.l]
                if len(current_label.text) > base_length:
                    # Removes last char
                    current_label.update_text(current_label.text[:-1])
                else:
                    # Switches to IP input
                    self.guestmenu.l = 1
            # If user wants to switch to Port input
            elif event.key == pg.K_RETURN:
                self.guestmenu.l = 2

    def get_server_data_from_labels(self, addr, port):
        return (addr.text.split(" ")[-1],
            port.text.split(" ")[-1].replace(".", ""))

    def handle_view(self, view):
        view.update(self.mouse)

        surface = view.get_surface()
        self.blit_view(surface)

    def blit_view(self, surface):
        resized_surface = pg.transform.smoothscale(
            surface, self.render_resolution)
        self.screen.blit(resized_surface, (0, 0))

    def choose_connection(self):
        self.current_view = self.connectionmenu
        
    def play_as_guest(self):
        self.current_view = self.guestmenu

    def play_as_host(self):
        #Getting local IP address and creating the server
        local_address = socket.gethostbyname(socket.gethostname())
        port = 5555
        self.server = Server(local_address, port)
        if not self.server.start():
            #If the server didn't start, shows error
            self.server = None
            return self.connectionmenu.show_host_error()
        #Starts thread to run server loops
        _thread.start_new_thread(self.host, (self.server,))
        #Updates host menu label then switches view to it
        self.address, self.port = local_address, port
        self.hostmenu.labels[0].update_text(
            f"Hosting on {local_address}, {port}")
        self.current_view = self.hostmenu

    def host(self, server):
        try:
            self.server.handle_connections()
            self.server.set_starting_player()
            self.server.game_loop()
        except Exception as error:
            logging.error(f"SERVER - {error}")
            #If the match is not over, the client has disconnected
            if not self.finished:
                #Switches to endgame view
                self.current_view = self.gameovermenu
                # Shows lost connection error
                self.current_view.lost_connection_error("MainClient")

    def start_playing(self):
        #If the user is joining as guest
        if self.server is None:
            #If the user didn't enter IP address or port
            if self.guestmenu.no_input():
                return
            #Getting IP/Port from labels
            host, port = self.get_server_data_from_labels(
                self.guestmenu.labels[1],
                self.guestmenu.labels[2]
            )
        #If user is joining as host
        else:
            #Using cached server IP/Port to join
            host = self.address
            port = self.port

        self.last_command = "hold"
        #Creates the MainClient
        self.MainClient = MainClient(host, int(port), self)
        if not self.MainClient.connected:
            self.current_view.failed_connection_error()
            return
        #Starts thread to communicate with server
        _thread.start_new_thread(self.receive_commands, ())
        #Setting player number as joining order
        self.gameui.player_number = self.MainClient.position

        if self.gameui.player_number == 0:
            self.gameui.game_state = self.gamelogic.get_state()
        else:
            points, bar, scores = self.gamelogic.get_state()
            #Reversing game points to show flipped version of the game
            self.gameui.game_state = points[::-1], bar, scores

        self.gameui.labels[1].update_text(
            f"Player {self.gameui.player_number + 1}")

        self.current_view = self.gameui

    def receive_commands(self):
        try:
            while True:
                #Gets commands from server
                self.last_command = self.MainClient.receive_commands()
                #Updating tips label according to command received
                self.gameui.labels[0].update_text(
                    self.gameui.TIPS.get(self.last_command, "")
                )
        except Exception as error:
            logging.error(f"MainClient - {error}")
            #If the game is not over
            if not self.finished:
                self.current_view = self.gameovermenu
                #Shows lost connection error
                self.current_view.lost_connection_error("host")

if __name__ == "__main__":
    backgammon = Game((960, 540))
    backgammon.run()