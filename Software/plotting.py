from matplotlib.ticker import EngFormatter

class Axes(object):
    global EngFormatter
    def __init__(self, figure, canvas, axes, xmajor, ylabel, detectors):
        self.fig = figure
        self.points = []
        self.axes = axes
        self.ylimits = None
        self.status = False
        self.ylabel = ylabel
        self.canvas = canvas
        self.xmajor = xmajor
        self.background = None
        self.number_points = 0
        self.colors = {}
        self.labels = []
        self.xcoor = 0
        self.data = None

        self.init_lines(detectors)
        self.axes.set_ylabel(self.ylabel)
        self.size = self.get_size()

    def get_size(self):
        return self.axes.bbox.width, self.axes.bbox.height

    def init_lines(self, detectors):
        for detector in detectors:
            self.labels.append(detector.name)
            point = self.axes.plot([], [], "-o", ms=3, label = detector.name)[0]
            self.colors[detector.name] = point.get_color()
            self.points.append(point)
        self.number_points = len(self.points)
        self.ylimits = self.axes.get_ylim()
        self.axes.set_xlim(0, self.xmajor)
        self.axes.legend()
        self.axes.yaxis.set_major_formatter(EngFormatter())
        self.canvas.draw()
        self.set_background()

    def set_background(self):
        self.background = self.fig.canvas.copy_from_bbox(self.axes.bbox)

    def legend(self):
        self.axes.legend(self.points, self.labels, loc = 2)

    def change_status(self):
        self.status = all([last == now for (last, now) in \
                zip(self.ylimits, self.axes.get_ylim())])

    def update_plot(self):
        [self.points[i].set_data(self.xcoor, self.data[:, i+1]) for i in range(self.number_points)]

    def update_data(self, xcoor, data):
        max_ = []
        min_ = []
        self.xcoor = xcoor
        self.data = data
        self.change_status()
        for i in range(self.number_points):
            data_ = data[:, i+1]
            self.points[i].set_data(xcoor, data_)
            if self.status:
                max_.append(max(data_))
                min_.append(min(data_))
        if self.status:
            max_ = max(max_)*1.25
            min_ = min(min_)
            limits = self.axes.get_ylim()
            if(max_ > limits[1]\
               or min_ < limits[0]):
                self.axes.set_ylim(min_, max_)
                self.ylimits = self.axes.get_ylim()
                return True

        current_size = self.get_size()
        size_status = [abs(dim1 - dim2) > 1 for (dim1, dim2) in zip(self.size, current_size)]
        if not all(size_status):
            self.size = current_size
            return True
        return False

    def clean(self):
        self.axes.clear()

    def set_limits(self):
        self.axes.set_ylim(self.ylimits)
        self.axes.set_xlim(0, self.xmajor)
        self.axes.set_ylabel(self.ylabel)
        self.axes.yaxis.set_major_formatter(EngFormatter())
        self.legend()

    def draw_artist(self):
        [self.axes.draw_artist(line) for line in self.points]

    def blit(self):
        self.fig.canvas.blit(self.axes.bbox)
