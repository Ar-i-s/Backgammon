import _thread
import pygame as pg
from pygame import gfxdraw
import logging
from ui_elements import View, Button, Label
from utils import Serialization
from settings import *
class GameUI(View):
    #Creation and positioning of the Board. 
    
    SIZEOFBOARD = 1240, 860
    BASECOLOR = (183, 184, 183)
    FRAMESIZE = round(SIZEOFBOARD[0] * 1 / 38)
    FRAMECOLOR = (0, 110, 38)
    POINTHEIGHT = round(
        2 / 5 * (SIZEOFBOARD[1] - 2 * FRAMESIZE))
    BOARD_POINTWIDTH = (SIZEOFBOARD[0] // 2 - 2 * FRAMESIZE) # // npoints // 4
    BOARD_HOMEPOINTCOLOR = (255, 255, 255)
    BOARD_AWAYPOINTCOLOR = (1, 161, 56)
    BOARD_HOVERPOINTALPHA = 80
    BOARD_HOVERPOINTCOLOR = (255, 255, 255)
    BOARD_HOVEREDPOINTBORDER = 4


    #Creation of the Checkers and the Triangle home bases. 
    CHECKER_AWAYCOLOR = (0, 5, 5)
    CHECKER_HOMECOLOR = (51, 255, 241)
    CHECKER_RADIUS = 28
    CHECKER_YOFFSET = 36
    CHECKER_AREASIZE = 110, 110
    CHECKER_SELECTEDBORDER = 3
    CHECKER_SELECTEDALPHA = 120

    #Creation of the Dice and its color. 
    DIE_SIZE = 60
    DIE_POS = SIZEOFBOARD[0] * 1 / 4, SIZEOFBOARD[1] // 2 - DIE_SIZE // 2
    DIE_COLOR = (254, 246, 225)
    DIE_DOTCOLOR = (84, 44, 30)
    DIE_DOTRADIUS = round(DIE_SIZE // (3 * 2) * 1 / 2)
    DIE_DOTS = {
        1: [(1, 1)],
        2: [(0, 2), (2, 0)],
        3: [(0, 2), (1, 1), (2, 0)],
        4: [(0, 0), (2, 0), (0, 2), (2, 2)],
        5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
        6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)]
    }
    DICE_XDISTANCE = 80
    DIE_DOTSOFFSET = (DIE_SIZE * 3 / 4) // 3
    
    DIE_ANIMATION_NUMROLLS = 3
    DIE_ANIMATION_SINGLEROLLFRAMES = 5
    BEAROFFBUTTON_POS = (
        RESOLUTION[0] // 2 + SIZEOFBOARD[0] // 2 + 100,
        round(RESOLUTION[1] * 3 / 4))
    BEAROFFBUTTON_SIZE = 100, 100
    BEAROFFBUTTON_COLOR = "black"
    BEAROFFBUTTON_BORDER = 3
    BEAROFFBUTTON_RADIUS = 12

    TIPS_LABELPOS = RESOLUTION[0] // 2, 50
    PLAYERNUMBER_LABELPOS = RESOLUTION[0] // 2, RESOLUTION[1] - 50
    PLAYERSCORE_LABELPOS = (BEAROFFBUTTON_POS[0] + BEAROFFBUTTON_SIZE[0] // 2,
                            BEAROFFBUTTON_POS[1] + BEAROFFBUTTON_SIZE[1] // 2)
    OPPONENTSCORE_LABELPOS = (
        BEAROFFBUTTON_POS[0] + BEAROFFBUTTON_SIZE[0] // 2,
        RESOLUTION[1] - BEAROFFBUTTON_POS[1] - BEAROFFBUTTON_SIZE[1] // 2
    )

    ROLLBUTTON_POS = BEAROFFBUTTON_POS[0], RESOLUTION[1] // 2 - 50
    QUITBUTTON_POS = 100, RESOLUTION[1] // 2 - 50
    BARBUTTON_POS = (RESOLUTION[0] // 2 - FRAMESIZE,
                    RESOLUTION[1] // 2 - SIZEOFBOARD[1] // 2)

    MAX_SCORE = 15

    TIPS = {
        "hold": "Waiting for opponent..",
        "roll": "Roll the dice!",
        "singleroll": "Roll the dice!",
        "acceptint": "Waiting for opponent..",
        "move": "Make your move!",
        "acceptstate": "Waiting for opponent.."
    }

    def __init__(self, game):
        #Initalizes the view, its labels and buttons, and match variables.
        super().__init__(game)
        # Gets starting game state
        self.game_state = self.game.gamelogic.get_state()

        # List to store latest dice values
        self.dice_draw = []
        # List to store used dice values for a single turn
        self.used_dice_draws = []
        # Dict to store possible moves for a single turn
        self.possible_moves = {}

        # Defines labels
        self.labels = [
            # Tips label
            Label(
                self.TIPS_LABELPOS,
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=40,
                external=True,
                dynamic=True
            ),
            # Player number label
            Label(
                self.PLAYERNUMBER_LABELPOS,
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=30,
                external=True,
                dynamic=True
            ),
            # Player score label
            Label(
                self.PLAYERSCORE_LABELPOS,
                text="0",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=50,
                external=True,
                dynamic=True
            ),
            # Opponent score label
            Label(
                self.OPPONENTSCORE_LABELPOS,
                text="0",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=50,
                external=True,
                dynamic=True
            )
        ]

        # Defines buttons
        self.buttons = [
            # Roll button
            Button(
                self.ROLLBUTTON_POS,
                (130, 130),
                text="Roll", 
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=70,
                external=True,
                click_callback=self.roll_dice
            ),
            # Quit button
            Button(
                self.QUITBUTTON_POS,
                (130, 130),
                text="Quit",
                font_family="TheanoOldStyle-Regular.ttf",
                font_size=70,
                external=True,
                click_callback=self.quit_game
            ),
        ]

        self.initalize_buttons()
        # List to store highlighted points for a single turn
        self.hovered_points = []

        self.animate_dice = False
        self.die_animation_numrolls = 0
        self.die_animation_frame = 0

        self.showing_possible_checkers = False
        self.showing_possible_moves = False
        self.selected_point = None
        self.highlight_bearoff = False

        self.online = True
        self.player_number = 0

    def initalize_buttons(self):
        #Initializes points buttons, bar button and bearoff button
        npoints = len(self.game.gamelogic.points)
        pointwidth = self.BOARD_POINTWIDTH // npoints * 4

        point_xoffset = ((RESOLUTION[0] - self.SIZEOFBOARD[0]) // 2 + \
                self.FRAMESIZE)
        point_yoffset = ((RESOLUTION[1] - self.SIZEOFBOARD[1]) // 2 + \
                self.FRAMESIZE)

        # Defines buttons for the top row of points
        for i in range(npoints // 2):
            # left horizontal offset because of board middle vertical bar
            offset = 2 * self.FRAMESIZE * int(i >= npoints // 4)

            x = point_xoffset + i * pointwidth + offset
            y = point_yoffset

            btn = Button(
                (x, y), (pointwidth, self.POINTHEIGHT), visible=False,
                # converting i for loop index to gamestate points index
                hover_callback=lambda p=i: self.hover_point(p + 12),
                click_callback=lambda x=i: self.show_possible_moves(x + 12))

            self.buttons.append(btn)

        # Defines buttons for the bottom row of points
        for i in range(npoints // 2):
            # left horizontal offset because of board middle vertical bar
            offset = 2 * self.FRAMESIZE * int(i >= npoints // 4)

            x = point_xoffset + i * pointwidth + offset
            y = point_yoffset + self.POINTHEIGHT + self.SIZEOFBOARD[1] - \
                (2 * self.POINTHEIGHT) - (2 * self.FRAMESIZE)

            btn = Button(
                (x, y), (pointwidth, self.POINTHEIGHT), visible=False,
                # converting i for loop index to gamestate points index
                hover_callback=lambda p=i: self.hover_point(11 - p),
                click_callback=lambda x=i: self.show_possible_moves(11 - x))

            self.buttons.append(btn)

        bar_button = Button(
            self.BARBUTTON_POS,
            (self.FRAMESIZE * 2, self.SIZEOFBOARD[1]),
            visible=False,
            hover_callback=self.hover_bar,
            click_callback=self.click_bar
        )

        bearoff_button = Button(
            self.BEAROFFBUTTON_POS,
            self.BEAROFFBUTTON_SIZE,
            visible=False,
            hover_callback=self.hover_bearoff,
            click_callback=self.click_bearoff
        )

        self.buttons.append(bar_button)
        self.buttons.append(bearoff_button)

    def roll_dice(self):
        #Rolls dice, roll button's click_callback.
        pos = self.player_number
        #Single roll to set starting player
        if self.game.last_command == "singleroll":
            #If player is first one to single roll
            if pos == 0:
                self.dice_draw = [0]
            #keeps first dice value
            else:
                self.dice_draw = [self.dice_draw[0], 0]
            #Gets the random single value
            self.dice_draw[pos] = self.game.gamelogic.throw_dice()[0]
            # Starts dice animation
            self.animate_dice = True
        #The common dice roll
        elif self.game.last_command == "roll":
            self.animate_dice = True
            # Resets used dice values
            self.used_dice_draws = []

    def hover_point(self, point):
        #Handles points buttons mouse hovering
        if self.showing_possible_checkers:
            if point in self.possible_moves:
                self.pointing_cursor = True
        elif self.showing_possible_moves:
            if point in self.hovered_points or point == self.selected_point:
                self.pointing_cursor = True

    def hover_bar(self):
        #Handles bar button mouse hovering.
        command_check = self.game.last_command == "moving"
        #If any player checker is in bar
        if self.player_number in self.game_state[1] and command_check:
            self.pointing_cursor = True

    def hover_bearoff(self):
        #Handles bearoff button mouse hovering.
        if self.highlight_bearoff:
            self.pointing_cursor = True

    def show_possible_moves(self, point):
        #Points buttons click_callback, handle checker moves.
        if self.game.last_command == "moving":
            #If showing possible checkers (some checkers are highlighted)
            if not self.showing_possible_moves:
                #If point being clicked has at least one player's checker
                checkers = self.game_state[0][point]
                has_player_checker = self.player_number in checkers
                #And any legal move can be made from here
                is_movable = point in self.possible_moves
                if has_player_checker and is_movable:
                    #Saves clicked point
                    self.selected_point = point
                    #Stops showing other possible movable checkers
                    self.showing_possible_checkers = False
                    #Starts showing possible moves for the checker
                    self.showing_possible_moves = True
                    #Gets points to which the checker can be moved
                    possible_moves = self.possible_moves[point]
                    #Updates highlighted points (highlighted_points
                    #would be better) to show possible moves
                    self.hovered_points = [x for x in possible_moves]
                    #If checker is bearable, its move its represented
                    # as a tuple inside the possible_moves list
                    if any(type(move) is tuple for move in possible_moves):
                        # Highlights bearoff button
                        self.highlight_bearoff = True
            #If showing possible moves (some points are highlighted)
            else:
                #If user is reclicking the same point,
                #back to showing possible checkers
                if self.selected_point == point:
                    self.showing_possible_checkers = Tru
                    self.showing_possible_moves = False
                    self.selected_point = None
                    self.hovered_points = []
                    self.highlight_bearoff = False
                #If user is clicking a point which is
                #a legal move for the selected_point
                elif point in self.possible_moves[self.selected_point]:
                    # Moves the checker
                    self.make_move(point)

    def click_bar(self):
        #Bar button click_callback, handles entering hit checkers.
        #If any of the player checkers is on bar
        if self.player_number in self.game_state[1]:
            #If showing possible checkers (a checker on bar is highlighted)
            if self.showing_possible_checkers:
                #Sets selected point to a special value (-1)
                #to distinguish normal moves to entering moves
                self.selected_point = -1
                self.showing_possible_checkers = False
                self.showing_possible_moves = True
                #Gets possible entering moves
                possible_moves = self.possible_moves.get(-1, [])
                #Updates highlighted points
                self.hovered_points = [x for x in possible_moves]
            #If reclicking bar
            else:
                #Back to showing possible checkers
                self.showing_possible_checkers = True
                self.showing_possible_moves = False
                self.selected_point = None
                self.hovered_points = []

    def click_bearoff(self):
        #Bearoff button click_callback, handle bearing off.
        #If showing possible moves and checker can be beared off
        if self.showing_possible_moves and self.highlight_bearoff:
            #Updates game state
            self.game_state = self.game.gamelogic.bearoff(
                *self.game_state, self.selected_point + 1, self.player_number
            )
            #Gets dice value used to bearoff
            possible_moves = self.possible_moves[self.selected_point]
            #bearoff move is a 2 value tuple,
            #whose 2nd value is the dice value used 
            move_used = [
                move for move in possible_moves if type(move) is tuple
            ][0][1]
            #Sends used move to server
            #to update opponent's game state
            self.send_move(move_used)
            #Stops showing possible moves
            self.showing_possible_moves = False
            self.hovered_points = []
            self.highlight_bearoff = False

            self.labels[2].update_text(str(self.game_state[2][self.player_number]))
            logging.info(f"MainClient - Bearing off checker from {self.selected_point + 1}, score: {self.game_state[2][self.player_number]}.")

    def make_move(self, point):
        #Moves a checker from self.selected_point to given point
        #Stops showing possible moves
        self.showing_possible_moves = False
        self.hovered_points = []
        #Moves checker by updating game state
        move_used = self.move_checker(self.selected_point, point)
        #Sends updates to server
        self.send_move(move_used)

        logging.info(f"MainClient - Moving checker from {self.selected_point + 1} to {point + 1}.")

        self.selected_point = None

    def move_checker(self, point, to):
        #Moves a checker from a point to another,
        #returns dice value used.
        *self.game_state, move_left = self.game.gamelogic.move_to(
            *self.game_state, point + 1, to + 1, self.player_number)
        return move_left

    def send_move(self, move_used):
        #Sends updated game state to server, updates used dice values,
        #checks for end of turn or gamover.
        #Serializes and sends game state to server
        serialized, length = self.get_serialized_game_state()
        self.send_data_to_server(length)
        self.send_data_to_server(serialized, log="game state")

        #Updates used dice values
        if move_used in self.dice_draw:
            #Makes a copy of dice_draw
            draw = [x for x in self.dice_draw]
            #Replaces used dice values with -1
            #to handle correct behaviour when dice values
            #are the same (player has rolled the same value
            #in each dice)
            for d in self.used_dice_draws:
                draw.pop(d)
                draw.insert(d, -1)
            #Gets move_used's dice_draw index, 
            #appends it to used_dice_draw
            self.used_dice_draws.append(draw.index(move_used))

        #Checks if player has won
        if self.game.gamelogic.check_for_winner(
                self.game_state[2][self.player_number]):
            #Switches to gameover menu and shows winner
            self.game.current_view = self.game.gameovermenu
            self.game.current_view.show_winner(self.player_number)
            # Ends turn
            return self.end_turn()

        #If player has used all of the dice values
        if len(self.used_dice_draws) == len(self.dice_draw):
            self.end_turn()
        #If player has dice values left to use
        else:
            self.start_turn()

    def start_turn(self):
        #Called after player has rolled dice
        self.view_possible_moves_checkers()
        self.game.last_command = "moving"

    def end_turn(self):
        #Ends player turn, giving control back to server
        # Sends 0 to indicate end of turn
        self.send_data_to_server(0)
        self.game.last_command = "hold"

    def view_possible_moves_checkers(self):
        #Gets possible checkers that can be moved
        #after player has rolled dice.
        #Possible moves are stored as dict whose keys are points indexes
        #from which player can move a checker and whose values are lists
        #containing points indexes player can move checker to
        possible_moves = {}
        # Gets not used dice values
        r = range(len(self.dice_draw))
        draws_to_use = [
            self.dice_draw[i] for i in r if i not in self.used_dice_draws
        ]
        #If player has no checkers on bar
        if not self.player_number in self.game_state[1]:
            #For each point
            for point in range(len(self.game_state[0]) + 1):
                #Gets possible moves from that point
                possible_move = self.game.gamelogic.get_possible_moves(
                    self.game_state, point, self.player_number, draws_to_use)
                #If there are any possible moves adds them to possible_moves
                if possible_move:
                    possible_moves[point - 1] = [x - 1 for x in possible_move]
            #Checks if bearing off is possible
            if self.game.gamelogic.check_for_bearoff(
                *self.game_state, self.player_number):
                # Gets possible bearoffs
                possible_bearoffs = self.game.gamelogic.get_possible_bearoffs(
                    self.game_state[0], draws_to_use, self.player_number)
                # Adds them to possible_moves as tuple (-1, dice_value)
                for p, d in possible_bearoffs:
                    if p in possible_moves:
                        possible_moves[p].append((-1, d))
                    else:
                        possible_moves[p] = [(-1, d)]
        #If player has any checker on bar
        else:
            #Gets possible moves from bar, passing -1 as point number
            possible_move = self.game.gamelogic.get_possible_moves(
                self.game_state, -1, self.player_number, draws_to_use)
            #Adds them to possible_moves dict with -1 as key
            if possible_move:
                possible_moves[-1] = [x - 1 for x in possible_move]

        logging.info(f"MainClient - Possible moves: {possible_moves}")
        if not possible_moves:
            self.hovered_points = []
            logging.info("MainClient - No possible moves.")
            self.end_turn()
        else:
            self.showing_possible_checkers = True
        
        self.possible_moves = possible_moves

    def handle_turn(self):
        #Handles turn based on the latest command received from server.
        if self.game.last_command == "move":
            #Start showing possible moves
            self.start_turn()
        if self.game.last_command == "roll":
            #Checks for loss
            opp = int(not bool(self.player_number))
            if self.game.gamelogic.check_for_winner(self.game_state[2][opp]):
                self.game.current_view = self.game.gameovermenu
                self.game.current_view.show_winner(opp)

    def send_data_to_server(self, data, log=True):
        #Sends the data to the server
        self.game.MainClient.send_data(data, log=log)
    
    def get_serialized_game_state(self):
        #Returns a serialized version of the game state
        return Serialization.list_to_bytes(self.game_state)

    def update_dice(self):
        #Handles dice rolling animation
        #Changes shown dice values for a fixed number of times
        if self.animate_dice:
            #If number of shown values reaches the limit
            if self.die_animation_numrolls >= self.DIE_ANIMATION_NUMROLLS:
                #Stops animating dice
                self.animate_dice = False
                self.die_animation_numrolls = 0
                self.die_animation_frame = 0
                #Sends 0 to server to signal end of animation
                self.send_data_to_server("0")
                #If it's not a single roll
                if len(self.dice_draw) > 1:
                    #If user rolled the same value
                    if self.dice_draw[0] == self.dice_draw[1]:
                        #Doubles the number of values rolled
                        self.dice_draw *= 2
            else:
                #If animation frames for a pair of dice values
                #reaches a fixed amount, changes shown dice values
                #and reset frames counting
                if self.die_animation_frame >= \
                    self.DIE_ANIMATION_SINGLEROLLFRAMES:
                    #Increases die_animation_numrolls and resets frames
                    self.die_animation_numrolls += 1
                    self.die_animation_frame = 0
                    #If its a single roll
                    if self.game.last_command == "singleroll":
                        #Updates a single dice_draw value 
                        self.dice_draw[
                            self.player_number
                        ] = self.game.gamelogic.throw_dice()[0]
                    #If its a normal roll
                    elif self.game.last_command == "roll":
                        self.dice_draw = self.game.gamelogic.throw_dice()

                    #Sends to server formatted dice values
                    self.send_data_to_server(
                        "".join([str(x) for x in self.dice_draw])
                    )
                #Increases frames counter
                self.die_animation_frame += 1

    def quit_game(self):
        #If the player is hosting
        if self.game.server:
            self.game.server.stop()
        
        self.end_turn()
        #Switches view to menu
        self.game.back_to_menu()
        self.game.finished = True

    def update(self, mouse):
        #Calls each frame, updates view's logic and graphics.
        self.handle_turn()
        self.check_buttons(mouse)
        self.update_dice()
        self.update_labels()
        self.update_buttons()
        self.refresh()

    def draw_score_box(self, score, x, y, width, height, radius,
                        border, color, flipped, highlight):
        #Draws a rounded score box
        
        #Calculates height of the inner colored rect based on score
        mapped_height = round(height * (score / self.MAX_SCORE))
        #Calculates its y coordinate
        ypos = y + (height - mapped_height) if not flipped else y
        #Defines border radius for each corner
        bt_rd, tp_rd = (radius, 0) if not flipped else (0, radius)

        #If player score > 0
        if mapped_height > 0:
            #Draws the inner coloured rect
            pg.draw.rect(self.view, color,
                (x, ypos, width, mapped_height),
                border_top_left_radius=tp_rd,
                border_top_right_radius=tp_rd,
                border_bottom_left_radius=bt_rd,
                border_bottom_right_radius=bt_rd)

        #If a player can bearoff a checker
        if highlight:
            #Defines transparent surface
            surf = pg.Surface(self.BEAROFFBUTTON_SIZE)
            surf.fill("blue")
            surf.set_colorkey("blue")
            surf.set_alpha(150)
            # Defines its color
            if self.player_number == 1:
                color = self.BOARD_HOMEPOINTCOLOR
            else:
                color = self.BOARD_AWAYPOINTCOLOR
            #Draws a semi-transparent rect and blits surface to view
            pg.draw.rect(surf, color,
                (0, 0, width, height),
                border_top_left_radius=radius,
                border_top_right_radius=radius,
                border_bottom_left_radius=radius,
                border_bottom_right_radius=radius)
            self.view.blit(surf, (x, y))

        #Draws box outline
        pg.draw.rect(self.view, "black",
            (x, y, width, height), width=border,
            border_top_left_radius=radius,
            border_top_right_radius=radius,
            border_bottom_left_radius=radius,
            border_bottom_right_radius=radius)
        
    def draw_scores(self, scores):
        #Draws score boxes.
        #Sets colors
        if self.player_number == 0:
            color1 = self.BOARD_HOMEPOINTCOLOR
            color2 = self.BOARD_AWAYPOINTCOLOR
        else:
            color1 = self.BOARD_AWAYPOINTCOLOR
            color2 = self.BOARD_HOMEPOINTCOLOR
        #Draws player's score box
        self.draw_score_box(
            scores[self.player_number],
            *self.BEAROFFBUTTON_POS,
            *self.BEAROFFBUTTON_SIZE,
            self.BEAROFFBUTTON_RADIUS,
            self.BEAROFFBUTTON_BORDER,
            color1,
            False, self.highlight_bearoff)
        #Draws opponent's score box
        self.draw_score_box(
            scores[int(not self.player_number)],
            self.BEAROFFBUTTON_POS[0],
            RESOLUTION[1] - self.BEAROFFBUTTON_POS[1] - \
                self.BEAROFFBUTTON_SIZE[1],
            *self.BEAROFFBUTTON_SIZE,
            self.BEAROFFBUTTON_RADIUS,
            self.BEAROFFBUTTON_BORDER,
            color2,
            True, False)

    def draw_empty_board(self, npoints):
        #Draws game board, its frame and its points.
        board = pg.Surface(self.SIZEOFBOARD)
        board.fill(self.BASECOLOR)
        width, height = self.SIZEOFBOARD

        #Draws top row of points
        base_width = self.BOARD_POINTWIDTH // (npoints // 4)
        color = self.BOARD_AWAYPOINTCOLOR
        #Draws each 6 points group separately
        for x in range(2):
            for n in range(npoints // 4):
                #Draws a single point
                #Alternates point color based on previous point
                if color == self.BOARD_AWAYPOINTCOLOR:
                    color = self.BOARD_HOMEPOINTCOLOR
                else:
                    color = self.BOARD_AWAYPOINTCOLOR
                #Defines triangle coordinates
                #Left top corner
                p1x = self.FRAMESIZE + \
                    (width // 2 * x) + n * base_width
                p1y = self.FRAMESIZE
                #Right top corner
                p2x, p2y = p1x + base_width, p1y
                #Bottom corner
                p3x, p3y = p1x + base_width // 2, p1y + self.POINTHEIGHT
                #Draws filled and antialiased-triangle
                gfxdraw.filled_trigon(
                    board, p1x, p1y, p2x, p2y, p3x, p3y, color)
                gfxdraw.aatrigon(
                    board, p1x, p1y, p2x, p2y, p3x, p3y, color)
                #If point needs to be highlighted
                if n + (x * npoints // 4) + 12 in self.hovered_points:
                    # Draws semi-transparent triangle 
                    surf = pg.Surface((base_width, self.POINTHEIGHT))
                    surf.fill('black')
                    surf.set_colorkey('black')
                    surf.set_alpha(self.BOARD_HOVERPOINTALPHA)
                    #Highlighted color is the opposite of the point color
                    if color == self.BOARD_AWAYPOINTCOLOR:
                        hover_color = self.BOARD_HOMEPOINTCOLOR
                    else:
                        hover_color = self.BOARD_AWAYPOINTCOLOR
                    gfxdraw.filled_trigon(
                        surf,0, 0,
                        base_width, 0, base_width // 2,
                        self.POINTHEIGHT, hover_color)
                    #Draws multiple trigons with offset to 
                    #thicken triangle borders
                    for i in range(self.BOARD_HOVEREDPOINTBORDER):
                        gfxdraw.aatrigon(
                            board,
                            p1x + i, p1y + i,
                            p2x - i, p2y + i,
                            p3x, p3y - i * 5,
                            hover_color)
                    board.blit(surf, (p1x, p1y))
        #Draws bottom row of points
        color = self.BOARD_HOMEPOINTCOLOR
        for x in range(2):
            for n in range(npoints // 4):
                if color == self.BOARD_AWAYPOINTCOLOR:
                    color = self.BOARD_HOMEPOINTCOLOR
                else:
                    color = self.BOARD_AWAYPOINTCOLOR

                p1x = self.FRAMESIZE + (width // 2 * x) + \
                    n * base_width
                p1y = height - self.FRAMESIZE
                p2x, p2y = p1x + base_width, p1y

                p3x, p3y = p1x + base_width // 2, p1y - self.POINTHEIGHT
                gfxdraw.filled_trigon(
                    board, p1x, p1y, p2x, p2y, p3x, p3y, color)
                gfxdraw.aatrigon(
                    board, p1x, p1y, p2x, p2y, p3x, p3y, color)

                if 11 - (n + (x * npoints // 4)) in self.hovered_points:
                    surf = pg.Surface((base_width, self.POINTHEIGHT))
                    surf.fill('black')
                    surf.set_colorkey('black')
                    surf.set_alpha(self.BOARD_HOVERPOINTALPHA)

                    if color == self.BOARD_AWAYPOINTCOLOR:
                        hover_color = self.BOARD_HOMEPOINTCOLOR
                    else:
                        hover_color = self.BOARD_AWAYPOINTCOLOR
                    gfxdraw.filled_trigon(
                        surf, 0, self.POINTHEIGHT,
                        base_width, self.POINTHEIGHT,
                        base_width // 2, 0, hover_color)
                    for i in range(self.BOARD_HOVEREDPOINTBORDER):
                        gfxdraw.aatrigon(
                            board,
                            p1x + i, p1y - i,
                            p2x - i, p2y - i,
                            p3x, p3y + i * 5,
                            hover_color)
                    board.blit(surf, (p1x, p3y))

        #Draws board frame
        for i in range(2):
            half_frame = (width // 2 * i, 0, width * (i + 1), height)
            pg.draw.rect(board, self.FRAMECOLOR, half_frame,
                self.FRAMESIZE * 2)

        return board
    
    def draw_checker(
            self, board, type, c, r, n,
            top, highlight, selected, on_bar=False
        ):
        #Draws a single checker.
        #Chooses checker color based on player number
        color = self.CHECKER_AWAYCOLOR if type == 1 else self.CHECKER_HOMECOLOR
        #Calculates x coordinate offset because of middle bar width
        xoffset = self.FRAMESIZE * 2 if c >= n // 4 else 0
        #Calculates y coordinate based on top or bottom row
        if top:
            y = r * self.POINTHEIGHT // 5 + self.CHECKER_YOFFSET + \
                self.FRAMESIZE
        else:
            y = self.SIZEOFBOARD[1] - (self.FRAMESIZE + \
                r * self.POINTHEIGHT // 5 + self.CHECKER_YOFFSET)
        #Adjust coordinates for bar's checkers
        if on_bar:
            #Places checkers vertically on bar based on wether
            #there's a pair or odd number of checkers
            d = self.CHECKER_YOFFSET - self.CHECKER_RADIUS
            if c != n // 2:
                if c < n // 2:
                    i = ((n // 2) - c - 1 * bool(n % 2 == 0))
                else:
                    i = abs(c - (n // 2))
            else:
                i = 0
            x = self.SIZEOFBOARD[0] // 2
            if n % 2 == 0:
                y = (d // 2) + self.CHECKER_RADIUS + \
                    (2 * self.CHECKER_RADIUS + d) * ((n // 2) / (i + 1) - 1)
            else:
                y = (2 * self.CHECKER_RADIUS + d) * i
            y = round(-y) if c < n // 2 else round(y)
            y += self.SIZEOFBOARD[1] // 2
        #Checker is not on bar
        else:
            x = round((c + 0.5) * self.BOARD_POINTWIDTH // (n // 4)) \
                + self.FRAMESIZE + xoffset
        #The checker is drawn by stacking three circles
        
        #Draws the base checker
        gfxdraw.filled_circle(board, x, y, self.CHECKER_RADIUS, color)
        gfxdraw.aacircle(board, x, y, self.CHECKER_RADIUS, color)
        gfxdraw.filled_circle(
            board, x + 1, y + 1, self.CHECKER_RADIUS - 12, color)
        gfxdraw.aacircle(
            board, x + 1, y + 1, self.CHECKER_RADIUS - 12, color)

        #If checker can be moved or has been selected
        if highlight or selected:
            #Chooses checker's opposite color
            if type == 0:
                color = self.CHECKER_AWAYCOLOR
            else:
                color = self.CHECKER_HOMECOLOR
            #If the checker has been selected, changes its alpha

    def draw_current_state(self, board, points, bar):
        #Draws current game state (checkers)
        n = len(points)
        #Slices points list to later draw them separately
        slices = (points[n//2:], points[:n//2][::-1])
        possible_points = [move for move in self.possible_moves]

        #Draws top row of checkers
        for col, point in enumerate(slices[0]):
            for row, checker in enumerate(point):
                highlight = row == len(point) - 1 and \
                    (col + 12) in possible_points and \
                    self.showing_possible_checkers
                selected = row == len(point) - 1 and \
                    (col + 12) == self.selected_point and \
                    self.showing_possible_moves
                self.draw_checker(
                    board, checker, col, row, n,
                    top=True, highlight=highlight, selected=selected)

        #Draws top row of checkers
        for col, point in enumerate(slices[1]):
            for row, checker in enumerate(point):
                highlight = row == len(point) - 1 and \
                    (11 - col) in possible_points and \
                    self.showing_possible_checkers
                selected = row == len(point) - 1 and \
                    (11 - col) == self.selected_point and \
                    self.showing_possible_moves
                self.draw_checker(
                    board, checker, col, row, n,
                    top=False, highlight=highlight, selected=selected)
        
        #Draws bar's checkers
        for i, checker in enumerate(bar):
            highlight = self.player_number in bar and \
                i == bar.index(self.player_number) and \
                self.showing_possible_checkers
            selected = self.player_number in bar and \
                i == bar.index(self.player_number) and \
                self.selected_point == -1
            self.draw_checker(
                board, checker, i, 1, len(bar),
                True, highlight, selected, on_bar=True)

    def draw_dice(self, board, draws, draw):
        #Draws dice based on current dice values.
        #Gets number of dice thrown
        nrolls = min(2, len(draws))
        if not draw or not nrolls:
            return board
        
        x, y = self.DIE_POS
        

        for i in range(nrolls):
            #Draws die
            pg.draw.rect(
                board, self.DIE_COLOR,
                (x + self.DICE_XDISTANCE * i, y, self.DIE_SIZE, self.DIE_SIZE),
                border_radius=5
            )
            #Draws dots to represent die values
            for dotx, doty in self.DIE_DOTS[draws[i]]:
                gfxdraw.filled_circle(
                    board,
                    round(x + self.DIE_DOTSOFFSET * (1 + dotx) + \
                        self.DICE_XDISTANCE * i),
                    round(y + self.DIE_DOTSOFFSET * (1 + doty)),
                    self.DIE_DOTRADIUS,
                    self.DIE_DOTCOLOR
                )
                gfxdraw.aacircle(
                    board,
                    round(x + self.DIE_DOTSOFFSET * (1 + dotx) + \
                        self.DICE_XDISTANCE * i),
                    round(y + self.DIE_DOTSOFFSET * (1 + doty)),
                    self.DIE_DOTRADIUS,
                    self.DIE_DOTCOLOR
                )
        #Draws rect over dice to show used dice values
        nrolls = len(draws)
        for i in range(nrolls):
            if i in self.used_dice_draws:
                #Handles when player has 4 identical moves
                #(he has rolled the same value on each dice)
                if nrolls > 2:
                    xoff = 0 if i < 2 else 1
                    c = i if i < 2 else i - 2
                else:
                    c, xoff = 0, i
    def draw_board(self, state):
        #Draws The game board to view.
        points, bar, scores = state

        board = self.draw_empty_board(len(points))
        self.draw_current_state(board, points, bar)
        self.draw_dice(board, self.dice_draw, bool(len(self.dice_draw)))

        board_rect = board.get_rect(center=self.view.get_rect().center)
        self.view.blit(board, board_rect)

    def refresh(self):
        #Called each frame, handles drawing to view.
        self.view.fill('white')
        self.draw_board(self.game_state)
        self.draw_scores(self.game_state[2])
        self.draw_labels()
        self.draw_buttons()
