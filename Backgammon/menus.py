import _thread

import pygame as pg

from ui_elements import View, Button, Label
from settings import *

class GameMenu(View):
    def __init__(self, game):
        super().__init__(game)
        self.font = pg.font.Font("TheanoOldStyle-Regular.ttf", 100)

        self.buttons = [
            Button(
                (500, 700),
                (200, 100),
                text="Play",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=80,
                external=True,
                click_callback=self.game.choose_connection
            ),
            Button(
                (1230, 700),
                (200, 100),
                text="Quit",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=80,
                external=True,
                click_callback=self.game.quit
            )
        ]

    def draw_title(self):
        """Draws game title."""
        text = self.font.render("Backgammon", True, 'black')
        text_rect = text.get_rect(
            center=(RESOLUTION[0]//2, RESOLUTION[1]//2))

        self.view.blit(text, text_rect)

    def refresh(self):
        self.view.fill('white')
        self.draw_title()
        self.draw_buttons()

class SelectConnectionMenu(View):
    def __init__(self, game):
        super().__init__(game)
        self.labels = [
            Label(
                (960, 540),
                text="Play as",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=90,
                external=True
            )
        ]

        self.buttons = [
            Button((500, 700), (200, 100),
                    text="Host",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=80,
                    external=True,
                    click_callback=self.game.play_as_host),
            Button((1230, 700), (200, 100),
                    text="Guest",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=80,
                    external=True,
                    click_callback=self.game.play_as_guest),
            Button((900, 100), (200, 100),
                    text="Back",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=50,
                    external=True,
                    click_callback=self.game.back_to_menu),
        ]

    def show_host_error(self):
        """Shows text if error occured during server creation."""
        self.labels.append(
            Label(
                (960, 850),
                text="Failed creating host server",
                color="red",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=50,
                external=True
            ),
        )

class HostMenu(View):
    def __init__(self, game):
        super().__init__(game)
        self.labels = [
            Label(
                (960, 540),
                text="",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=80,
                external=True,
                dynamic=True
            )
        ]

        self.buttons = [
            Button((880, 700), (200, 100),
                    text="Join",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=80,
                    external=True,
                    click_callback=lambda: _thread.start_new_thread(
                    self.game.start_playing, ())),
            Button((900, 100), (200, 100),
                    text="Back",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=50,
                    external=True,
                    click_callback=self.game.back_to_menu),
        ]
    
    def failed_connection_error(self):
        """Shows text if error occured joining match."""
        self.labels.append(
            Label(
                (960, 750),
                text="Failed connecting to host",
                color="red",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=50,
                external=True
            ),
        )

class GuestMenu(View):
    DIGITS_KEY_CODES = {
        pg.K_0: "0",
        pg.K_1: "1",
        pg.K_2: "2",
        pg.K_3: "3",
        pg.K_4: "4",
        pg.K_5: "5",
        pg.K_6: "6",
        pg.K_7: "7",
        pg.K_8: "8",
        pg.K_9: "9",
        pg.K_PERIOD: ".",
    }
    def __init__(self, game):
        super().__init__(game)
        self.labels = [
            Label(
                (960, 360),
                text="Connect to Host",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=80,
                external=True
            ),
            Label(
                (960, 550),
                text="IP Address: ",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=60,
                external=True,
                dynamic=True
            ),
            Label(
                (960, 650),
                text="Port: ",
                color="black",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=60,
                external=True,
                dynamic=True
            ),
        ]

        self.buttons = [
            Button((870, 800), (200, 100),
                    text="Join",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=80,
                    external=True,
                    click_callback=lambda: _thread.start_new_thread(
                        self.game.start_playing, ())),
            Button((900, 100), (200, 100),
                    text="Back",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=50,
                    external=True,
                    click_callback=self.game.back_to_menu),
        ]
        self.l = 1
        self.lengths = {
            1: 12,
            2: 6
        }

    def failed_connection_error(self):
        """Shows text if error occured joining server."""
        self.labels.append(
            Label(
                (960, 750),
                text="Failed connecting to host",
                color="red",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=50,
                external=True
            ),
        )
    
    def no_input(self):
        return any(
            len(self.labels[i].text) == self.lengths[i] for i in [1, 2] 
        )

class GameoverMenu(View):
    def __init__(self, game):
        super().__init__(game)
        self.labels = [
            Label(
                (960, 540),
                text="",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=80,
                external=True,
                dynamic=True
            )
        ]

        self.buttons = [
            Button((860, 700), (200, 100),
                    text="Menu",
                    font_family="TheanoOldStyle-Regular.ttf",
                    font_size=80,
                    external=True,
                    click_callback=self.game.back_to_menu),
        ]

    def show_winner(self, player):
        """Shows winner name."""
        self.labels[0].update_text(f"Player {player + 1} wins!")
        self.game.finished = True
        if self.game.server:
            self.game.server.stop()
        else:
            self.game.MainClient.stop()
    
    def lost_connection_error(self, to="host"):
        """Shows text if connection was lost."""
        self.labels[0].update_text(f"Lost connection to {to}.")