"""
Run DashCast semi-persistently on a Chromecast while allowing other
Chromecast apps to work also by only launching when idle.
"""

from __future__ import print_function
import time
import os
import sys
import logging

import pychromecast
import pychromecast.controllers.dashcast as dashcast

print('DashCast')
print('Searching for Chromecasts...')

DASHBOARD_URL = os.getenv('DASHBOARD_URL', 'https://home-assistant.io')
DISPLAY_NAME = os.getenv('DISPLAY_NAME')
IGNORE_CEC = os.getenv('IGNORE_CEC') == 'True'

if IGNORE_CEC:
    print('Ignoring CEC for Chromecast', DISPLAY_NAME)
    pychromecast.IGNORE_CEC.append(DISPLAY_NAME)


if '--show-debug' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)


class DashboardLauncher():

    def __init__(self, device, dashboard_url='https://home-assistant.io', dashboard_app_name='DashCast'):
        self.device = device
        print('DashboardLauncher', self.device.name)

        self.controller = dashcast.DashCastController()
        self.device.register_handler(self.controller)

        receiver_controller = device.socket_client.receiver_controller
        receiver_controller.register_status_listener(self)

        self.dashboard_url = dashboard_url
        self.dashboard_app_name = dashboard_app_name

        # Check status on init.
        self.new_cast_status(self.device.status)
        # Launch dashboard on init.
        while True:
            self.launch_dashboard()
            time.sleep(60)

    def new_cast_status(self, cast_status):
        """ Called when a new cast status has been received. """
        print('new_cast_status', self.device.name, cast_status)

        def should_launch():
            """ If the device is active, the dashboard is not already active, and no other app is active. """
            print('should launch', self.is_device_active(), not self.is_dashboard_active(), not self.is_other_app_active())
            return (self.is_device_active()
                    and not self.is_dashboard_active()
                    and not self.is_other_app_active())

        if should_launch():
            print('might launch dashboard in 10 seconds')
            time.sleep(10)
        if should_launch():
            self.launch_dashboard()

    def is_device_active(self):
        """ Returns if there is currently an app running and (maybe) visible. """
        return (self.device.status is not None
                and self.device.app_id is not None
                and (self.device.status.is_active_input or self.device.ignore_cec)
                and (not self.device.status.is_stand_by and not self.device.ignore_cec))

    def is_dashboard_active(self):
        """ Returns if the dashboard is (probably) visible. """
        return (self.is_device_active()
                and self.device.app_display_name == self.dashboard_app_name)

    def is_other_app_active(self):
        """ Returns if an app other than the dashboard or the Backdrop is (probably) visible. """
        return (self.is_device_active()
                and self.device.app_display_name not in ('Backdrop', self.dashboard_app_name))

    def launch_dashboard(self):
        print('Launching dashboard on Chromecast', self.device.name)

        def callback(response):
            print('callback called', response)

        try:
            self.controller.load_url(self.dashboard_url, callback_function=callback)
        except Exception as e:
            print(e)
            pass


"""
Check for cast.socket_client.get_socket() and
handle it with cast.socket_client.run_once()
"""
"""
def main_loop():
    def callback(chromecast):
        print('found', chromecast)
        DashboardLauncher(chromecast, dashboard_url='http://192.168.1.132:8080')

    pychromecast.get_chromecasts(blocking=False, callback=callback)

    while True:
        time.sleep(1)

main_loop()
"""

casts = pychromecast.get_chromecasts()
if len(casts) == 0:
    print('No Devices Found')
    exit()

cast = next(cc for cc in casts if DISPLAY_NAME in (None, '') or cc.device.friendly_name == DISPLAY_NAME)

if not cast:
    print('Chromecast with name', DISPLAY_NAME, 'not found')
    exit()

DashboardLauncher(cast, dashboard_url=DASHBOARD_URL)

# Keep running
while True:
    time.sleep(1)

