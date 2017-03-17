/* Hardware

 - Board: Arduino Nano
*/

// IO Definitions

#define dspl_sclk 2
#define dspl_mosi 3
#define dspl_dc   4
#define dspl_cs   5
#define dspl_rst  6

#define BATTERY_1_OUT 10
#define BATTERY_2_OUT 11
#define BATTERY_3_OUT 12

#define BATTERY_1_ANALOG_IN A0
#define BATTERY_2_ANALOG_IN A1
#define BATTERY_3_ANALOG_IN A2

// Color definitions
#define BLACK   0x0000
#define BLUE    0x001F
#define RED     0xF800
#define GREEN   0x07E0
#define CYAN    0x07FF
#define MAGENTA 0xF81F
#define YELLOW  0xFFE0  
#define WHITE   0xFFFF

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1351.h>
#include <SPI.h>

// using SPI Hardware
//Adafruit_SSD1351 tft = Adafruit_SSD1351(dspl_cs, dspl_dc, dspl_rst);
Adafruit_SSD1351 tft = Adafruit_SSD1351(dspl_cs, dspl_dc, dspl_mosi, dspl_sclk, dspl_rst);  

#define START_TIMER 2000  // ms

#define LEVEL_RED        11.3
#define LEVEL_YELLOW     11.8
#define LEVEL_HYSTERESIS  0.2

#define LEVEL_MIN 11.8  // switch battery level

#define DISPLAY_V_MIN 11.0
#define DISPLAY_V_MAX 13.0


class Battery {
  /** Represents a single battery
   *
   **/
  int _analogPin;
  int _onPin;
  float _factor;
  int _center;

  int _analog = 0;
  float _u = 0.0;
  byte _selected = -1;
  byte _old_selected = -99;

  bool _available = true;

  float _old_u = 99.0;
  
  public:
    byte num;
    
    Battery(int analogPin, int onPin, float factor, byte num, int center) {
      _analogPin = analogPin;
      _onPin = onPin;
      _factor = factor;
      this->num = num;
      _center = center;
    };

    void update() {
      _analog = analogRead(_analogPin);
      if (_available) {
        _u = (float)(int)((_analog * _factor) * 100) / 100;
      } else {
        _u = 0.0;
      }
    };

    void select(byte selected) {
      _selected = selected;
    }

    bool checkAvailable() {
      _available = _u > 8.0;
      return _available;
    }

    void manage() {
      digitalWrite(_onPin, (_available && (_selected == num)) ? HIGH : LOW);
    };
    
    float volt() {
      return _u;
    };
    
    float analog() {
      return _analog;
    };

    void draw_reset() {
      _old_selected = -99;
      _old_u = 99.0;
    };

    void draw_info() {
      draw_header();
      draw_batteries();
      _old_selected = _selected;
    };

    void draw_boot_info() {
      draw_batteries();
      _old_selected = _selected;
    };

private:
    void draw_header() {
      if (_old_selected != _selected) {
        tft.fillRect(_center-18, 0, 36, 16, (_selected == num) ? GREEN : WHITE);
        tft.setTextColor(BLACK);
        tft.setTextSize(2);
        tft.setCursor(_center-18+12, 1);
        tft.print(num);
      };
    }

    void draw_batteries() {
      if (   (_old_selected != _selected)
          && (!_available)
         ) {
        tft.fillRect(_center-18, 18, 36, 78, BLACK);
        tft.drawLine(_center-18, 18, _center+17, 96, RED);
        tft.drawLine(_center+17, 18, _center-18, 96, RED);
      }
      if (   _available
          && (   (_u < (_old_u - 0.03))
              || (_u > (_old_u + 0.03)))
         ) {
        int h = 0;
        if (_u > DISPLAY_V_MIN) {
          if (_u > DISPLAY_V_MAX) {
            h = 78;
          } else {
            h = (_u - DISPLAY_V_MIN) * 78.0 / 2;
          }
        } else if (_u > 2.0) {
          h = 5;
        }
        int color = GREEN;
        if (_u <= LEVEL_YELLOW) {
          if (_u > LEVEL_RED) {
            color = YELLOW;
          } else {
            color = RED;
          }
        }
        if (_u < 2.0) {
          color = RED;
          h = 78;
        }
        if (h != 78)
          tft.fillRect(_center-18, 18, 36, 78 - h, BLACK);
        tft.fillRect(_center-18, 18 + 78 - h, 36, h, color);
        tft.setRotation(3);
        tft.setTextSize(2);
        tft.setTextColor(WHITE);
        tft.setCursor(2, _center-9);
        tft.print(_u); tft.print("V");
        tft.setRotation(0);
        _old_u = _u;
      }
    }
};


#define NUM_BATTERIES 3
#define ANALOG_FACTOR 0.0155821

Battery* batteries[] = {
 new Battery(BATTERY_1_ANALOG_IN, BATTERY_1_OUT, ANALOG_FACTOR, 1, 19),
 new Battery(BATTERY_2_ANALOG_IN, BATTERY_2_OUT, ANALOG_FACTOR, 2, 64),
 new Battery(BATTERY_3_ANALOG_IN, BATTERY_3_OUT, ANALOG_FACTOR, 3, 109),
};

