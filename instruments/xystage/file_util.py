from stepper_util import Stepper
class FileHandler:
    def __init__(self):
        '''
        Utils responsible for writing coordinates from pyqt5 to file
        and for reading same file and running stepper moveto program  
        '''
        self.filename = 'coords.txt'

    def clear_file(self):
        '''
        Removes all contents from file for resetting program
        '''
        with open('filename.txt', 'w'):
            pass # in write mode all contents are deleted upon opening


    def append_coords(self, x_coord, y_coord):
        '''
        Puts x,y coords from pyqt5 into a file for storage and future retrieval
        '''
        f = open(self.filename, 'a') # append mode
        f.write(str(round(y_coord, 3)) + ',' + str(round(x_coord, 3)) + '\n')
        f.close()
    
    def read_coords_and_move(self, stepper: Stepper):
        '''
        Reads coordinates from file and calls stepper.moveto. Expects initialized stepper object
        '''
        f = open(self.filename, 'r') # read mode
        text = ""
        while text:
            text = f.readline()
            y_pos = float(text.split(',')[0]) # update the current y value
            x_pos = float(text.split(',')[1]) # update the current x value
            stepper.moveto(x_pos, y_pos)
        f.close()
    
    