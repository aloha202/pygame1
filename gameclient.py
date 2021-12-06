import socket
import pygame
import os
import pickle
pygame.font.init()
pygame.mixer.init()

HEADER = 64
PORT = 5051
SERVER = "127.0.0.1"
FORMAT = 'utf-8'
DELIM = '::'

FPS = 60


DISCONNECT_MESSAGE = "!DISCONNECT"
CONTINUE_MESSAGE = "!CONTINUE"
HANDSHAKE_MESSAGE = "!HANDSHAKE"
MESSAGE_MESSAGE = "!MESSAGE"

ADDR = (SERVER, PORT)


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = pickle.dumps(msg)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    result = client.recv(10000)
    result = pickle.loads(result)
    return result

name = input("Enter your name:")
send_obj = {
    "type": HANDSHAKE_MESSAGE,
    "name": name
}
res = send(send_obj)

_RESULT = res.copy()
_ME_ = res['id']



BULLET_HIT_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'Grenade+1.mp3'))
BULLET_FIRE_SOUND = pygame.mixer.Sound(os.path.join('Assets', 'Gun+Silencer.mp3'))

HEALTH_FONT = pygame.font.SysFont('comicsans', 40)
WINNER_FONT = pygame.font.SysFont('comicsans', 100)

YELLOW = (255,255,0)
RED = (255,0,0)

WIDTH, HEIGHT = 900, 500
SPACESHIP_WIDTH = 50
SPACESHIP_HEIGHT = 50
SPACESHIP_SIZE = (SPACESHIP_WIDTH,SPACESHIP_HEIGHT)

BULLET_VEL = 8
BULLET_WIDTH = 10

YELLOW_HIT = pygame.USEREVENT + 1
RED_HIT = pygame.USEREVENT + 2

BORDER_WIDTH = 10
BORDER_LEFT = WIDTH//2 - (BORDER_WIDTH / 2)
BORDER = pygame.Rect(BORDER_LEFT, 0, BORDER_WIDTH, HEIGHT)

WIN = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("My Super Game")

FPS = 60
VEL = 5
MAX_BULLETS = 3

YELLOW_SPACESHIP_IMAGE = pygame.image.load(os.path.join('Assets', 'spaceship_yellow.png'))
YELLOW_SPACESHIP = pygame.transform.scale(YELLOW_SPACESHIP_IMAGE, SPACESHIP_SIZE)
YELLOW_SPACESHIP = pygame.transform.rotate(YELLOW_SPACESHIP, 90)

RED_SPACESHIP_IMAGE = pygame.image.load(os.path.join('Assets', 'spaceship_red.png'))
RED_SPACESHIP = pygame.transform.scale(RED_SPACESHIP_IMAGE, SPACESHIP_SIZE)
RED_SPACESHIP = pygame.transform.rotate(RED_SPACESHIP, 270)

SPACE = pygame.transform.scale(pygame.image.load(os.path.join('Assets', 'space.png')), (WIDTH, HEIGHT))

_SPACESHIPS = {
    'yellow': {
        'ship': None,
        'bullets': [],
        'name': False,
        'position': 'left',
        'image': YELLOW_SPACESHIP,
        'color': YELLOW,
        'boundry_left': 0,
        'boundry_right': BORDER.x
    },
    'red': {
        'ship': None,
        'bullets': [],
        'name': False,
        'position': 'right',
        'image': RED_SPACESHIP,
        'color': RED,
        'boundry_left': BORDER.x + BORDER.width,
        'boundry_right': WIDTH
    }
}



def draw_window():
    WIN.blit(SPACE, (0, 0))
    pygame.draw.rect(WIN, (0,0,0), BORDER)

    for key in _SPACESHIPS:
        spaceship = _SPACESHIPS[key]
        if spaceship['name']:
            health_text = HEALTH_FONT.render(spaceship['name'] + ' ' + "".ljust(spaceship['health'], '|'), 1, (255,255,255))
            if spaceship['position'] == 'left':
                text_x = 10
            else:
                text_x = WIDTH - health_text.get_width() - 10
            WIN.blit(health_text, (text_x, 10))        
            WIN.blit(spaceship['image'], (spaceship['ship'].x, spaceship['ship'].y))
            for bullet in spaceship['bullets']:
                if bullet:
                    pygame.draw.rect(WIN, spaceship['color'], bullet)

    pygame.display.update()