Battery* active_batteries[] = {0, 0, 0};


class BatteryManager {

  Battery** all_batteries;
  Battery** batteries;
  
  byte num_active_batteries = 0;
  byte selected = -1;
  
public:
  BatteryManager(Battery** batteries, Battery** active_batteries) {
    this->all_batteries = batteries;
    this->batteries = active_batteries;
  };

  void begin() {
    this->loop_all(&Battery::update);
    int insert = 0;
    for(int i = 0; i < NUM_BATTERIES; i++) {
      Battery* battery=all_batteries[i];
      if (battery->checkAvailable()) {
        batteries[num_active_batteries] = battery;
        num_active_batteries++;
      }
    }
    selected = -1;
    // this->selectBattery();
  }

  void call(bool booting) {
    this->loop(&Battery::update);
    if (!booting)
      this->selectBattery();
    this->loop(&Battery::manage);
  }

  void draw_reset() {
    this->loop_all(&Battery::draw_reset);
  }

  void draw_info() {
    this->loop_all(&Battery::draw_info);
  }

  void draw_boot_info() {
    this->loop_all(&Battery::draw_boot_info);
  };

private:
  void selectBattery() {
    /** Battery selection strategy:
     *
     * At start select the first battery with highest voltage.
     *
     * Switch to another battery when current battery is below LEVEL_MIN.
     * If all are below LEVEL_MIN always switch to the one with the highes
     * voltage.
     *
     **/
    if (num_active_batteries < 0) {
      // no batteries
      selected = -1;
    } else if (num_active_batteries == 1) {
      // only one battery
      selected = 0;
    } else {
      float current_u = 0.0;
      if (selected >= 0 && selected < num_active_batteries)
        current_u = batteries[selected]->volt();
      if (current_u < LEVEL_MIN) {
        // lookup a new battery
        int next_selected = -1;
        int next_u = 0.0;
        for(int i = 0; i < num_active_batteries; i++) {
          if (next_u < batteries[i]->volt()) {
            next_selected = i;
            next_u = batteries[i]->volt();
          };
        };
        if (next_selected >= 0
            && (next_u > (current_u + LEVEL_HYSTERESIS)))
          selected = next_selected;
      }
    }
    // convert the selection index to the battery number
    byte s = selected;
    if (s >= 0 && s < num_active_batteries)
      s = batteries[s]->num;
    for(int i = 0; i < num_active_batteries; i++)
      batteries[i]->select(s);
  }

  void loop_all(void (Battery::*f)()) {
    for(int i = 0; i < NUM_BATTERIES; i++)
        (all_batteries[i]->*f)();
  }

  void loop(void (Battery::*f)()) {
    for(int i = 0; i < num_active_batteries; i++)
        (batteries[i]->*f)();
  }
};


class WristWatch {
  unsigned long start_time = 0;
  unsigned long loop_time = 0;
  unsigned long time_diff = 0;
  unsigned long duration = 0;
  int old_w = -1;

public:
    void start(unsigned int duration) {
        this->duration = duration;
        this->start_time = millis();
    };

    void loop() {
        this->loop_time = millis();
        this->time_diff = this->loop_time - this->start_time;
    };

    bool finished() {
      return time_diff >= duration;
    };

    void draw_reset() {
      old_w = -1;
    };

    void draw() {
      if (finished()) {
        tft.fillRect(0, 0, 128, 16, BLUE);
      } else {
        if (old_w < 0) {
          tft.fillRect(0, 0, 128, 16, WHITE);
          old_w = 0;
        }
        int w = (128 * time_diff) / duration;
        int diff = w - old_w;
        if (diff > 0) {
          tft.fillRect(old_w, 0, diff, 16, BLUE);
        }
        old_w = w;
      }
    };
};

BatteryManager manager(batteries, active_batteries);
WristWatch watch;

unsigned long lastDraw = 0;

enum class DisplayState:byte {
  UNKNOWN,
  BOOTING,
  START_DELAY,
  INFO
};

#define DISPLAY_INFO_REDRAW_INTERVAL 3000

DisplayState display_state = DisplayState::BOOTING;
DisplayState old_display_state = DisplayState::UNKNOWN;
bool booting = true;


void setup() {
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);
  tft.begin();
  manager.begin();
}

void loop() {
  unsigned long cm = millis();

  if (old_display_state != display_state) {
    tft.fillScreen(BLACK);
    manager.draw_reset();
    watch.draw_reset();
    old_display_state = display_state;
  }

  manager.call(booting);

  switch (display_state) {
    case DisplayState::BOOTING:
      manager.draw_boot_info();
      watch.start(START_TIMER);
      display_state = DisplayState::START_DELAY;
      old_display_state = display_state;
      break;
    case DisplayState::START_DELAY:
      watch.loop();
      if (watch.finished()) {
        booting = false;
        display_state = DisplayState::INFO;
      } else {
        watch.draw();
      }
      break;
    case DisplayState::INFO:
      if ((cm - lastDraw) > DISPLAY_INFO_REDRAW_INTERVAL) {
        manager.draw_info();
        lastDraw = cm;
      }
      break;
    default:
      display_state = DisplayState::BOOTING;
      break;
  }
}
