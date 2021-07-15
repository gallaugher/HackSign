# By Prof. John Gallaugher
# YouTube: https://YouTube.com/profgallaugher, https://gallaugher.com  Twitter: @gallaugher
#
# Takes advantage of worldful CircuitPython libraries, stewarded by Adafruit.
# Adafruit makes great hardware & has fanastic support. See adafruit.com
#
# Meant to be used with an Adafruit CircuitPlayground Bluefruit (CPB)
# and the free Adafruit Bluefruit app (only tested on iOS but Android should work).
# Savvy users can adapt the code to work with other Bluefruit boards by updating
# the led_pin = board.A1 to whatever pin is being used on the alternative board.A1
# To use:
#  - Save this code on the CircuitPlayground Bluefruit as code.py
#  - By default the sign will light up in the default color (BLUE, below)
# To run animations:
#  - Run the Bluefruit app on your mobile device or desktop computer.
#  - Press "Connect" on the CPB from the app's device list listed.
#    It should show up as "HackSign", but is finicky and might simply be
#    listed as something beginning with CIRCUITPY
#  - Select "Controller"
#  - Select Color Picker, choose a color, and press the "Send Selected Color" button to set
#    all colors in the sign.
#  - If you return to the controller "< Controller" in upper-right, you can select "Control Pad"
#  - Animations 1 - 3 will use the default color or last color selected in the app.
#  - #1 performs a "Blink" flash
#  - #2 performs a "Pulse", fading in and out fade_color
#  - #3 performs a "SparklePulse", starting blank, then randomly adding a new light until all LEDs are lit.
#  - #4 loops through various rainbow animations. Cue the EDM music.
#  - Left and Right arrows adjust the speed of flash or pulse animations faster (right) or slower (left)
#  - Up arrow stops animations & shows a single light in the selected color.
#    if the light is already showing, it will move the light "up" until it reaches the "other end" of the sign strip.
#  - Down arrow stops animations & shows a single light in the selected color.
#    if the light is already showing, it will move the light "down" until it reaches the "bottom" of the tie.

import board
import neopixel
import time

# TODO From Original - clear out imports not needed.
# for example, check DigitalInOut, Pulls, etc.
from digitalio import DigitalInOut, Direction, Pull
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.color_packet import ColorPacket
from adafruit_bluefruit_connect.button_packet import ButtonPacket

# import animations and colors
# TODO check to see if I can use Color.COLOR_NAME instead of imports below.
# ALSO: Ask someone which is more efficient.
from adafruit_led_animation.animation.solid import Solid
from adafruit_led_animation.animation.colorcycle import ColorCycle
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.comet import Comet
from adafruit_led_animation.animation.chase import Chase
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowChase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.sparkle import Sparkle
from adafruit_led_animation.animation.SparklePulse import SparklePulse
from adafruit_led_animation.sequence import AnimationSequence
from adafruit_led_animation.sequence import AnimateOnce
from adafruit_led_animation.color import (
    AMBER, #(255, 100, 0)
    AQUA, # (50, 255, 255)
    BLACK, #OFF (0, 0, 0)
    BLUE, # (0, 0, 255)
    CYAN, # (0, 255, 255)
    GOLD, # (255, 222, 30)
    GREEN, # (0, 255, 0)
    JADE, # (0, 255, 40)
    MAGENTA, #(255, 0, 20)
    OLD_LACE, # (253, 245, 230)
    ORANGE, # (255, 40, 0)
    PINK, # (242, 90, 255)
    PURPLE, # (180, 0, 255)
    RED, # (255, 0, 0)
    TEAL, # (0, 255, 120)
    WHITE, # (255, 255, 255)
    YELLOW, # (255, 150, 0)
    RAINBOW # a list of colors to cycle through
    # RAINBOW is RED, ORANGE, YELLOW, GREEN, BLUE, and PURPLE ((255, 0, 0), (255, 40, 0), (255, 150, 0), (0, 255, 0), (0, 0, 255), (180, 0, 255))
)

MAROON = (139, 0 , 0)

# setup bluetooth
ble = BLERadio()
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)
# Give your CPB a unique name between the quotes below
advertisement.complete_name = "HackSign"

runAnimation = False
animation_number = -1
lightPosition = -1

# Update to match the pin connected to your NeoPixels
led_pin = board.A1
# Update to match the number of NeoPixels you have connected
num_leds = 24
defaultColor = BLUE
pickedColor = defaultColor

defaultTime = 0.1
minWaitTime = 0.01
hundredths = 0.01
tenths = 0.1
adjustedTime = defaultTime

# If your light colors are off, try changing the initials GRB to a differnet order,
# swapping colors that seem in the wrong place (e.g. RGB instead of GRB, etc.).
strip = neopixel.NeoPixel(led_pin, num_leds, pixel_order=neopixel.GRB, brightness=1.0, auto_write=False)

solid = Solid(strip, color=PINK)
turnOff = Solid(strip, color=BLACK)
blink = Blink(strip, speed=0.5, color=pickedColor)
colorcycle = ColorCycle(strip, speed=0.5, colors=[MAGENTA, ORANGE, TEAL])
chase = Chase(strip, speed=0.1, color=WHITE, size=3, spacing=6)
# for night-rider, battlestar galactica larson scanner effect, set length to something lik e3 and speed to a bit longer like 0.2
# Comet has a dimming tale and can also bounce back.
cometTailLength = int(num_leds/3) + 1

