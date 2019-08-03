#!/usr/bin/env python

import json
import asyncio

import pyppeteer

# conda list -e > requirements.txt

_version = '0.0.2'
with open('params.json', encoding='utf-8') as f:
    _supported_bills = json.loads(f.read())
_indent = '\n    '
_greet = """Welcome to *billme* version {0[version]}
Current supported bills are referred to as:{0[indent]}{0[supported_bills]}
"""


# todo: remove? this is temporary fix
def patch_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect

    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method


def validated_input(
    request_str,
    validation_pred,
    except_str='',
):
    while True:
        try:
            input_str = input(request_str).strip()
            if not validation_pred(input_str):
                raise ValueError(except_str)
        except ValueError as e:
            print(e)
        else:
            break
    return input_str


def get_bill_inputs():
    bill_type = validated_input(
        'Enter your bill:',
        lambda x: x in _supported_bills.keys(),
        'ERROR: please choose one of: {}'.format(list(_supported_bills.keys()))
    )
    db = _supported_bills.get(bill_type)
    for stage in db.get('stages'):
        for field_name in stage.get('fields').keys():
            input_str = validated_input(
                'Enter value for field: {}'.format(field_name),
                lambda x: True,
            )
            stage['fields'][field_name]['input_value'] = input_str
    return db


async def launch_browser(url, block_media):
    print('Launching new browser instance, going to URL: {}'.format(url))

    patch_pyppeteer()

    browser = await pyppeteer.launch(headless=False)
    page = await browser.newPage()
    # page.setDefaultNavigationTimeout()
    print('Browser launched and page initiated')

    if block_media:
        # setup page properties
        await page.setRequestInterception(True)

        async def block_request(request):
            blockedResourceTypes = [
                'image',
                'media',
                'font',
                'texttrack',
                'object',
                'beacon',
                'csp_report',
                'imageset',
            ]
            if request.resourceType in blockedResourceTypes:
                await request.abort()
            else:
                await request.continue_()
            return None

        page.on(
            'request',
            lambda request: asyncio.ensure_future(block_request(request))
        )
    await page.goto(
        url,
        {'waitUntil': 'networkidle2'}
    )

    return browser, page


async def go_pmt_page(db, block_media):
    seed_url = db['url']
    stages = db['stages']
    browser, page = await launch_browser(seed_url, block_media)
    await asyncio.sleep(2)

    for stage in stages:
        for field_name, field_attrs in stage['fields'].items():
            if not field_attrs['input_value']:
                continue
            else:
                print('Filling in details for field: {}'.format(field_name))
                el_selector = field_attrs['selector']
                await asyncio.wait(
                    [page.waitForSelector(el_selector)],
                    timeout=1.0
                )
                element = await page.querySelector(el_selector)
                print('query selector awaited')
                print("field_attrs['input_value']: {}".format(field_attrs['input_value']))
                await element.type(field_attrs['input_value'])

        if stage['next_btn_selector']:
            next_btn = stage['next_btn_selector']
            print('stage[ next_btn_element ]: {}'.format(next_btn))
            await page.waitForSelector(next_btn)
            next_btn_element = await page.querySelector(next_btn)
            print('next_btn_element: {}'.format(next_btn_element))
            await asyncio.sleep(2)
            await next_btn_element.click()
            await asyncio.wait(
                [page.waitForNavigation({'waitUntil': 'networkidle2'})],
                timeout=2.0
            )
            print('Done waiting')

    await asyncio.sleep(10000)


async def main():
    print(
        _greet.format({
            'version': _version,
            'indent': _indent,
            'supported_bills': _indent.join(_supported_bills.keys())
        })
    )
    db = get_bill_inputs()
    pmt_page = await go_pmt_page(db, block_media=False)

    return pmt_page


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # https://stackoverflow.com/questions/53556006/the-connection-closed-when-code-running-which-use-pyppeteer-to-crawl-a-web
    # https://github.com/miyakogi/pyppeteer/issues/178
    # https://github.com/miyakogi/pyppeteer/pull/160/files
