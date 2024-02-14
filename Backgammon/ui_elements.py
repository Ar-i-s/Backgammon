import pygame as pg

from settings import *

pg.font.init()
BASE_FONT = pg.font.SysFont("Calibri", 20)

class Label:
    DEFAULTS = {
        "text": "",
        "color": "black",
        "font_family": "Calibri",
        "font_size": 20,
        "external": False,
        "dynamic": False
    }
    def __init__(self, center, **kwargs):
        self.center = center
        self.text = kwargs.get("text", self.DEFAULTS["text"])
        self.color = kwargs.get("color", self.DEFAULTS["color"])
        font_family = kwargs.get("font_family", self.DEFAULTS["font_family"])
        font_size = kwargs.get("font_size", self.DEFAULTS["font_size"])
        external = kwargs.get("external", self.DEFAULTS["external"])
        self.dynamic = kwargs.get("dynamic", self.DEFAULTS["dynamic"])

        #Chooses font type
        font_type = pg.font.Font if external else pg.font.SysFont
        self.font = font_type(font_family, font_size)
        #Renders the label surface
        self.render()

    def update_text(self, text):
        self.text = text

    def update(self):
        if self.dynamic:
            self.render()

    def render(self):
        self.surface = self.font.render(self.text, True, self.color)
        #Positioning the label so it's center is in self.center
        self.rect = self.surface.get_rect(center=self.center)
    
    def draw(self, view):
        view.blit(self.surface, self.rect)

class Button(Label):
    BTN_DEFAULTS = {
        "visible": True,
        "hover_callback": lambda: None,
        "click_callback": lambda: print("click")
    }
    def __init__(self, pos, size, **kwargs):
        self.width, self.height = size
        center = pos[0] + self.width // 2, pos[1] + self.height // 2
        self.x, self.y = pos
        super().__init__(center, **kwargs)

        self.visible = kwargs.get("visible", self.BTN_DEFAULTS["visible"])
        self.hover_callback = kwargs.get(
            "hover_callback", self.BTN_DEFAULTS["hover_callback"])
        self.click_callback = kwargs.get(
            "click_callback", self.BTN_DEFAULTS["click_callback"])

        self.dynamic = True if self.visible else False

        self.hovered = False
        self.clicked = False
        self.released = False
    
    def check_input(self, mousepos, mouseclick):
        self.is_hovered(mousepos)
        self.is_pressed(mouseclick)

    def is_hovered(self, mousepos):
        self.hovered = False
        mousex, mousey = mousepos[0], mousepos[1]
        xcollide = self.x < mousex < self.x + self.width
        ycollide = self.y < mousey < self.y + self.height
        if xcollide and ycollide:
            self.hovered = True

    def is_pressed(self, mouseclick):
        self.released = False
        if mouseclick:
            self.clicked = True
        else:
            if self.clicked:
                self.released = True
                self.clicked = False            
        #Calls callback only when mouse button
        #has been released after a click
        if self.hovered and self.released:
            self.click_callback()

    def update(self, view):
        self.color = (100, 100, 100)
        if self.hovered:
            self.color = "black"
            self.hover_callback()
            if self.visible:
                view.pointing_cursor = True
        if self.dynamic:
            self.render()
    
    def draw(self, view):
        if self.visible:
            view.blit(self.surface, (self.x, self.y, 0, 0))

class View:
    BASE_BG_COLOR = "white"
    def __init__(self, game):
        self.game = game
        self.view = pg.Surface(RESOLUTION)

        self.labels = []
        self.buttons = []

        self.pointing_cursor = False

    def check_buttons(self, mouse):
        mousepos, mouseclick = mouse.get_pos(), mouse.get_click()
        for btn in self.buttons:
            btn.check_input(mousepos, mouseclick)
        #Sets the normal cursor icon
        self.pointing_cursor = False

    def update_labels(self):
        for lbl in self.labels:
            lbl.update()

    def update_buttons(self):
        for btn in self.buttons:
            btn.update(self)

    def update(self, mouse):
        self.check_buttons(mouse)
        self.update_labels()
        self.update_buttons()
        self.refresh()

    def draw_labels(self):
        for lbl in self.labels:
            lbl.draw(self.view)
    
    def draw_buttons(self):
        for btn in self.buttons:
            btn.draw(self.view)
        #Sets the mouse icon
        self.game.mouse.set_pointing_cursor(self.pointing_cursor)
    
    def refresh(self):
        self.view.fill(self.BASE_BG_COLOR)
        self.draw_labels()
        self.draw_buttons()

    def get_surface(self):
        return self.view