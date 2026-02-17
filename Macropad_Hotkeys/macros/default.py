# SPDX-FileCopyrightText: 2021 Victor Toni - GitHub @vitoni
#
# SPDX-License-Identifier: MIT

# MACROPAD Hotkeys example: blank screen for idle


from adafruit_hid.consumer_control_code import ConsumerControlCode

app = {               # REQUIRED dict, must be named 'app'
    'name' : 'Default', # Application name
    'macros' : [      # List of button macros...
        # COLOR    LABEL    KEY SEQUENCE
        # 1st row ----------
        (0x200000, 'Mic Mute', [{'serial_cmd': 'MIC_TOGGLE'}]),
        (0x000020, '', []),
        (0x202020, 'Mute', [[ConsumerControlCode.MUTE]]),
        # 2nd row ----------
        (0x000000, '<<  ', [[ConsumerControlCode.SCAN_PREVIOUS_TRACK]]),
        (0x000020, '>>  ', [[ConsumerControlCode.SCAN_NEXT_TRACK]]),
        (0x202020, 'Play/Pause', [[ConsumerControlCode.PLAY_PAUSE]]),
        # 3rd row ----------
        (0x000000, '', []),
        (0x200000, '', []),
        (0x000000, '', []),
        # 4th row ----------
        (0x202000, 'Pages', [{'app_select': True}]),
        (0x002000, '', []),
        (0x202000, '', []),
        # Encoder button ---
        (0x000000, 'Mute', [[ConsumerControlCode.MUTE]])
    ]
}