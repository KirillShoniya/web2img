import os
import asyncio

from argparse import ArgumentParser
from datetime import datetime

from aiohttp import web
from aiohttp import ClientSession
from pyppeteer import connect


class AsyncScreenshotMaker:
    def __init__(self):
        self._document_ready_timeout = int(os.environ['DOCUMENT_READY_TIMEOUT']) * 1000
        self._animation_ready_timeout = int(os.environ['ANIMATION_READY_TIMEOUT'])
        self._screenshot_path = os.environ['SCREENSHOT_PATH']
        self._filename_prefix = os.environ['FILENAME_PREFIX']
        self._ready_element_id = os.environ['READY_ELEMENT_ID']
        self._chrome_dev_host = os.environ['CHROME_WS_HOST']
        self._chrome_dev_port = os.environ['CHROME_WS_PORT']
        self._chrome_user_agent = os.environ['CHROME_UA']

        self._page = None
        self._width = 1920
        self._height = 1080

    async def get_debugger_ws_url(self):
        """
        Обращается к url дебагера для того,
        чтобы получить полный url дебагера с UUID

        :return: str
        """
        async with ClientSession() as session:
            try:
                async with session.get('http://{}:{}/json/version'.format(
                        self._chrome_dev_host, self._chrome_dev_port)) as resp:
                    chrome_info = await resp.json()
                    print('debugger порт: {}'.format(chrome_info['webSocketDebuggerUrl']))
                    return chrome_info['webSocketDebuggerUrl']
            except Exception as e:
                print('Не удалось получить WS URL Chrome: {}'.format(e))
                return ''

    async def code(self, request):
        """
        Возвращает код для вставки на страницу

        :return:
        """
        return web.Response(text="""
        <script type="text/javascript">
            $(document).ready(function() {
                $("body").append('<span id=" """ + self._ready_element_id + """ style="opacity: 0"></span>')
            })
        </script>""")

    @staticmethod
    async def return_400():
        """
        Возвращает 200 с JSON,
        описывающим 400 код состояния

        :return:
        """
        return web.json_response({
            'status': 400,
        })

    async def status(self, request):
        """
        Конечная точка для возвращения информации
        о статусе сервиса

        :return:
        """
        status = 200

        ws = await self.get_debugger_ws_url()
        if not ws:
            status = 500

        return web.json_response({
            'status': status,
        })

    async def make_screenshot(self, request):
        """
        Конечная точка для создания скриншота

        :param request:
        :return:
        """
        if 'id' not in request.query:
            return await self.return_400()

        if 'url' not in request.query:
            return await self.return_400()

        ws_url = await self.get_debugger_ws_url()
        if not ws_url:
            raise RuntimeError('Нет соединения с Chrome')

        browser = await connect({'browserWSEndpoint': ws_url})
        page = await browser.newPage()

        await page.setViewport({
            'width': self._width,
            'height': self._height,
        })

        await page.setUserAgent(self._chrome_user_agent)
        await page.goto(request.query['url'])

        # если ожидание селектора не отключено при запросе, ждем селектор
        if 'nw' not in request.query:
            await page.waitForSelector('#{}'.format(self._ready_element_id), timeout=self._document_ready_timeout)

        # ждем анимацию
        await asyncio.sleep(self._animation_ready_timeout)

        filename = '{}_{}.png'.format(
            self._filename_prefix,
            datetime.utcnow().timestamp()
        )

        path = '{}/{}'.format(
            self._screenshot_path,
            filename
        )

        opt = {
            'path': path,
        }

        if 'full_page' in request.query:
            opt['fullPage'] = True
        else:
            target_element = await page.querySelector("#{}".format(request.query['id']))
            element_size = await target_element.boxModel()

            await page.setViewport({
                'width': self._width,
                'height': element_size['height'],
            })

            await page.hover("#{}".format(request.query['id']))

            opt['clip'] = {
                'x': element_size['content'][0]['x'],
                'y': element_size['content'][0]['y'],
                'width': element_size['width'],
                'height': element_size['height'],
            }

        await page.screenshot(opt)
        await page.close()

        await browser.disconnect()

        return web.json_response({
            'status': 200,
            'id': request.query['id'],
            'result': '/static/{}'.format(filename)
        })


if __name__ == '__main__':
    a = ArgumentParser()
    a.add_argument('--host', required=False, type=str, default=None, help='Адрес на котором будет запущен сервер')
    a.add_argument('--port', required=False, type=int, default=None, help='Порт на котором будет запущен сервер')
    args = a.parse_args()

    handler = AsyncScreenshotMaker()

    app = web.Application()
    app.add_routes([
        web.get('/', handler.make_screenshot),
        web.get('/code', handler.code),
        web.get('/status', handler.status),
        web.static('/static/', os.environ['SCREENSHOT_PATH'])
    ])

    host = None
    port = None

    if args.host is None:
        host = os.environ['WEB_SERVER_HOST']

    if args.port is None:
        port = os.environ['WEB_SERVER_PORT']

    web.run_app(app, host=host, port=port)
