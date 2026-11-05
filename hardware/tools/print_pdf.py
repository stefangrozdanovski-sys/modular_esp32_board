#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
"""Print an HTML file to PDF with headless Chromium (A4 from the page CSS).  usage: print_pdf.py in.html out.pdf"""
import asyncio, os, sys
from playwright.async_api import async_playwright

async def main(src, dst):
    async with async_playwright() as p:
        exe = '/opt/pw-browsers/chromium' if os.path.exists('/opt/pw-browsers/chromium') else None
        br = await p.chromium.launch(executable_path=exe)
        pg = await br.new_page()
        await pg.goto('file://' + os.path.abspath(src)); await pg.wait_for_timeout(500)
        await pg.pdf(path=dst, prefer_css_page_size=True, print_background=True)
        await br.close()
asyncio.run(main(*sys.argv[1:3]))
