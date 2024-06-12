from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


class Keypad(HighLevelAnalyzer):
    """High level analyzer for Gardtec 490X remote keypad.

    Input Analyzer must be Async Serial with the following parameters:
        Bit rate: 1560 bits/s
        8 Bits per frame (different from display)
        1 Stop bit
        No Parity bit
        Most significant bit sent first
        Non inverted signal
        Normal mode
    """
    result_types = {
        'keypress': {
            'format': '{{data.key}}'
        }
    }

    def __init__(self):
        pass

    def decode(self, frame: AnalyzerFrame):
        if frame.type != 'data' or 'error' in frame.data:
            return

        result = []
        for d in frame.data['data']:
            if d == 0xFF:
                continue
            elif d >= 0xC0:
                d = ((d & 0x1F) << 3) | 0x07

            key = d >> 4

            result.append(AnalyzerFrame('keypress', frame.start_time, frame.end_time, {
                'key': '{:X}'.format(key)
            }))

        return result


class Display(HighLevelAnalyzer):
    """High level analyzer for Gardtec 490X remote keypad LCD status display.

    Input Analyzer must be Async Serial with the following parameters:
        Bit rate: 1560 bits/s
        7 Bits per frame (different from keypad)
        1 Stop bit
        No Parity bit
        Most significant bit sent first
        Non inverted signal
        Normal mode
    """
    result_types = {
        'status': {
            'format': '{{data.message}}'
        }
    }

    def __init__(self):
        self._frame_start_time = None
        self._frame_address = None
        self._frame_length = 0
        self._backlit = False
        self._message = []
        self._beeps = []
        self._bytes = []

    def _reset_frame(self, start_time=None, addr=None):
        self._frame_start_time = start_time
        self._frame_address = addr
        self._frame_length = 0
        self._backlit = False
        self._message.clear()
        self._beeps.clear()
        self._bytes.clear()

    def _is_backlit(self, d):
        self._backlit = (d & 0x40) == 0x40
        if d >= 0x40:
            return d ^ 0x40
        else:
            return d

    def decode(self, frame: AnalyzerFrame):
        if frame.type != 'data' or 'error' in frame.data:
            return

        result = []
        for d in frame.data['data']:
            if d in (0x7F, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07):
                self._reset_frame(frame.start_time, d)

            if self._frame_start_time is None:
                continue

            self._frame_length += 1
            self._bytes.append(d)

            if self._frame_length == 1:
                continue
            elif self._frame_length in (2, 15, 28):
                if self._frame_length == 15:
                    d = self._is_backlit(d)
                self._beeps.append(str(d))
                continue
            elif self._frame_length < 37:
                self._message.append(chr(d))
                if len(self._message) == 16:
                    self._message.append('\n')
                continue

            result.append(AnalyzerFrame('status', self._frame_start_time, frame.end_time, {
                'message': ''.join(self._message),
                'keypad': 'all' if self._frame_address == 0x7F else str(self._frame_address),
                'backlit': self._backlit,
                'beeps': ','.join(self._beeps),
                'eot': '{:02x}'.format(d),
            }))

            self._reset_frame()

        return result
