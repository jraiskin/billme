#!/usr/bin/env python

import json
import asyncio

import pyppeteer

# conda list -e > requirements.txt

_version = '0.0.2'
_supported_bills = {
    'hashmal': {
        'fields': {
            'contract number ("heshbon hoze")': {
                'input_value': '',
                'selector': "input[name*='BillContractNumber']",
            },
            'invoice 4 last digits ("kabala - makor")': {
                'input_value': '',
                'selector': "input[name*='BillLastFourDigits']",
            },
        },
        'next_btn_selector': "button[name*='BtnStep1']",
        'url': 'https://www.iec.co.il/pages/billspayment.aspx',
    },
    'TEST': {
        'fields': {
            'TEST1',
            'TEST2'
        }
    },
}
_indent = '\n    '
_greet = """Welcome to *billme* version {0[version]}
Current supported bills are referred to as:{0[indent]}{0[supported_bills]}
"""


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
    for field_name in db.get('fields').keys():
        print(field_name)
        # get field value from input
        input_str = validated_input(
            'Enter value for field: {}'.format(field_name),
            lambda x: True,
        )
        db['fields'][field_name]['input_value'] = input_str
    return db


async def launch_browser(url):
    print('Launching new browser instance, going to URL: {}'.format(url))

    browser = await pyppeteer.launch(headless=False)
    page = await browser.newPage()
    # page.setDefaultNavigationTimeout()
    print('Browser launched and page initiated')

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
        # requestUrl = request._url.split('?')[0].split('#')[0]
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
        {'waitUntil': 'load'}
    )
    await page.waitForNavigation({'waitUntil': 'networkidle0'})

    return browser, page


async def go_pmt_page(db):
    seed_url = db['url']
    fields = db['fields']
    browser, page = await launch_browser(seed_url)
    await asyncio.sleep(2)

    for field_name, field_attrs in db['fields'].items():
        print('Filling in details for field: {}'.format(field_name))
        element = await page.querySelector(field_attrs['selector'])
        print('query selector awaited')
        await element.type(field_attrs['input_value'])
        await asyncio.sleep(1)
    next_btn_element = await page.querySelector(db['next_btn_selector'])
    await next_btn_element.click()
    await asyncio.sleep(10000)


if __name__ == '__main__':
    print(
        _greet.format({
            'version': _version,
            'indent': _indent,
            'supported_bills': _indent.join(_supported_bills.keys())
        })
    )
    db = get_bill_inputs()
    pmt_page = go_pmt_page(db)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pmt_page)
