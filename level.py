from krita import (
        Krita,)

from PyQt5.QtCore import (
        Qt,
        QEvent,
        QPointF,
        QRect,
        QTimer)

from PyQt5.QtGui import (
        QTransform,
        QPainter,
        QBrush,
        QColor,
        QPolygonF,
        QInputEvent,
        QCursor)

from PyQt5.QtWidgets import (
        QWidget,
        QMdiArea,
        QTextEdit,
        QAbstractScrollArea)


def get_q_view(view):
    window = view.window()
    q_window = window.qwindow()
    q_stacked_widget = q_window.centralWidget()
    q_mdi_area = q_stacked_widget.findChild(QMdiArea)
    for v, q_mdi_view in zip(window.views(), q_mdi_area.subWindowList()):
        if v == view:
            return q_mdi_view.widget()


def get_q_canvas(q_view):
    scroll_area = q_view.findChild(QAbstractScrollArea)
    viewport = scroll_area.viewport()
    for child in viewport.children():
        cls_name = child.metaObject().className()
        if cls_name.startswith('Kis') and ('Canvas' in cls_name):
            return child


def get_transform(view):
    def _offset(scroller):
        mid = (scroller.minimum() + scroller.maximum()) / 2.0
        return -(scroller.value() - mid)
    canvas = view.canvas()
    document = view.document()
    q_view = get_q_view(view)
    area = q_view.findChild(QAbstractScrollArea)
    zoom = (canvas.zoomLevel() * 72.0) / document.resolution()
    transform = QTransform()
    transform.translate(
            _offset(area.horizontalScrollBar()),
            _offset(area.verticalScrollBar()))
    transform.rotate(canvas.rotation())
    transform.scale(zoom, zoom)
    return transform
    

def get_cursor_in_document_coords():
    app = Krita.instance()
    view = app.activeWindow().activeView()
    if view.document():
        q_view = get_q_view(view)
        q_canvas = get_q_canvas(q_view)    
        transform = get_transform(view)
        transform_inv, _ = transform.inverted()
        global_pos = QCursor.pos()
        local_pos = q_canvas.mapFromGlobal(global_pos)
        center = q_canvas.rect().center()
        return transform_inv.map(local_pos - QPointF(center))


class MyLogger(QTextEdit):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._ticker = QTimer(parent=self)
        self._ticker.setInterval(35)  # ms
        self._ticker.timeout.connect(self._on_tick)
        self._ticker.start()
        
    def _on_tick(self):
        app = Krita.instance()
        view = app.activeWindow().activeView()
        document = view.document()
        if document:
            center = QPointF(0.5 * document.width(), 0.5 * document.height())
            p = get_cursor_in_document_coords()
            doc_pos = p + center
            #self.append(f'cursor at: x={doc_pos.x()}, y={doc_pos.y()}')
            Krita.instance().activeDocument().setHorizontalGuides([doc_pos.y()])


my_logger = MyLogger()
my_logger.resize(400, 600)
my_logger.show()