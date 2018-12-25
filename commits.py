#!/usr/bin/python

import datetime
import itertools
import json
import os
import subprocess
import sys


class Pixels(object):

  def __init__(self, width, height, pixels):
    self.width = width
    self.height = height
    self.pixels = pixels  # row major

  def active(self, w, h):
    return self.pixels[h * self.width + w]


def load_pixels(path):
  ret = {}

  pdict = json.loads(open(path, 'r').read())

  for char, data in pdict.iteritems():
    pixels = pdict[char]['pxif']['pixels']

    xindices = []
    yindices = []
    active = []

    for pixel in pixels:
      yindices.append(pixel['y'] / pixel['size'])
      xindices.append(pixel['x'] / pixel['size'])
      # Hackily detect alpha = 0 in pixels as used in ' '.
      active.append(not pixel['color'].endswith('0)'))

    width = max(xindices) + 1
    height = max(yindices) + 1

    pindices = [False] * width * height
    for x, y, a in zip(xindices, yindices, active):
      pindices[y * width + x] = a

    ret[char] = Pixels(width=width, height=height, pixels=pindices)

  return ret


def do_commit(curdate, c, x, y):
  args = [
      'git', 'commit', '--allow-empty',
      '--date=%s' % curdate.strftime('%Y.%m.%d'), '-m',
      'The letter of the day is %c (%d %d)' % (c, x, y)
  ]

  git = subprocess.Popen(args)
  git.wait()


def get_pixels(c, pixels):
  if not c in pixels:
    return pixels['?']
  return pixels[c]


def dates_for_string(instr, pixels, end=datetime.date.today()):

  weeks = 0

  for c in instr:
    p = get_pixels(c, pixels)
    weeks += p.width + 1

  start = end - datetime.timedelta(7 * weeks)
  start += datetime.timedelta(
      6 - start.weekday())  # 6 == Sunday, which is when we want to start

  if start < datetime.date(1970, 1, 1):
    raise ValueError(
        'Input string encoding requires history starting before the UNIX epoch (%s)'
        % start)

  curdate = start

  for c in instr:
    p = get_pixels(c, pixels)

    pad = 7 - p.height
    if pad < 0:
      raise ValueError('Pixel character height must be <= 7')

    # Characters that are less than 7 pixels in height require padding
    # days; we'll prefer top-padding to align on the baseline.
    if pad:
      bpad = pad / 2
      tpad = pad - bpad
    else:
      bpad = tpad = 0

    for x in range(0, p.width):
      curdate += datetime.timedelta(tpad)
      for y in range(0, p.height):
        if p.active(x, y):
          yield (curdate, c, x, y)
        curdate += datetime.timedelta(1)
      curdate += datetime.timedelta(bpad)

    curdate += datetime.timedelta(7)


def main(instr):
  pixels = load_pixels(os.path.join(os.path.dirname(__file__), 'alphabet.json'))

  # alphabet.json contains only lowercase definitions
  for date, char, x, y in dates_for_string(instr=instr.lower(), pixels=pixels):
    do_commit(date, char, x, y)


if __name__ == '__main__':
  main(sys.argv[1])
