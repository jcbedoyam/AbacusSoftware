import cv2
import time
import numpy as np
import pytesseract as act
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from PIL import Image

def angle_cos(p0, p1, p2):
    d1, d2 = (p0-p1).astype('float'), (p2-p1).astype('float')
    return abs( np.dot(d1, d2) / np.sqrt( np.dot(d1, d1)*np.dot(d2, d2) ) )

def find_squares(img):
    img = cv2.GaussianBlur(img, (5, 5), 0)
    squares = []
    area = []
    center = []
    for gray in cv2.split(img):
        thrs = 150
        retval, bin = cv2.threshold(gray, thrs, 255, cv2.THRESH_BINARY)
        bin, contours, hierarchy = cv2.findContours(bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            cnt_len = cv2.arcLength(cnt, True)
            cnt = cv2.approxPolyDP(cnt, 0.02*cnt_len, True)
            area_ = cv2.contourArea(cnt)
            if len(cnt) == 4 and area_ > 1e3 and cv2.isContourConvex(cnt) and area_ < 1e5:
                cnt = cnt.reshape(-1, 2)
                max_cos = np.max([angle_cos(cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4] ) for i in range(4)])
                if max_cos < 0.1:
                    squares.append(cnt)
                    area.append(area_)
    return np.array(squares), area

def get_channels_only(img):
    squares, areas = find_squares(img)
    sorted_pos = np.argsort(areas)[::-1]

    squares = squares[sorted_pos]
    print(squares.shape)

    for i in range(squares.shape[0]):
        if i == 5:
            break
        try:
            square = squares[i]
        except IndexError:
            break
        distances = np.array([np.sum((center - square)**2) for center in squares])
        positions = np.where((distances > 0) & (distances < 100))
        squares = np.delete(squares, positions, axis=0)
    return squares[:5]

def order_contours(squares):
    height = (squares[:, 0, 1] + squares[:, -1, 1])*0.5
    return squares[np.argsort(height)]

def start_plot(squares):
    gs = gridspec.GridSpec(3, 3, width_ratios=[4, 1, 1])
    axes = [None] * 6
    plots = [None] * 6
    axes[0] = plt.subplot(gs[:, 0])
    axes[1] = plt.subplot(gs[0, 1])
    axes[2] = plt.subplot(gs[0, 2])
    axes[3] = plt.subplot(gs[1, 1])
    axes[4] = plt.subplot(gs[1, 2])
    axes[5] = plt.subplot(gs[2, 1:])

    axes[0].set_axis_off()
    for (i, ax) in enumerate(axes[1:]):
        squares[i].start_plot(ax)

    return axes

def create_squares(squares):
    return [Square(square) for square in squares]

class Square():
    def __init__(self, contour):
        self.contour = contour
        self.corners = self.get_corners(contour)
        self.axes = None
        self.plot = None
        self.image = None

    def get_corners(self, square):
        return square[0, 0], square[-1, 0], square[0, 1], square[1, 1]

    def start_plot(self, axes):
        self.axes = axes
        self.axes.set_axis_off()
        self.plot = self.axes.imshow(np.zeros((2, 2)))

    def set_contour(self, contour):
        self.contour = contour
        self.corners = self.get_corners(contour)

    def set_image(self, image):
        x0, x1, y0, y1 = self.corners
        self.image = image[y0:y1, x0:x1]

    def update_plot(self):
        self.plot.set_data(self.image)

img = cv2.imread('test.jpg')
contours = get_channels_only(img)
contours= order_contours(contours)
squares = create_squares(contours)

fig = plt.figure()
axes = start_plot(squares)
principal_plot = axes[0].imshow(np.zeros((2, 2)))

plt.ion() ## Note this correction

cam = cv2.VideoCapture(1)
cam.set(3,1280)
cam.set(4,1024)

while True:
    try:
        ret_val, img = cam.read()
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_cont = img.copy()
        contours = get_channels_only(img)
        if len(contours) == 5:
            contours = order_contours(contours)
            cv2.drawContours(img_cont, contours, -1, (0,255,0), 3)

            for (square, contour) in zip(squares, contours):
                square.set_contour(contour)
                square.set_image(img)
                square.update_plot()
        test_img = Image.fromarray(np.uint8(img))
        principal_plot.set_data(img_cont)
        plt.pause(1e-3) #Note this correction

    except KeyboardInterrupt:
        break
