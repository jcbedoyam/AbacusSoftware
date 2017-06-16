import os
import six
import matplotlib
from matplotlib.ticker import EngFormatter
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.backends.backend_qt5 import (QtCore, QtGui, QtWidgets, _getSaveFileName,
                        __version__, is_pyqt5)

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

class NavigationToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, figure, parent = None):
        NavigationToolbar2QT.__init__(self, canvas, figure)
        self.parent_window = parent
    # 
    # def matplotlib_save_figure(self):
    #     """Taken from matplotlib"""
    #     filetypes = self.canvas.get_supported_filetypes_grouped()
    #     sorted_filetypes = list(six.iteritems(filetypes))
    #     sorted_filetypes.sort()
    #     default_filetype = self.canvas.get_default_filetype()
    #
    #     startpath = matplotlib.rcParams.get('savefig.directory', '')
    #     startpath = os.path.expanduser(startpath)
    #     start = os.path.join(startpath, self.canvas.get_default_filename())
    #     filters = []
    #     selectedFilter = None
    #     for name, exts in sorted_filetypes:
    #         exts_list = " ".join(['*.%s' % ext for ext in exts])
    #         filter = '%s (%s)' % (name, exts_list)
    #         if default_filetype in exts:
    #             selectedFilter = filter
    #         filters.append(filter)
    #     filters = ';;'.join(filters)
    #
    #     fname, filter = _getSaveFileName(self.parent,
    #                                      "Choose a filename to save to",
    #                              start, filters, selectedFilter)
    #     if fname:
    #         if startpath == '':
    #             # explicitly missing key or empty str signals to use cwd
    #             matplotlib.rcParams['savefig.directory'] = startpath
    #         else:
    #             # save dir for next time
    #             savefig_dir = os.path.dirname(six.text_type(fname))
    #             matplotlib.rcParams['savefig.directory'] = savefig_dir
    #         try:
    #             ### MODIFIED PART
    #             if self.parent_window != None:
    #                 self.parent_window.currently_saving_fig = True
    #                 # self.parent_window.fig.canvas.draw()
    #                 # self.parent_window.restorePlot()
    #                 self.canvas.print_figure(six.text_type(fname))
    #                 self.parent_window.currently_saving_fig = False
    #             else:
    #                 self.canvas.print_figure(six.text_type(fname))
    #
    #         except Exception as e:
    #             QtWidgets.QMessageBox.critical(
    #                 self, "Error saving file", six.text_type(e),
    #                 QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton)
    #
    # def save_figure(self):
    #     self.matplotlib_save_figure()
