"""
A Python script for testing the battery life of an IMU by recording data until the IMU dies.
"""
from classes import IMU
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt
from pathlib import Path
import witmotion as wm
from matplotlib.figure import Figure
import utils as ut

# Location of refresh icon, stored for main program.
refreshIcon = str(Path().absolute().parent) + '\\icons\\refresh_icon.png'


class ImuBatterLifeTest:
    def __init__(self):
        # COM ports available on the system.
        self.availableComPorts = IMU.availableComPorts()
        # Number of messages received from the IMU device during a test.
        self.imuTestCounter = 0
        # File for saving IMU data of recording.
        self.drainTestsFile = None
        # IMU object and associated variables.
        self.imu = None
        self.comPort = 'COM3'
        self.baudRate = c.COMMON_BAUD_RATES[6]
        self.quaternion = None
        self.acceleration = None
        self.angle = None
        self.rotateIMUXY = False
        # Connection state of the IMU.
        self.isConnected = False
        # Plotting variables: axis, points, lines, fig_agg, and bg set to None until initialised.
        self.ax = None
        self.pointData = None
        self.lineData = None
        self.fig_agg = None
        self.bg = None
        # Is a test currently running.
        self.testing = False
        self.testStartTime = dt.now().timestamp()
        self.testLastMessageTime = dt.now().timestamp()
        self.testElapsedTime = self.testLastMessageTime - self.testStartTime
        # Create BatteryTests directory.
        self.batteryTestsPath = ut.createBatteryTestDirectory()

        # Layout creation.
        self.layout = self.createLayout()
        # Create main window for display.
        self.window = sg.Window('IMU Battery Tester', self.layout, finalize=True)

        self.createOrientationPlot(c.DEFAULT_AZIMUTH)

        # Display loop.
        while True:
            self.updateIMUValues()
            self.updateOrientationPlot()
            event, values = self.window.read(0)
            # Close window event (exit).
            if event == sg.WIN_CLOSED:
                break
            # Refresh available COM ports.
            if event == '-BUTTON-COM-REFRESH-':
                self.refreshComPorts()
            # Combo of available COM ports.
            if event == '-COMBO-COM-PORT-':
                self.comPort = values['-COMBO-COM-PORT-']
            # Combo of available baud rates.
            if event == '-COMBO-BAUD-RATE-':
                self.baudRate = int(values['-COMBO-BAUD-RATE-'])
            # Toggle IMU connection.
            if event == '-BUTTON-IMU-CONNECT-':
                self.toggleImuConnect()
            # Set azimuth.
            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(int(values['-SLIDER-AZIMUTH-']))
            # Toggle IMU XY flip/rotation.
            if event == '-BUTTON-ROTATE-XY-':
                self.toggleImuRotate()
            # Set the return rate of the IMU.
            if event == '-COMBO-RETURN-RATE-':
                self.imu.set_update_rate(float(values['-COMBO-RETURN-RATE-'][:-2]))
            # Calibrate IMU acceleration.
            if event == '-BUTTON-IMU-CALIBRATE-':
                self.imu.send_config_command(wm.protocol.ConfigCommand(register=wm.protocol.Register.calsw, data=0x01))
            # Start a timed test.
            if event == '-BUTTON-TEST-START-':
                self.toggleTest()
            # Stop a timed test.
            if event == '-BUTTON-TEST-STOP-':
                self.toggleTest()

        # Close IMU connections manually.
        print('Program closing down...')

        if self.isConnected:
            self.imu.ser.close()
            self.imu.close()

    def createLayout(self):
        """
        Create the layout for the program.

        Returns:
            layout (list): 2D list used by PySimpleGUI as the layout format.
        """
        # IMU controls.
        imuLayout = [
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (0, 20)))],
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source=refreshIcon,
                       image_subsample=4, border_width=3),
             sg.Combo(key='-COMBO-COM-PORT-', default_value=self.comPort, values=self.availableComPorts, size=7,
                      font=st.COMBO_FONT, enable_events=True, readonly=True),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', default_value=self.baudRate, values=c.COMMON_BAUD_RATES, size=7,
                      font=st.COMBO_FONT, enable_events=True, readonly=True)],
            [sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect IMU', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((0, 0), (20, 20)))],
            [sg.Text('Return Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-RETURN-RATE-', values=c.IMU_RATE_OPTIONS, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True, disabled=True),
             sg.Button(key='-BUTTON-IMU-CALIBRATE-', button_text='Calibrate Acc', size=(15, 1),
                       font=st.BUTTON_FONT, border_width=3, pad=((40, 0), (0, 0)), disabled=True)]
        ]
        # Orientation plot.
        imuPlotLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))],
            [sg.Text('Select Azimuth', font=st.DESC_FONT, pad=((0, 0), (5, 0)))],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=c.DEFAULT_AZIMUTH, size=(40, 10),
                       orientation='h', enable_events=True)],
            [sg.Text('Rotate IMU about plane: ', justification='left', font=st.DESC_FONT),
             sg.Button(key='-BUTTON-ROTATE-XY-', button_text='XY', border_width=3)]
        ]
        # IMU values from callback.
        imuValuesLayout = [
            [sg.Text('IMU Values (Raw)', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Text('Acceleration (m/s^2): ', justification='left', font=st.DESC_FONT, size=(20, 1)),
             sg.Text(key='-TEXT-ACCELERATION-', text='', justification='right', font=st.DESC_FONT, size=(30, 1))],
            [sg.Text('Quaternion: ', justification='left', font=st.DESC_FONT, size=(20, 1)),
             sg.Text(key='-TEXT-QUATERNION-', text='', justification='right', font=st.DESC_FONT, size=(30, 1))],
            [sg.Text('Euler Angles (deg): ', justification='left', font=st.DESC_FONT, size=(20, 1)),
             sg.Text(key='-TEXT-ANGLE-', text='', justification='right', font=st.DESC_FONT, size=(30, 1))]
        ]

        # Test start column.
        testStartLayout = [
            [sg.Text(text='Start Time', font=st.DESC_FONT + ' underline', size=(15, 1))],
            [sg.Text(key='-TEXT-TEST-START-', font=st.DESC_FONT, size=(15, 1))]
        ]

        # Test last message received column.
        testLastLayout = [
            [sg.Text(text='Last Message\nReceived At', font=st.DESC_FONT + ' underline', size=(15, 1))],
            [sg.Text(key='-TEXT-TEST-LAST-', font=st.DESC_FONT, size=(15, 1))]
        ]
        # Test elapsed time column.
        testElapsedLayout = [
            [sg.Text(text='Elapsed Time', font=st.DESC_FONT + ' underline', size=(15, 1))],
            [sg.Text(key='-TEXT-TEST-ELAPSED-', font=st.DESC_FONT, size=(15, 1))]
        ]
        # Test counter layout
        testCounterLayout = [
            [sg.Text(text='Total Messages', font=st.DESC_FONT + ' underline', size=(15, 1))],
            [sg.Text(key='-TEXT-TEST-COUNTER-', font=st.DESC_FONT, size=(15, 1))]
        ]
        # Test control layout.
        testControlLayout = [
            [sg.Button(key='-BUTTON-TEST-START-', button_text='Start', font=st.BUTTON_FONT, border_width=3,
                       pad=((0, 10), (20, 20)), disabled=True, button_color='#33ff77'),
             sg.Column(testStartLayout, element_justification='center', vertical_alignment='top'),
             sg.Column(testLastLayout, element_justification='center', vertical_alignment='top'),
             sg.Column(testElapsedLayout, element_justification='center', vertical_alignment='top'),
             sg.Column(testCounterLayout, element_justification='center', vertical_alignment='top'),
             sg.Button(key='-BUTTON-TEST-STOP-', button_text='Stop', font=st.BUTTON_FONT, border_width=3,
                       pad=((0, 10), (20, 20)), disabled=True, button_color='#ff2121')]
        ]
        # Total layout.
        layout = [
            [sg.Column(imuLayout, element_justification='center', vertical_alignment='top', justification='c')],
            [sg.HSep(pad=((0, 10), (10, 20)))],
            [sg.Column(imuPlotLayout, element_justification='center', vertical_alignment='top'),
             sg.Column(imuValuesLayout, element_justification='center', vertical_alignment='top')],
            [sg.HSep(pad=((0, 10), (10, 20)))],
            [sg.Column(testControlLayout, element_justification='center', vertical_alignment='top', justification='c')]
        ]

        return layout

    def toggleTest(self):
        """
        Toggle the testing state of the program. If true, IMU data will be stored in a .txt file, else close data file.
        """
        self.testing = not self.testing
        print(f'Start a test: {self.testing}')

        if self.testing:
            self.drainTestsFile = open(
                Path(self.batteryTestsPath, 'DrainTests.txt'), 'w')
            self.imuTestCounter = 0
            self.testStartTime = dt.now().timestamp()
        else:
            self.saveToFile()
            self.drainTestsFile.close()
            self.drainTestsFile = None

        # Set element states.
        self.window['-BUTTON-TEST-START-'].update(disabled=True if self.testing else False)
        self.window['-BUTTON-TEST-STOP-'].update(disabled=True if not self.testing else False)
        self.window['-TEXT-TEST-START-'].update(
            f"{dt.fromtimestamp(self.testStartTime).strftime('%H-%M-%S.%f')[:-3]}s" if self.testing else "")
        self.window['-TEXT-TEST-LAST-'].update('' if self.testing else "No Test Running")
        self.window['-TEXT-TEST-ELAPSED-'].update('')
        # self.window['-SLIDER-AZIMUTH-'].update(disabled=True if self.testing else False)
        self.window['-BUTTON-IMU-CONNECT-'].update(disabled=True if self.testing else False)
        self.window['-COMBO-RETURN-RATE-'].update(disabled=True if self.testing else False)
        self.window['-BUTTON-IMU-CALIBRATE-'].update(disabled=True if self.testing else False)

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop-down menu/list.
        """
        self.availableComPorts = IMU.availableComPorts()
        self.window['-COMBO-COM-PORT-'].update(values=self.availableComPorts)

    def toggleImuConnect(self):
        """
        Toggles the connection state of the IMU. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes.
        """

        # If imu is not connected it must be connected, else disconnected.
        if not self.isConnected:
            print(f'Attempting to connect to {self.comPort} at {self.baudRate}...')
            try:
                self.imu = wm.IMU(self.comPort, self.baudRate)
                self.imu.subscribe(self.imuCallback)
                self.isConnected = True
            except Exception as e:
                print(f'Error connecting to IMU: {e}.')
                self.isConnected = False
        else:
            print(f'Disconnecting from {self.comPort} as {self.baudRate}...')
            self.imu.close()
            self.imu.ser.close()
            self.isConnected = False
        # Set element states
        self.window['-COMBO-COM-PORT-'].update(disabled=True if self.isConnected else False)
        self.window['-COMBO-BAUD-RATE-'].update(disabled=True if self.isConnected else False)
        self.window['-BUTTON-IMU-CONNECT-'].update(
            button_color='#ff2121' if self.isConnected else sg.DEFAULT_BUTTON_COLOR,
            text='Disconnect IMU' if self.isConnected else 'Connect IMU'
        )
        self.window['-COMBO-RETURN-RATE-'].update(disabled=True if not self.isConnected else False)
        self.window['-BUTTON-IMU-CALIBRATE-'].update(disabled=True if not self.isConnected else False)
        self.window['-BUTTON-TEST-START-'].update(disabled=True if not self.isConnected else False)

    def createOrientationPlot(self, azimuth):
        """
        Instantiate the initial plotting variables: The Figure and the axis. This is also called when changing
        the azimuth of the plot as the entire canvas needs to be redrawn.

        Args:
            azimuth (int): Azimuth angle in degrees.
        """
        fig = Figure(figsize=(4, 4), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')
        fig.patch.set_facecolor(sg.DEFAULT_BACKGROUND_COLOR)
        self.ax.set_position((0, 0, 1, 1))

        self.ax = ut.initialiseAxis(self.ax, azimuth)
        self.ax.disable_mouse_rotation()

        self.fig_agg = ut.drawFigure(fig, self.window['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def updateOrientationPlot(self):
        """
        Update the plot to show orientation of the IMU unit.
        """
        # Only plot if the IMU is connected, and a quaternion value is available.
        if self.isConnected and self.quaternion:
            self.fig_agg.restore_region(self.bg)

            if self.rotateIMUXY:
                # Change here to include rotation change
                self.ax = ut.plotPointsOnAxis(self.ax, self.quaternion)
            else:
                self.ax = ut.plotPointsOnAxis(self.ax, self.quaternion)

            self.fig_agg.blit(self.ax.bbox)
            self.fig_agg.flush_events()

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north. The axis needs to be cleared first, then reinitialised
        to ensure a clean plot is saved for blit purposes.

        Args:
            azimuth (int): Azimuth to set the displayed plot to.
        """
        # Clear axis.
        self.ax.cla()
        # Reinitialise axis.
        self.ax = ut.initialiseAxis(self.ax, azimuth)
        # Redraw new axis.
        self.fig_agg.draw()
        # Re-save background for blit.
        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def imuCallback(self, msg):
        """
        Callback subscribed to the IMU object. Called whenever a new dataset is ready to be read. This callback is
        activated for every value sent by the IMU (Acceleration, Quaternion, Angle, ..etc) and not just for each
        serial packet. Only quaternion messages are read here, and the counter only increases when a quaternion
        message is read.

        Args:
            msg (String): The type of dataset that is newly available.
        """
        msg_type = type(msg)

        if msg_type is wm.protocol.AccelerationMessage:
            self.acceleration = self.imu.get_acceleration()
        elif msg_type is wm.protocol.AngleMessage:
            self.angle = self.imu.get_angle()
        elif msg_type is wm.protocol.QuaternionMessage:
            self.quaternion = self.imu.get_quaternion()
            self.testLastMessageTime = dt.now().timestamp()
            self.imuTestCounter += 1

    def updateIMUValues(self):
        """
        Update the shown IMU values if they are available.
        """
        if self.isConnected:
            if self.acceleration:
                self.window['-TEXT-ACCELERATION-'].update(
                    f'[{self.acceleration[0]:.4f}, {self.acceleration[1]:.4f}, {self.acceleration[2]:.4f}]')
            if self.quaternion:
                self.window['-TEXT-QUATERNION-'].update(
                    f'[{self.quaternion[0]:.4f}, {self.quaternion[1]:.4f}, {self.quaternion[2]:.4f}, '
                    f'{self.quaternion[3]:.4f}]')
            if self.angle and self.angle[0]:
                self.window['-TEXT-ANGLE-'].update(f'[{self.angle[0]:.4f}, {self.angle[1]:.4f}, {self.angle[2]:.4f}]')

            if self.testing:
                self.window['-TEXT-TEST-LAST-'].update(
                    f"{dt.fromtimestamp(self.testLastMessageTime).strftime('%H:%M:%S.%f')[:-3]}s")
                self.window['-TEXT-TEST-ELAPSED-'].update(
                    f"{dt.fromtimestamp(self.testLastMessageTime - self.testStartTime).strftime('%H:%M:%S')}s")
                self.window['-TEXT-TEST-COUNTER-'].update(
                    f'{self.imuTestCounter}'
                )

    def saveToFile(self):
        """
        Save details of the test to the DrainTests.txt file.

        Future note: Calling saveToFile from the IMU callback was causing threading issues as updating GUI from
        a non-main thread is a problem.
        """

        self.drainTestsFile.write(
            f"Drain Test Started: {dt.fromtimestamp(self.testStartTime).strftime('%d %m %Y - %H:%M:%S')},"
            f"Test Completed: {dt.fromtimestamp(dt.now().timestamp()).strftime('%d %m %Y - %H:%M:%S')}"
            f"Last Message: {dt.fromtimestamp(self.testLastMessageTime).strftime('%d %m %Y - %H:%M:%S')},"
            f"Run Time: {dt.fromtimestamp(self.testLastMessageTime - self.testStartTime).strftime('%d %m %Y - %H:%M:%S')},"
            f"Total Messages received: {self.imuTestCounter}\n")

    def toggleImuRotate(self):
        """
        Toggle the state of plane rotation for the IMU orientation plot. If the IMU is installed "upside down" the
        orientation needs to be flipped about the XY plane for the plot to match the physical movements of the IMU.
        This flip does not affect the displayed IMU values, only the orientation plot. Only flipping about XY plane
        for now.
        """
        self.rotateIMUXY = not self.rotateIMUXY

        self.window['-BUTTON-ROTATE-XY-'].update(
            button_color='#33ff77' if self.rotateIMUXY else sg.DEFAULT_BUTTON_COLOR)


ImuBatterLifeTest()
