/* Hardware

 - Board: SparkFun Pro Micro
 - Processor: Use the 5V version
*/

#include "DebounceInput.h"
#include "Keyboard.h"
#include "Mouse.h"

#define STICK_OK 10
const int STICK_RIGHT = 16;
const int STICK_UP = 6;
const int STICK_DOWN = 4;
const int STICK_LEFT = 5;
const int BUTTON_ESC = 2;
const int BUTTON_F1 = 3;
const int BUTTON_F2 = 7;
const int BUTTON_F3 = 8;
const int BUTTON_F4 = 9;

struct Key
{
  int pin;
  int key;
  bool isMouseButton;
  DebouncedInput* input;
};

Key KEYBOARD[] = {
  {STICK_OK, KEY_RETURN, true, NULL},
  {STICK_RIGHT, KEY_RIGHT_ARROW, true, NULL},
  {STICK_UP, KEY_UP_ARROW, true, NULL},
  {STICK_DOWN, KEY_DOWN_ARROW, true, NULL},
  {STICK_LEFT, KEY_LEFT_ARROW, true, NULL},
  {BUTTON_ESC, KEY_ESC, false, NULL},
  {BUTTON_F1, KEY_F1, false, NULL},
  {BUTTON_F2, KEY_F2, false, NULL},
  {BUTTON_F3, KEY_F3, false, NULL},
  {BUTTON_F4, KEY_F4, false, NULL},
};
const int KEYS = sizeof(KEYBOARD) / sizeof(Key);

const Key* OK = &KEYBOARD[0];
const Key* RIGHT = &KEYBOARD[1];
const Key* UP = &KEYBOARD[2];
const Key* DOWN = &KEYBOARD[3];
const Key* LEFT = &KEYBOARD[4];
/*
Key ESC = {BUTTON_ESC, KEY_ESC, false, NULL};
Key F1 = {BUTTON_F1, KEY_F1, false, NULL};
Key F2 = {BUTTON_F2, KEY_F2, false, NULL};
Key F3 = {BUTTON_F3, KEY_F3, false, NULL};
Key F4 = {BUTTON_F4, KEY_F4, false, NULL};
*/
void setup() {
  for (int i=0; i < KEYS; ++i) {
    Key& key = KEYBOARD[i];
    key.input = new DebouncedInput(key.pin);
  };
  Mouse.begin();
  Keyboard.begin();
}

#define MOUSE_MODE_SWITCH_TIME 4000
#define MOUSE_RANGE 3
#define MOUSE_RESPONSE_DELAY 10
#define MOUSE_MODE_KEY BUTTON_F1

unsigned int mouseModeStartTick = 0;
unsigned int mouseLoopTimer = 0;
bool mouseMode = false;

unsigned int currentMillis;

void loop() {
  currentMillis = millis();
  for (int i=0; i < KEYS; ++i) {
    Key& key = KEYBOARD[i];
    key.input->read();
    if (key.input->falling()) {
      if (key.pin == MOUSE_MODE_KEY) {
        mouseModeStartTick = currentMillis;
      }
    } else if (key.input->rising()) {
      boolean ignoreKey = false;
      if (key.pin == MOUSE_MODE_KEY) {
        if (mouseModeStartTick != 0
            && ((currentMillis - mouseModeStartTick) > MOUSE_MODE_SWITCH_TIME)) {
          mouseMode = !mouseMode;
          mouseModeStartTick = 0;
          ignoreKey = true;
        }
      }
      if (!key.isMouseButton) {
          if (!ignoreKey)
            Keyboard.write(key.key);
      } else {
        if (!mouseMode && !ignoreKey) {
          // Send key when button is released but only if this is not a switch
          // from mouse mode to keyboard mode:
          Keyboard.write(key.key);
        }
      }
    }
  }
  if (mouseMode) {
    handleMouse();
  } else {
    mouseLoopTimer = currentMillis;
  };
}

void handleMouse() {
  if ((currentMillis - mouseLoopTimer) >= MOUSE_RESPONSE_DELAY) {
    mouseLoopTimer = currentMillis;
    // read the buttons:
    int upState = UP->input->high();
    int downState = DOWN->input->high();
    int rightState = RIGHT->input->high();
    int leftState = LEFT->input->high();
 
    // calculate the movement distance based on the button states:
    int  xDistance = (leftState - rightState) * MOUSE_RANGE;
    int  yDistance = (upState - downState) * MOUSE_RANGE;
 
    // if X or Y is non-zero, move:
    if ((xDistance != 0) || (yDistance != 0)) {
      Mouse.move(xDistance, yDistance, 0);
    }
 
    // if the mouse button is pressed:
    if (OK->input->low()) {
      // if the mouse is not pressed, press it:
      if (!Mouse.isPressed(MOUSE_LEFT)) {
        Mouse.press(MOUSE_LEFT);
      }
    } else {
      // if the mouse is pressed, release it:
      if (Mouse.isPressed(MOUSE_LEFT)) {
        Mouse.release(MOUSE_LEFT);
      }
    }
  }
}
