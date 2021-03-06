"""
Class for creating the menu bar based on the state of variables in DataCaptureDisplay class.
"""
import constants as c


class Menu:
    def __init__(self):
        # Set initial values
        self.frameGrabberConnected = False
        self.imuConnected = False
        self.signalMenu = None
        self.imuImenu = None
        # Initial creation of menus.
        self.__generateMenus()

    def getMenu(self, frameGrabberConnected=False, imuConnected=False):
        """
        Return the current menu bar based on the parameter values given. The local parameter values are updated based on
        the given parameters and the menus are generated. The generated menus are combined into a single menu bar layout
        and returned.

        Args:
            frameGrabberConnected (bool): True if FrameGrabber object is connected, else False.
            imuConnected (bool): True if IMU object is connected, else False.

        Returns:
            menuFinal (list): Final menu layout.
        """
        # Local variable update.
        self.frameGrabberConnected = frameGrabberConnected
        self.imuConnected = imuConnected
        # Generate menus.
        self.__generateMenus()

        menuFinal = [self.signalMenu, self.imuImenu]
        # Return menu bar layout.
        return menuFinal

    def __generateSignalMenu(self):
        """
        Function for creating signal source menus based on the connection status of the FrameGrabber object. For
        selecting the video source and changing its properties. If self.frameGrabberConnected:

        False (initial state):      Menu to show when the signal source is not connected. Since there is no signal,
                                    the signal properties cannot be changed.
        True (post connection):     Menu to show when the signal source is connected. Now that the source is connected,
                                    the source signal can be changed, it can be disconnected, and properties can be
                                    changed.
        """
        if not self.frameGrabberConnected:
            self.signalMenu = ['Signal Source', ['Connect to Source',
                                                 [f'{i}::-MENU-SIGNAL-CONNECT-' for i in
                                                  range(0, c.SIGNAL_SOURCES + 1)],
                                                 '---',
                                                 '!Change Signal Dimensions',
                                                 ]
                               ]
        if self.frameGrabberConnected:
            self.signalMenu = ['Signal Source', ['Disconnect from Source::-MENU-SIGNAL-DISCONNECT-',
                                                 '---',
                                                 'Change Signal Dimensions',
                                                 [f'{i[0]}::-MENU-SIGNAL-DIMENSIONS-' for i in
                                                  c.COMMON_SIGNAL_DIMENSIONS]
                                                 ]
                               ]

    def __generateImuMenu(self):
        """
        Function for creating imu menus based on the connection status of the IMU object. For controlling the
        connection to the IMU. if self.imuConnected:

        False (initial state):      Menu to show when the IMU is not connected. Since the IMU is not connected the
                                    return rate cannot be changed and the acceleration cannot be calibrated, so these
                                    options are disabled.
        True (post connection):     Menu to show when the IMU has been connected, enabling return rate and acceleration
                                    calibration.
        """
        if not self.imuConnected:
            self.imuImenu = ['IMU', ['Connect::-MENU-IMU-CONNECT-',
                                     '---',
                                     '!Set Return Rate',
                                     '!Calibrate Acceleration::-MENU-IMU-CALIBRATE-']
                             ]
        if self.imuConnected:
            self.imuImenu = ['IMU', ['Disconnect::-MENU-IMU-DISCONNECT-',
                                     '---',
                                     'Set Return Rate', [f'{i}::-MENU-IMU-RATE-' for i in c.IMU_RATE_OPTIONS],
                                     'Calibrate Acceleration::-MENU-IMU-CALIBRATE-']
                             ]

    def __generateMenus(self):
        """
        Function to call individual menu generating functions. More menus can be added, which now only require a single
        function to create the menu and a single call to this __generateMenus function.
        """
        # Signal Menu.
        self.__generateSignalMenu()
        # IMU Menu.
        self.__generateImuMenu()