def get_updates(data):
    result = send({"type": MESSAGE_MESSAGE, "data": data})
    for key in _SPACESHIPS:
        _SPACESHIPS[key]['name'] = False
    for key in result['players']:
        player = result['players'][key]
        if player['id']:
            _SPACESHIPS[player['id']]['name'] = player['name']
    return result
    
def handle_movement(keys_pressed):
    me_data = _RESULT['data']['spaceships'][_ME_]
    me = _SPACESHIPS[_ME_]
    if keys_pressed[pygame.K_LEFT] and me_data['x'] - VEL >= me['boundry_left']:
        me_data['x'] -= VEL
    if keys_pressed[pygame.K_RIGHT] and me_data['x'] + me['ship'].width + VEL <=  me['boundry_right']:
        me_data['x'] += VEL
    if keys_pressed[pygame.K_UP] and me_data['y'] - VEL >= 0:
        me_data['y'] -= VEL
    if keys_pressed[pygame.K_DOWN] and me_data['y'] + VEL + me['ship'].height <= HEIGHT:
        me_data['y'] += VEL

    bullet_step = BULLET_VEL if me['position'] == 'left' else -BULLET_VEL
    for i in range(len(me_data['bullets'])):
        me_data['bullets'][i]['x'] += bullet_step
        remove = False
        if me['position'] == 'left':
            if me_data['bullets'][i]['x'] > WIDTH:
                remove = True
        else:
            if me_data['bullets'][i]['x'] + BULLET_WIDTH < 0:
                remove = True
        if remove:
            _RESULT['data']['spaceships'][_ME_]['bullets'][i] = False
    if False in _RESULT['data']['spaceships'][_ME_]['bullets']:
        _RESULT['data']['spaceships'][_ME_]['bullets'].remove(False)


def update_bullets(type, data_spaceships):
    if len(data_spaceships[type]['bullets']) > len(_SPACESHIPS[type]['bullets']): #somebody fired a bullet
        bullet = pygame.Rect(0, 0, BULLET_WIDTH, 5)
        _SPACESHIPS[type]['bullets'].append(bullet)
        BULLET_FIRE_SOUND.play()
    elif len(data_spaceships[type]['bullets']) < len(_SPACESHIPS[type]['bullets']):
        _SPACESHIPS[type]['bullets'].pop(0)
    for i in range(len(data_spaceships[type]['bullets'])):
        if _SPACESHIPS[type]['bullets'][i] and data_spaceships[type]['bullets'][i]:
            _SPACESHIPS[type]['bullets'][i].x = data_spaceships[type]['bullets'][i]['x']
            _SPACESHIPS[type]['bullets'][i].y = data_spaceships[type]['bullets'][i]['y']

def update_models(data_spaceships):
    _SPACESHIPS['yellow']['ship'].x = data_spaceships['yellow']['x']
    _SPACESHIPS['yellow']['ship'].y = data_spaceships['yellow']['y']
    _SPACESHIPS['red']['ship'].x = data_spaceships['red']['x']
    _SPACESHIPS['red']['ship'].y = data_spaceships['red']['y']
    
    update_bullets('red', data_spaceships)
    update_bullets('yellow', data_spaceships)

    

def main():
    global _RESULT
    spaceships = _RESULT['data']['spaceships']
    _SPACESHIPS['red']['ship'] = pygame.Rect(spaceships['red']['x'], spaceships['red']['y'], SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    _SPACESHIPS['yellow']['ship'] = pygame.Rect(spaceships['yellow']['x'], spaceships['yellow']['y'], SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
    _SPACESHIPS['red']['health'] = 10
    _SPACESHIPS['yellow']['health'] = 10
    _SPACESHIPS['red']['bullets'] = []
    _SPACESHIPS['yellow']['bullets'] = []


    run = True
    clock = pygame.time.Clock()

    me = _SPACESHIPS[_ME_]

    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                send({"type": DISCONNECT_MESSAGE})
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and len(me['bullets']) < MAX_BULLETS:
                    if(me['position'] == 'left'):
                        bullet_x = me['ship'].x + me['ship'].width
                    else:
                        bullet_x = me['ship'].x
                    bullet_y = me['ship'].y + (me['ship'].height//2) - 2
                    _RESULT['data']['spaceships'][_ME_]['bullets'].append({
                        'x': bullet_x,
                        'y': bullet_y
                    })

        handle_movement(pygame.key.get_pressed())
        r = get_updates(_RESULT['data']['spaceships'][_ME_])
        _RESULT = r.copy()
        # print(_RESULT['data']['spaceships'])
        update_models(_RESULT['data']['spaceships'])
        draw_window()

    main()

if __name__ == '__main__':
    main()