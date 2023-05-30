#importamos la librerias necesarias
import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init()  # init font

WIN_WIDTH = 600  # Anchura de la ventana del juego
WIN_HEIGHT = 800  # Altura de la ventana del juego
FLOOR = 730  # Posición del suelo en el juego
STAT_FONT = pygame.font.SysFont("comicsans", 50)  # Fuente utilizada para mostrar estadísticas en el juego
END_FONT = pygame.font.SysFont("comicsans", 70)  # Fuente utilizada para mostrar mensajes finales en el juego
DRAW_LINES = False  # Bandera para indicar si se deben dibujar líneas de conexión en la red neuronal

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Crea la ventana del juego con el tamaño especificado
pygame.display.set_caption("Flappy Bird")  # Establece el título de la ventana como "Flappy Bird"

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")).convert_alpha())  # Carga y escala la imagen de los tubos
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs","bg.png")).convert_alpha(), (600, 900))  # Carga y escala la imagen de fondo
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird" + str(x) + ".png"))) for x in range(1,4)]  # Carga y escala las imágenes del pájaro en diferentes estados
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")).convert_alpha())  # Carga y escala la imagen de la base del juego

gen = 0

class Bird:
    """
    Clase Bird que representa al pájaro en el juego Flappy Bird
    """
    MAX_ROTATION = 25  # Rotación máxima del pájaro
    IMGS = bird_images  # Imágenes del pájaro en diferentes estados
    ROT_VEL = 20  # Velocidad de rotación
    ANIMATION_TIME = 5  # Tiempo de animación

    def __init__(self, x, y):
        """
        Inicializa el objeto Bird
        :param x: posición inicial en el eje x (int)
        :param y: posición inicial en el eje y (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # Grados de inclinación
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Hace que el pájaro salte
        :return: None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        Hace que el pájaro se mueva
        :return: None
        """
        self.tick_count += 1

        # Para la aceleración descendente
        displacement = self.vel*(self.tick_count) + 0.5*(3)*(self.tick_count)**2  # Calcula el desplazamiento

        # Velocidad terminal
        if displacement >= 16:
            displacement = (displacement/abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # Inclinación hacia arriba
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # Inclinación hacia abajo
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Dibuja al pájaro
        :param win: ventana o superficie de Pygame
        :return: None
        """
        self.img_count += 1

        # Para la animación del pájaro, cambia entre tres imágenes
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # Cuando el pájaro se está sumergiendo, no aletea las alas
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        # Inclina al pájaro
        blitRotateCenter(win, self.img, (self.x, self.y),self.tilt)

    def get_mask(self):
        """
        Obtiene la máscara para la imagen actual del pájaro
        :return: None
        """
        return pygame.mask.from_surface(self.img)