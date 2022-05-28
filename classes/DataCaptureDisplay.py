import utils as ut
from classes import IMU
from classes import FrameGrabber
import styling as st
import constants as c

import PySimpleGUI as sg
from datetime import datetime as dt
from matplotlib.figure import Figure





class DataCaptureDisplay():
    def __init__(self):
        # Create initial directories for storing data.
        self.singleFramesPath, self.videosPath = ut.createInitialDirectories()
        # Record state of the program.
        self.enableRecording = False
        # Counter for labelling frame number in a recording.
        self.frameGrabCounter = 0
        # Time variables used to estimate frame rate of program.
        self.fpsCalc1 = dt.now().timestamp()
        self.fpsCalc2 = dt.now().timestamp()
        # IMU object instantiated with default values.
        self.imu = IMU.IMU()
        # Display FrameGrabber results.
        self.enableDisplay = True
        # Enable plot updates
        self.enablePlotting = True
        # FrameGrabber object instantiated with default values.
        self.frameGrabber = FrameGrabber.FrameGrabber()
        # Initial search for system COM ports.
        self.availableComPorts = IMU.availableComPorts()
        # Plotting variables, axis, points, lines, fig_agg, and bg set to None until initialised.
        self.ax = None
        self.pointData = None
        self.lineData = None
        self.fig_agg = None
        self.bg = None

        # Create overall layout.
        self.layout = self.createLayout()

        self.window = sg.Window('Ultrasound Data Capture', self.layout, finalize=True)

        self.createPlot(c.DEFAULT_AZIMUTH)

        self.run()

    def createLayout(self):
        imuColumnLayout = [
            [sg.Text('IMU Orientation Plot', size=(40, 1), justification='center', font=st.HEADING_FONT)],
            [sg.Canvas(key='-CANVAS-PLOT-', size=(500, 500))],
            [sg.Text('Select Azimuth')],
            [sg.Slider(key='-SLIDER-AZIMUTH-', range=(0, 360), default_value=c.DEFAULT_AZIMUTH, size=(40, 10),
                       orientation='h',
                       enable_events=True)],
            [sg.Text('IMU Controls', size=(40, 1), justification='center', font=st.HEADING_FONT,
                     pad=((0, 0), (20, 5)))],
            [sg.Button(key='-BUTTON-COM-REFRESH-', button_text='', image_source='icons/refresh_icon.png',
                       image_subsample=4, border_width=3),
             sg.Combo(key='-COMBO-COM-PORT-', values=self.availableComPorts, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Text('Baud Rate:', justification='right', font=st.DESC_FONT, pad=((20, 0), (0, 0))),
             sg.Combo(key='-COMBO-BAUD-RATE-', values=c.COMMON_BAUD_RATES, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True),
             sg.Button(key='-BUTTON-IMU-CONNECT-', button_text='Connect IMU', size=(15, 1), font=st.BUTTON_FONT,
                       border_width=3, pad=((40, 0), (0, 0)))],
            [sg.Combo(key='-COMBO-RETURN-RATE-', values=c.IMU_RATE_OPTIONS, size=7, font=st.COMBO_FONT,
                      enable_events=True, readonly=True, disabled=True)]

        ]

        layout = [[sg.Column(imuColumnLayout, element_justification='center')]]

        return layout

    def run(self):
        """
        Main loop for displaying the GUI and reacting to events, in standard PySimpleGUI fashion.
        """
        while True:
            # Update the plot
            self.updatePlot()

            event, values = self.window.read(timeout=0)

            if event == sg.WIN_CLOSED:
                self.close()
                break

            if event == '-SLIDER-AZIMUTH-':
                self.setAzimuth(int(values['-SLIDER-AZIMUTH-']))

            if event == '-BUTTON-COM-REFRESH-':
                self.refreshComPorts()

            if event == '-COMBO-COM-PORT-':
                self.imu.comPort = values['-COMBO-COM-PORT-']

            if event == '-COMBO-BAUD-RATE-':
                self.imu.baudRate = int(values['-COMBO-BAUD-RATE-'])

            if event == '-BUTTON-IMU-CONNECT-':
                self.toggleImuConnect()

            if event == '-COMBO-RETURN-RATE-':
                self.imu.setReturnRate(values['-COMBO-RETURN-RATE-'][:-2])

    def createPlot(self, azimuth):
        """
        Instantiate the initial plotting variables: The Figure and the axis. This is also called when changing
        the azimuth of the plot as the entire canvas needs to be redrawn.

        Args:
            azimuth (int): Azimuth angle in degrees.
        """
        fig = Figure(figsize=(5, 5), dpi=100)
        self.ax = fig.add_subplot(111, projection='3d')

        self.ax = ut.initialiseAxis(self.ax, azimuth)

        self.fig_agg = ut.drawFigure(fig, self.window['-CANVAS-PLOT-'].TKCanvas)

        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def updatePlot(self):
        """
        Update the plot to show orientation of the IMU unit.
        """
        # Only plot if plotting is enabled, the IMU is connected, and a quaternion value is available.
        if self.enablePlotting and self.imu.isConnected and self.imu.quaternion:
            self.fig_agg.restore_region(self.bg)

            self.ax = ut.plotPointsOnAxis(self.ax, self.imu.quaternion)

            self.fig_agg.blit(self.ax.bbox)
            self.fig_agg.flush_events()

    def setAzimuth(self, azimuth):
        """
        Set the azimuth of the plot to the slider value. This allows for aligning the plot to the user's orientation
        since the IMU orientation is based on magnetic north. The axis needs to be cleared first, then reinitialised
        to ensure a clean plot is saved for blitting purposes.

        Args:
            azimuth (int): Azimuth to set the displayed plot to.
        """
        # Clear axis.
        self.ax.cla()
        # Reinitialise axis.
        self.ax = ut.initialiseAxis(self.ax, azimuth)
        # Redraw new axis.
        self.fig_agg.draw()
        # Re-save background for blitting.
        self.bg = self.fig_agg.copy_from_bbox(self.ax.bbox)

    def refreshComPorts(self):
        """
        Refresh the available COM ports. The list of available COM ports is updated as well as the drop down menu/list.
        """
        self.availableComPorts = IMU.availableComPorts()
        self.window['-COMBO-COM-PORT-'].update(values=self.availableComPorts)

    def toggleImuConnect(self):
        """
        Toggles the connection state of the IMU object. If the IMU is connected, it will be disconnected, else it will
        be connected using the values set in the Combo boxes or using the default initialisation values.
        """

        # If imu is not connected it must be connected, else disconnected.
        if not self.imu.isConnected:
            self.imu.connect()
        else:
            self.imu.disconnect()
        # Set element states
        self.window['-COMBO-COM-PORT-'].update(disabled=True if self.imu.isConnected else False)
        self.window['-COMBO-BAUD-RATE-'].update(disabled=True if self.imu.isConnected else False)
        self.window['-BUTTON-IMU-CONNECT-'].update(
            button_color='#ff2121' if self.imu.isConnected else sg.DEFAULT_BUTTON_COLOR,
            text='Disconnect IMU' if self.imu.isConnected else 'Connect IMU'
        )
        self.window['-COMBO-RETURN-RATE-'].update(disabled=True if not self.imu.isConnected else False)

    def close(self):
        """
        Delete references to IMU and FrameGrabber objects for garbage collection. This ensures the resources are freed
        up for future use. Only called as the program is shutting down.
        """
        if self.imu.isConnected:
            self.imu.disconnect()
            del self.imu

        if self.frameGrabber.isConnected:
            del self.frameGrabber
