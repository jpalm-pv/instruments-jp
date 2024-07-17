import os
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from instruments.xystage.stepper_util import Stepper
import yaml
import logging

# Directory of the current file
XY_DIR = os.path.dirname(__file__)

def XY_UI():
    class XY(QMainWindow):
        """
        Main application window for XY coordinate tracking.
        """
        def __init__(self) -> None:
            super(XY, self).__init__()
            ui_path = os.path.join(XY_DIR, "xystage.ui")
            uic.loadUi(ui_path, self)
            self.setup_ui()
            self.show()

            self.scan_coordinates = {}  # Dictionary to store scan coordinates
            self.green_circles = []       # List to store references to green circle items

            # Load the hardware constants (offset, limits, etc.)
            self._constants_path = os.path.join(XY_DIR, 'hardware_constants.yaml')
            with open(self._constants_path, 'r') as file:
                self._constants = yaml.safe_load(file)

            logging.basicConfig(
                filename= os.path.join(XY_DIR, 'XYpy.log'),
                level = logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            
            self.update_current_status('Connecting to Arduino.')
            self.stepper = Stepper()
            self.update_current_status('Connected to Arduino. Ensure items are clear of the stage and Home Stage.')

        def setup_ui(self) -> None:
            """
            Setup the user interface elements.
            """
            self.xy_table = self.findChild(QTableWidget, 'xy_table')
            self.xy_table.setColumnCount(2)
            self.xy_table.setHorizontalHeaderLabels(['X', 'Y'])
            self.xy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            self.file_dialog = self.findChild(QPushButton, 'file_dialog')
            self.file_dialog.clicked.connect(self.open_file_dialog)

            self.file_label = self.findChild(QLabel, 'file_label')

            self.graphicsView = self.findChild(QGraphicsView, 'image_area')
            self.graphicsView.setMouseTracking(True)
            self.graphicsView.viewport().installEventFilter(self)
            self.scene = QGraphicsScene(self.graphicsView)

            self.take_scans_button = self.findChild(QPushButton, 'take_scans_button')
            self.take_scans_button.clicked.connect(self.take_scans)

            self.clear_points_button = self.findChild(QPushButton, 'clear_points_button')
            self.clear_points_button.clicked.connect(self.clear_points)

            self.home_stage_button = self.findChild(QPushButton, 'home_stage_button')
            self.home_stage_button.clicked.connect(self.gohome)

            # Add a button to save the scene as an image
            self.save_image_button = self.findChild(QPushButton, 'save_image_button')
            self.save_image_button.clicked.connect(self._save_scene_as_image)

            self.current_coords_label = self.findChild(QLabel, 'current_coords_label')
            self.current_status_label = self.findChild(QLabel, 'current_status')

            self.num_points = 0  # Counter for number of points added

        def eventFilter(self, widget, event):
            """
            Event filter to handle mouse events on the QGraphicsView.
            """
            if event.type() == QEvent.Resize and widget is self.graphicsView:
                self.graphicsView.fitInView(self.graphicsView.items()[0], Qt.KeepAspectRatio)
                return True

            elif widget == self.graphicsView.viewport() and event.type() == QEvent.Wheel and event.modifiers() == Qt.ControlModifier:
                scale = 1.25 if event.angleDelta().y() > 0 else 0.8
                self.graphicsView.scale(scale, scale)
                return True

            elif widget == self.graphicsView.viewport() and event.type() == QEvent.MouseButtonDblClick:
                view_pos = event.pos()
                scene_pos = self.graphicsView.mapToScene(view_pos)

                x = self._pixel_to_mm_BrightSpot(scene_pos.x())
                y = self._pixel_to_mm_BrightSpot(scene_pos.y())
                
                # make sure the point is in bounds before moving there
                if x > self._constants['coordinates']['x_max']:
                    self.update_current_status(f'Invalid x-coordinate! You chose: {x:0.3f},  Max is: {self._constants['coordinates']['x_max']}')
                    return False
                elif x < self._constants['coordinates']['x_min']:
                    self.update_current_status(f'Invalid x-coordinate! You chose: {x:0.3f},  Min is: {self._constants['coordinates']['x_min']}')
                    return False
                
                if y > self._constants['coordinates']['y_max']:
                    self.update_current_status(f'Invalid y-coordinate! You chose: {y:0.3f},  Max is: {self._constants['coordinates']['y_max']}')
                    return False
                elif y < self._constants['coordinates']['y_min']:
                    self.update_current_status(f'Invalid y-coordinate! You chose: {y:0.3f},  Min is: {self._constants['coordinates']['y_min']}')
                    return False

                if event.modifiers() == Qt.ControlModifier:
                    self.remove_last_green_circle()
                else:
                    self.num_points += 1
                    self.add_green_circle(scene_pos)
                    self.add_data_to_table(scene_pos.x(), scene_pos.y())

                return True

            return super().eventFilter(widget, event)

        def open_file_dialog(self):
            """
            Open file dialog to select an image file.
            """
            dlg = QFileDialog()
            dlg.setFileMode(QFileDialog.AnyFile)

            if dlg.exec_():
                self.xy_table.setRowCount(0)
                self.num_points = 0

                filename = dlg.selectedFiles()
                self.load_image(filename[0])

        def load_image(self, filename):
            """
            Load an image file into the QGraphicsView.
            """
            self.image = QPixmap(filename)
            item = QGraphicsPixmapItem(self.image)
            self.scene.clear()
            self.scene.addItem(item)
            self.graphicsView.setScene(self.scene)
            self.graphicsView.fitInView(item, Qt.KeepAspectRatio)

            self.file_label.setText(f'File Path: {filename}')

        def add_green_circle(self, scene_pos):
            """
            Add a green circle and associated text item at the given scene position.
            """
            green_brush = QBrush(QColor(50, 205, 50))
            green_circle = QGraphicsEllipseItem(-20, -20, 40, 40)
            green_circle.setBrush(green_brush)
            green_circle.setPos(scene_pos)

            text_item = QGraphicsTextItem(str(self.num_points))
            text_item.setDefaultTextColor(Qt.white)
            text_item.setFont(QFont("Arial", 40))
            text_item.setPos(scene_pos.x() - 40, scene_pos.y() - 90)

            self.scene.addItem(green_circle)
            self.scene.addItem(text_item)

            self.green_circles.append((green_circle, text_item))

        def remove_last_green_circle(self):
            """
            Remove the last added green circle and its associated text item.
            """
            if self.green_circles:
                del self.scan_coordinates[self.num_points]
                self.num_points -= 1
                last_green_circle, last_text_item = self.green_circles.pop()
                self.scene.removeItem(last_green_circle)
                self.scene.removeItem(last_text_item)
                self.xy_table.removeRow(self.xy_table.rowCount() - 1)

        def add_data_to_table(self, x_coord, y_coord):
            """
            Add coordinates to the table and scan coordinates dictionary.
            """
            row_position = self.xy_table.rowCount()
            self.xy_table.insertRow(row_position)

            x_mm = self._pixel_to_mm_BrightSpot(x_coord)
            y_mm = self._pixel_to_mm_BrightSpot(y_coord)
            
            item_x_coord = QTableWidgetItem(f'{x_mm:.3f}')
            item_y_coord = QTableWidgetItem(f'{y_mm:.3f}')

            self.scan_coordinates[self.num_points] = (x_mm, y_mm)
            self.xy_table.setItem(row_position, 0, item_x_coord)
            self.xy_table.setItem(row_position, 1, item_y_coord)

        def _pixel_to_mm_BrightSpot(self, pixel):
            """
            Convert pixel value to millimeters based on a calibration factor.
            """
            return pixel / 28.2588
        
        def take_scans(self):
            """
            Print the scan coordinates dictionary.
            """
            for k in self.scan_coordinates.keys():
                scan_x = self.scan_coordinates[k][0]
                scan_y = self.scan_coordinates[k][1]
                
                self.update_current_status(f'Moving to Point {k}: (X: {scan_x:0.3f}, Y: {scan_y:0.3f})')
                self.stepper.moveto(x_pos=scan_x, y_pos=scan_y)
                self.update_UI_coords()
                print(f'Moved to ({self.stepper.current_x:0.3f}, {self.stepper.current_y:0.3f})')

            self.update_current_status('Scanning complete.')

        def clear_points(self):
            """
            Clear all added points (green circles and table data).
            """
            self.xy_table.setRowCount(0)
            self.scan_coordinates.clear()

            for green_circle, text_item in self.green_circles:
                self.scene.removeItem(green_circle)
                self.scene.removeItem(text_item)

            self.green_circles.clear()
            self.num_points = 0

        def update_UI_coords(self):
            """
            Update the UI with the current coordinates.
            """
            self.current_coords_label.setText(f"X:{self.stepper.current_x:0.3f}, Y:{self.stepper.current_y:0.3f}")
            QApplication.processEvents()
        
        def update_current_status(self, text):
            """
            Update the current status label with the given text.
            """
            self.current_status_label.setText(f'Current Status: {text}')
            QApplication.processEvents()

        def _save_scene_as_image(self):
            """
            Save the QGraphicsScene as an image.
            """
            print('clicked')
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "JPEG Files (*.jpg);;All Files (*)")
            if file_path:
                # Determine the size of the scene
                rect = self.scene.sceneRect()

                # Create an image with the size of the scene
                image = QImage(int(rect.width()), int(rect.height()), QImage.Format_RGB16)

                # Create a painter to render the scene onto the image
                painter = QPainter(image)
                self.scene.render(painter)
                painter.end()

                # Scale the image to reduce its size
                scaled_image = image.scaled(int(rect.width() // 6), int(rect.height() // 6), Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Save the scaled image to the specified file path
                scaled_image.save(file_path)

        def gohome(self):
            """
            Move the stage to the home position.
            """
            self.update_current_status('Stage is going home...')
            self.stepper.gohome()
            self.update_current_status('Stage homed.')
            self.update_UI_coords()

        def closeEvent(self, event):
            """
            Confirm before closing the application.
            """
            reply = QMessageBox.question(
                self,
                "Message",
                "Are you sure you want to quit?",
                QMessageBox.Close | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            
            if reply == QMessageBox.Close:
                self.stepper.disconnect()
                event.accept()
            else:
                event.ignore()

    app = QApplication(sys.argv)
    window = XY()
    app.exec_()
