# Gardtec Utilities

Utilities to reverse engineer Gardtec 4-wire bus between a control panel and a remote keypad (GT490X model).


## Wiring

-  0V - ground 
- 12V - power
-  D1 - keypads TX, panel RX
-  D2 - panel TX, keypads RX

To tap a micro-controller or a logic analyser to the bus a level shifter is needed that is capable to convert signals as low as 1.5V to as high as 18V and vice versa.


## Protocol description

### Control Panel transmission

Over D2 line the control panel uses async serial connection with the following parameters:
- Bit rate: 1560 bits/s
- 7 Bits per frame (different from the keypad)
- 1 Stop bit
- No Parity bit
- Most significant bit sent first
- Non inverted signal
- Normal mode

The panel transmits 4-5 frames of data each second. The frequency of frames is just enough for LCD status display to update text (characters) for human readability.

A frame consists of 37 bytes:

| Index | Description                                   |
| ----- | --------------------------------------------- |
| 1     | Keypad number (1-4) or `0x7F` for all keypads |
| 2     | Beep A                                        |
| 3-14  | 12 characters of status text                  |
| 15    | Beep B with optional backlit mask `0x40`      |
| 16-27 | 12 more characters of status text             |
| 28    | Beep C                                        |
| 29-36 | 8 more characters of status text              |
| 37    | End of transmission (EOT)                     |

If the keypad number is other than `0x7F`, the frame is dedicated to a specific keypad, usually the one where a key is pressed. The other keypads if present on the line begin to display _System in use...Please WAIT_ status.

Beeps A, B and C if positive are in the range approximately from 15 to 25 setting frequency and level for the keypad internal sounder (piezo buzzer).

Characters of status text are of ASCII encoding. 32 characters of LCD display are split in 2 lines 16 characters each. 

EOT byte changes among `0x00`, `0x1c`, `0c14` in some chaotic order and can have other values when the panel installs a new keypad. 

### Remote Keypad transmission

Over D1 line the remote keypad uses async serial connection with the following parameters:
- Bit rate: 1560 bits/s
- 8 Bits per frame (different from the panel)
- 1 Stop bit
- No Parity bit
- Most significant bit sent first
- Non inverted signal
- Normal mode

Transmission from the keypad is synchronized with a frame received from the panel. If the panel does not transmit frames, the keypad is also silent.

The keypad number 1 (one) transmits heartbeats in sync with `3`, `17` and `31` bytes of the frame that is being received from the panel. The keypad number 2 (two) shifts its transmission to the next byte, i.e. `4`, `18` and `32`. The third keypad shifts to the next byte and so on. So, each keypad having a different number programmed, does not interfere with the others. 

Heartbeat is one byte `0xFF`. If a key is pressed then heartbeat `0xFF` is replaced with the value from _Code & Heartbeat_ column below.

In sync with 10 and 24 bytes of the frame, the keypad can transmit the code of a key pressed or the tamper code (`0xFF`). The code of a key pressed is the number from 0 to 11 specially encoded:

| Key |  Code  | Code & Heartbeat |
| --- | ------ | ---------------- |
|   0 | `0x07` | `0xC0`           | 
|   1 | `0x1F` | `0xC3`           |
|   2 | `0x27` | `0xC4`           |
|   3 | `0x3F` | `0xC7`           |
|   4 | `0x47` | `0xC8`           |
|   5 | `0x5F` | `0xCB`           |
|   6 | `0x67` | `0xCC`           |
|   7 | `0x7F` | `0xCF`           |
|   8 | `0x87` | `0xD0`           |
|   9 | `0x9F` | `0xD3`           |
|  No | `0xA7` | `0xD4`           |
| Yes | `0xBd` | `0xD7`           |

Using bitwise operations the Code and the Code & Heartbeat values can be converted to a number from 0 to 11 to find out the key pressed. 

The keypad can also transmit other codes when two keys pressed together, for example _1&3_, _7&9_, _PA1_, _PA2_ and _No+Yes_, but the codes that it transmits do not match the logic described above, so double presses are not supported.

Use Saleae Logic app to visualize sample sessions and see how data frames and keypad synchronization look like.
