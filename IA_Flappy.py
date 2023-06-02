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
    
class Pipe():
    """
    Clase que representa un objeto de tubería
    """
    GAP = 200  # Espacio entre las tuberías
    VEL = 5  # Velocidad de desplazamiento de la tubería

    def _init_(self, x):
        """
        Inicializa el objeto de la tubería
        :param x: int
        :param y: int
        :return: None
        """
        self.x = x
        self.height = 0

        # Posición del inicio y final de la tubería
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        Establece la altura de la tubería desde la parte superior de la pantalla
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Mueve la tubería en función de la velocidad
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        Dibuja la parte superior e inferior de la tubería
        :param win: ventana/superficie de Pygame
        :return: None
        """
        # Dibuja la parte superior
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # Dibuja la parte inferior
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird, win):
        """
        Verifica si un punto está colisionando con la tubería
        :param bird: objeto Bird
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True
        
        return False

class Base:
    """
    Representa el suelo móvil del juego
    """
    VEL = 5  # Velocidad de desplazamiento del suelo
    WIDTH = base_img.get_width()  # Ancho de la imagen del suelo
    IMG = base_img

    def _init_(self, y):
        """
        Inicializa el objeto
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Mueve el suelo para que parezca que se desplaza
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Dibuja el suelo. Son dos imágenes que se mueven juntas.
        :param win: la superficie o ventana de Pygame
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
    """
    Rota una superficie y la dibuja en la ventana
    :param surf: la superficie en la que se dibujará
    :param image: la superficie de imagen para rotar
    :param topleft: la posición superior izquierda de la imagen
    :param angle: un valor float para el ángulo
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect.topleft)


def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    Dibuja la ventana para el ciclo principal del juego
    :param win: la superficie o ventana de Pygame
    :param bird: un objeto Bird
    :param pipes: lista de tuberías
    :param score: puntuación del juego (int)
    :param gen: generación actual
    :param pipe_ind: índice de la tubería más cercana
    :return: None
    """
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # Dibuja líneas desde el pájaro hasta la tubería
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0), (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0), (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2),
                                 (pipes[pipe_ind].x +pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # Dibuja el pájaro
        bird.draw(win)
    
    # Puntaje
    score_label = STAT_FONT.render("Puntaje: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # Generaciones
    score_label = STAT_FONT.render("Gens: " + str(gen-1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    # Vivos
    score_label = STAT_FONT.render("Vivos: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50))

    pygame.display.update()

def eval_genomes(genomes, config):
    """
    Ejecuta la simulación de la población actual de aves y establece su
    aptitud en función de la distancia que alcanzan en el juego.
    """
    global WIN, gen
    win = WIN
    gen += 1

    # Comienza creando listas que contengan el genoma en sí, la
    # red neuronal asociada al genoma y el
    # objeto de ave que utiliza esa red para jugar
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # comienza con un nivel de aptitud de 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # determina si usar el primer o segundo
                pipe_ind = 1                                                                 # tubo en la pantalla para la entrada de la red neuronal

        for x, bird in enumerate(birds):  # da a cada ave una aptitud de 0.1 por cada fotograma que permanece viva
            ge[x].fitness += 0.1
            bird.move()

            # envía la ubicación del ave, la ubicación del tubo superior y la ubicación del tubo inferior y determina desde la red si debe saltar o no
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # usamos una función de activación tangente hiperbólica, por lo que el resultado estará entre -1 y 1. si es mayor a 0.5, salta
                bird.jump()

        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # revisa si hay colisión
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            # se puede agregar esta línea para dar más recompensa por pasar a través de un tubo (no es obligatorio)
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # romper si la puntuación es lo suficientemente alta
        '''if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break'''


def run(config_file):
    """
    Ejecuta el algoritmo NEAT para entrenar una red neuronal para jugar a Flappy Bird.
    :param config_file: ubicación del archivo de configuración
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Crea la población, que es el objeto de nivel superior para una ejecución de NEAT.
    p = neat.Population(config)

    # Agrega un reportero de stdout para mostrar el progreso en la terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    # p.add_reporter(neat.Checkpointer(5))

    # Ejecuta hasta 50 generaciones.
    winner = p.run(eval_genomes, 50)

    # muestra las estadísticas finales
    print('\nMejor genoma:\n{!s}'.format(winner))


if _name_ == '_main_':
    # Determina la ruta del archivo de configuración. Esta manipulación de ruta está
    # aquí para que el script se ejecute correctamente independientemente del
    # directorio de trabajo actual.
    local_dir = os.path.dirname(_file_)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)