# demonstrate that you can pass in custom colors, too.
# the multi values in parens below are called a tuple value.
# this tuple has three values between 0 and 255.
customMaroonSolid = Solid(strip, color = (128, 0, 0))

loopTimes = 0

strip.fill(pickedColor)
strip.write()

while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    ble.stop_advertising()

    # Now we're connected

    while ble.connected:
        # if ble.in_waiting:
        try:
            packet = Packet.from_stream(uart_server)
        except ValueError:
            continue # or pass. This will start the next

        if isinstance(packet, ColorPacket):
            print("*** color sent")
            print("pickedColor = ", ColorPacket)
            runAnimation = False
            animation_number = 0
            strip.fill(packet.color)
            strip.write()
            pickedColor = packet.color
            # the // below will drop any remainder so the values remain Ints, which color needs
            fade_color = (pickedColor[0]//2, pickedColor[1]//2, pickedColor[2]//2)
            # reset light_position after picking a color
            light_position = -1

        if isinstance(packet, ButtonPacket):
            if packet.pressed:
                if packet.button == ButtonPacket.BUTTON_1:
                    animation_number = 1
                    runAnimation = True
                elif packet.button == ButtonPacket.BUTTON_2:
                    animation_number = 2
                    # palette = blue
                    runAnimation = True
                    ledmode = 2
                elif packet.button == ButtonPacket.BUTTON_3:
                    animation_number = 3
                    # palette = school_colors
                    runAnimation = True
                    ledmode = 3
                elif packet.button == ButtonPacket.BUTTON_4:
                    animation_number = 4
                    runAnimation = True
                    # palette = rainbow_stripe
                    ledmode = 4
                    # buttonAnimation(offset, fadeup, palette)
                elif packet.button == ButtonPacket.UP or packet.button == ButtonPacket.DOWN:
                    animation_number = 0
                    runAnimation = False
                    # The UP or DOWN button was pressed.
                    increase_or_decrease = 1
                    if packet.button == ButtonPacket.DOWN:
                        increase_or_decrease = -1
                    lightPosition += increase_or_decrease
                    if lightPosition >= len(strip):
                        lightPosition = len(strip)-1
                    if lightPosition <= -1:
                        lightPosition = 0
                    strip.fill([0, 0, 0])
                    strip[lightPosition] = pickedColor
                    strip.show()
                elif packet.button == ButtonPacket.RIGHT:
                    # The RIGHT button was pressed.
                    runAnimation = True
                    # reset light_position after animation
                    lightPosition = -1
                    # new code below - you can delete code above
                    if adjustedTime <= 0.1:
                        adjustedTime = adjustedTime - hundredths
                    else:
                        adjustedTime = adjustedTime - tenths
                    if adjustedTime <= 0.0:
                        adjustedTime = minWaitTime
                elif packet.button == ButtonPacket.LEFT:
                    # The LEFT button was pressed.
                    runAnimation = True
                    # reset light_position after animation
                    light_position = -1
                   # new code below - you can delete code above
                    if adjustedTime >= 0.1:
                        adjustedTime = adjustedTime + tenths
                    else:
                        adjustedTime = adjustedTime + hundredths
        if runAnimation == True:
            if animation_number == 1:
                print("*** BLINK ***")
                blinkAnimation = Blink(strip, speed=adjustedTime, color=pickedColor)
                animations = AnimateOnce(blinkAnimation)
                while animations.animate():
                    pass
            elif animation_number == 2:
                print("*** PULSE ***")
                pulseAnimation = Pulse(strip, speed=adjustedTime, color=pickedColor, period=3)
                animations = AnimateOnce(pulseAnimation)
                while animations.animate():
                    pass
            elif animation_number == 3:
                """ For some reason Sparkle runs indefinitely
                # so I skipped Sparkle & used SparklePulse
            """
                print("*** SPARKLE PULSE ***")
                sparklePulseAnimation = SparklePulse(strip, speed=adjustedTime, period=3, color=pickedColor)
                animations = AnimateOnce(sparklePulseAnimation)
                while animations.animate():
                    pass
            elif animation_number == 4:
                print("*** RAINBOWS ***")
                #Rainbow: Entire strip starts RED and all lights fade together through rainbow
                rainbowAnimation = Rainbow(strip, speed=adjustedTime, period=2)
                # animations = AnimateOnce(rainbowAnimation)
                # RainbowSparkle: Strip sparkes all one color (Red first), then sparkles all one color through rest of the rainbow
                rainbowSparkleAnimation = RainbowSparkle(strip, speed=adjustedTime, period=3, num_sparkles=15)
                # RainbowComet - is a larson-style chase effect with comet in a rainbow pattern.
                # rainbowCometAnimation = RainbowComet(strip, speed=adjustedTime, tail_length=7, bounce=True)
                # animations = AnimateOnce(#ANIMATION_NAME_HERE#)

                # rainbowMedley
                #animations = AnimateOnce(rainbowAnimation, rainbowCometAnimation, rainbowSparkleAnimation)
                animations = AnimateOnce(rainbowAnimation, rainbowSparkleAnimation)
                while animations.animate():
                    pass
    # If we got here, we lost the connection. Go up to the top and start
    # advertising again and waiting for a connection.
