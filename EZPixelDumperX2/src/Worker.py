"""工作线程模块 - CameraWorker和WebServerWorker。"""

from typing import Any, Callable

import numpy as np
from PySide6.QtCore import QThread, Signal

from flask import Flask, Response
import json
import logging


####### 相机工作线程 #######

class CameraWorker(QThread):
    """相机工作线程 - 使用DXCam持续捕获屏幕画面。"""

    ####### 信号定义 #######
    data_signal = Signal(np.ndarray, str)  # 图像数据信号 (array, status)
    log_signal = Signal(str)  # 日志信号

    def __init__(
        self,
        camera: Any,
        fps: int,
        region: tuple[int, int, int, int]
    ) -> None:
        """初始化相机工作线程。

        Args:
            camera: DXCamera实例
            fps: 目标捕获帧率
            region: 捕获区域 (left, top, right, bottom)
        """
        super().__init__()

        self._running: bool = False
        self.camera: Any = camera
        self.fps: int = fps
        self.region: tuple[int, int, int, int] = region

    def run(self) -> None:
        """主循环：使用DXCam捕获屏幕画面。"""
        self._running = True

        left, top, right, bottom = self.region

        try:
            # 启动DXCam捕获（自动按fps抓取并截取特定范围）
            self.camera.start(target_fps=self.fps, region=(left, top, right, bottom))

            while self._running and self.camera.is_capturing:
                # 获取最新帧（阻塞直到有新帧）
                frame: np.ndarray | None = self.camera.get_latest_frame()

                if frame is not None:
                    # DXCam返回的就是RGB np.ndarray，直接发送
                    self.data_signal.emit(frame, 'ok')

        except Exception as e:
            self.log_signal.emit(f'CameraWorker 发生错误: {e}')
            self._running = False

    def stop(self) -> None:
        """停止工作线程并释放资源。"""
        self._running = False

        # 停止DXCam捕获
        if hasattr(self.camera, 'stop'):
            self.camera.stop()

        # 释放DXCam资源
        if hasattr(self.camera, 'release'):
            self.camera.release()

        self.wait()


####### Web服务器工作线程 #######

class WebServerWorker(QThread):
    """Web服务器工作线程 - 在后台运行Flask HTTP服务器。"""

    def __init__(
        self,
        get_pixel_dump_callback: Callable[[], dict[str, Any]],
        host: str = '0.0.0.0',
        port: int = 65131
    ) -> None:
        """初始化Web服务器工作线程。

        Args:
            get_pixel_dump_callback: 获取像素数据的回调函数
            host: 监听主机地址
            port: 监听端口
        """
        super().__init__()

        self._get_pixel_dump: Callable[[], dict[str, Any]] = get_pixel_dump_callback
        self._host: str = host
        self._port: int = port
        self._app: Flask = Flask(__name__)

        # 注册路由
        self._setup_routes()

    def _setup_routes(self) -> None:
        """设置Flask路由。"""

        @self._app.route('/', defaults={'path': ''})
        @self._app.route('/<path:path>')
        def catch_all(path: str) -> Response:
            """捕获所有路径请求，返回像素数据JSON。

            Args:
                path: URL路径（忽略）

            Returns:
                JSON响应
            """
            pixel_dump: dict[str, Any] = self._get_pixel_dump()
            response: Response = Response(
                json.dumps(pixel_dump, indent=2, ensure_ascii=False),
                mimetype='application/json; charset=utf-8'
            )
            # 添加CORS头，允许跨域访问
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            return response

    def run(self) -> None:
        """线程运行方法 - 启动Flask服务器。"""
        # 禁用Flask的默认日志输出，保持控制台整洁
        log: logging.Logger = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        # 启动服务器（多线程模式处理并发请求）
        self._app.run(
            host=self._host,
            port=self._port,
            threaded=True,
            debug=False,
            use_reloader=False
        )

    def stop(self) -> None:
        """停止Web服务器（通过终止线程）。"""
        self.terminate()
        self.wait(1000)
