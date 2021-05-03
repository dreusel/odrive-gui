#!/usr/bin/env python3
import streamlit as st
import odrive
from odrive.utils import dump_errors
import numpy as np
import session
import time

st.title("ODrive Tuning & Debugging")

@st.cache(allow_output_mutation=True)
def get_odrv():
    return odrive.find_any()

odrv = get_odrv()

state = session.get_state()
if not state.is_initialized:
    state.is_initialized = True
    state.axis_states = [
        odrv.axis0.current_state,
        odrv.axis1.current_state,
    ]
    state.control_modes = [
        odrv.axis0.controller.config.control_mode,
        odrv.axis1.controller.config.control_mode,
    ]
    state.vel = max(
        abs(odrv.axis0.controller.input_vel),
        abs(odrv.axis1.controller.input_vel),
    )
    state.input_vels = [
        odrv.axis0.controller.input_vel,
        odrv.axis1.controller.input_vel,
    ]
    state.pos_gains = [
        odrv.axis0.controller.config.pos_gain,
        odrv.axis1.controller.config.pos_gain,
    ]
    state.vel_gains = [
        odrv.axis0.controller.config.vel_gain,
        odrv.axis1.controller.config.vel_gain,
    ]
    state.vel_integrator_gains = [
        odrv.axis0.controller.config.vel_integrator_gain,
        odrv.axis1.controller.config.vel_integrator_gain,
    ]
    state.vel_limits = [
        odrv.axis0.controller.config.vel_limit,
        odrv.axis1.controller.config.vel_limit,
    ]

states = [
    'undefined',
    'idle',
    'startup sequence',
    'full calibration sequence',
    'motor calibration',
    'sensorless control',
    'encoder index search',
    'encoder offset calibration',
    'closed loop control',
    'lockin spin',
    'encoder dir find',
    'homing',
]

modes = [
    'voltage control',
    'torque control',
    'velocity control',
    'position control',
]

cols = st.beta_columns(2)

for a, axis in enumerate([odrv.axis0, odrv.axis1]):

    with cols[a]:

        st.header(f'Axis {a}')

        if axis.error:
            st.write('Error:', hex(axis.error))

        st.subheader('Settings')

        state.pos_gains[a] = axis.controller.config.pos_gain = st.number_input('pos_gain', min_value=0.0, value=state.pos_gains[a], key=f'number-pos_gain-{a}')
        state.vel_gains[a] = axis.controller.config.vel_gain = st.number_input('vel_gain', min_value=0.0, value=state.vel_gains[a], key=f'number-vel_gain-{a}')
        state.vel_integrator_gains[a] = axis.controller.config.vel_integrator_gain = st.number_input('vel_integrator_gain', min_value=0.0, value=state.vel_integrator_gains[a], key=f'number-vel_integrator_gain-{a}')
        state.vel_limits[a] = axis.controller.config.vel_limit = st.number_input('vel_limit', min_value=0.0, value=state.vel_limits[a], key=f'number-vel_limit-{a}')

        st.subheader('Test')

        state.control_modes[a] = axis.controller.config.control_mode = modes.index(st.radio('Mode', modes, state.control_modes[a], key=f'selectbox-mode-{a}'))

        if modes[state.control_modes[a]] == 'velocity control':
            st.write('input_vel:', state.input_vels[a])
            state.vel = st.number_input('new value', min_value=0.0, value=state.vel, key=f'number-vel-{a}')
            if st.button(f'Set input_vel = {-state.vel}', key=f'button-vel-{a}a'):
                state.input_vels[a] = axis.controller.input_vel = -state.vel
            if st.button('Set input_vel = 0.0', key=f'button-vel-{a}b'):
                state.input_vels[a] = axis.controller.input_vel = 0.0
            if st.button(f'Set input_vel = {state.vel}', key=f'button-vel-{a}c'):
                state.input_vels[a] = axis.controller.input_vel = state.vel

        state.axis_states[a] = axis.requested_state = states.index(st.selectbox('State', states, state.axis_states[a], key=f'selectbox-state-{a}'))
        for axis_state in ['idle', 'closed loop control']:
            if states[state.axis_states[a]] != axis_state:
                if st.button(f'Switch to "{axis_state}" state', key=f'button-{axis_state}-{a}'):
                    state.axis_states[a] = states.index(axis_state)

st.sidebar.header('ODrive')

st.sidebar.write('Serial number:', hex(odrv.serial_number).removeprefix('0x').upper())
st.sidebar.write('Hardware version:', f'{odrv.hw_version_major}.{odrv.hw_version_minor}.{odrv.hw_version_variant}')
st.sidebar.write('Firmware version:', f'{odrv.fw_version_major}.{odrv.fw_version_minor}.{odrv.fw_version_revision}', '(dev)' if odrv.fw_version_unreleased else '')
st.sidebar.write('Voltage:', np.round(odrv.vbus_voltage, 2))

if st.sidebar.button('Clear errors'):
    dump_errors(odrv, True)

if st.sidebar.button('Save configuration'):
    odrv.save_configuration()

if st.sidebar.button('Reboot'):
    odrv.reboot()

state.sync()

time_view = st.sidebar.json({})
while True:
    time_view.json({'t': time.time()})
    time.sleep(0.1)
