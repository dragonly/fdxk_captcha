
# coding:utf8
#!/usr/bin/env python3
from __future__ import division

import os
import requests
import cv2
import numpy as np
import requests


import sys
sys.path.append('/usr/local/lib/python2.7/site-packages')

S = requests.Session()

def draw_contour(image_clean, image_color):
    im, contours, hierarchy = cv2.findContours(image_clean, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # Tracer()()
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # not entire image
        if w > 8:
            cv2.rectangle(image_color, (x,y), (x+w,y+h), (0,255,0), 1)

    # cv2.drawContours(image_color, contours, -1, (0,0,0), 1)

def get_stats(image):
    X, Y = image.shape
    image_stats = np.ones(image.shape, np.uint8) * 255
    stats = []
    for y in range(Y):
        black = 0
        for x in range(X):
            if image[x,y] == 0:
                black += 1
        stats.append(black)
        for x in range(black):
            image_stats[X-x-1,y] = 0
    return image_stats, stats

def split(stats):
    length = len(stats)
    pos_cut = []
    left = right = 0
    for i in range(len(stats)):
        if stats[i] != 0:
            break
        left += 1
    for i in reversed(range(len(stats))):
        if stats[i] != 0:
            break
        right += 1

    # first scan, make sure blank positions are cut points
    pos_blank = []
    last_pos = left
    i = left
    while i < length-right:
        if stats[i] == 0: # no pixel here
            pos_blank.append((last_pos, i))
            while stats[i] == 0: # skip following blank
                i += 1
            last_pos = i
        else:
            i += 1
    pos_blank.append((last_pos, i))

    # second scan, find valleys
    pos_valley = []
    down = False
    for i in range(left+1, length-right):
        if stats[i] < stats[i-1]:
            down = True
        elif stats[i] > stats[i-1]:
            if down: # seems encountering a valley!
                delta = max(abs(stats[i-1]-stats[i-2]), abs(stats[i-1]-stats[i]))
                pos_valley.append((i-1, delta))
            down = False
    dict_valley = dict(pos_valley)
    set_valley = set([i for i,j in pos_valley])

    total_length = 0
    for l,r in pos_blank:
        total_length += r - l
    avg_length = total_length / 4
    pos_n = []
    for l,r in pos_blank:
        n = int(round((r-l) / avg_length))
        pos_n.append(n)
    for i,n in enumerate(pos_n):
        if n > 1:
            l,r = pos_blank[i]
            avg_length = (r-l) / n # get a specific average length of this very slot
            pos_last = l
            for j in range(1,n):
                pos_chosen = pos = pos_l = pos_r = int(round(j*avg_length + l))
                min_pixel = 10
                # position of quaters are great, except for honorable reasons that should jump into a valley
                for delta in range(3):
                    pos_l = pos - delta
                    pos_r = pos + delta
                    if pos_l in set_valley and pos_r in set_valley:
                        if stats[pos_l] < stats[pos_r]:
                            if stats[pos_l]+delta < min_pixel:
                                pos_chosen = pos_l
                                min_pixel = stats[pos_l]
                        else:
                            if stats[pos_r]+delta < min_pixel:
                                pos_chosen = pos_r
                                min_pixel = stats[pos_r]
                    elif pos_l in set_valley:
                        if stats[pos_l]+delta < min_pixel:
                            pos_chosen = pos_l
                            min_pixel = stats[pos_l]
                    elif pos_r in set_valley:
                        if stats[pos_r]+delta < min_pixel:
                            pos_chosen = pos_r
                            min_pixel = stats[pos_r]
                    else:
                        pass
                    # print(pos_l, pos_r, pos_chosen)

                pos_cut.append((pos_last, pos_chosen))
                pos_last = pos_chosen

            pos_cut.append((pos_last, r))
        else:
            pos_cut.append(pos_blank[i])

    return pos_cut

def _estimate_max_digit_height(image_clean, cut_points):
    # estimate max height of each digits
    max_height = 0
    for y1,y2 in cut_points:
        block_height = 0
        line = []
        for x in range(X):
            for y in range(y1,y2):
                if image_clean[x,y] == 0:
                    line.append(1)
                    break
            line.append(0)
        top = bottom = 0
        for i in line:
            if i == 0:
                top += 1
            else:
                break
        for i in reversed(line):
            if i == 0:
                bottom += 1
            else:
                break
        block_height = X - top - bottom
        if block_height > max_height:
            max_height = block_height
    # print('iter %03d - block: %d' % (it, block_height))

def draw_split(stats):
    cut_points = split(stats)
    image_split = image_color.copy()
    for y1,y2 in cut_points:
        cv2.line(image_split, (y1,0), (y1,X), (0,0,0), 1)
        cv2.line(image_split, (y2,0), (y2,X), (0,0,0), 1)
    cv2.imwrite('xk_%03d_split.png' % it, image_split)

def _get_heights_in_range(image_clean, cut_points):
    X, Y = image_clean.shape
    pos_td = []
    pad_td = []
    for y1,y2 in cut_points:
        height = 0
        line = []
        for x in range(X):
            black = False
            for y in range(y1,y2):
                if image_clean[x,y] == 0:
                    black = True
                    break
            if black:
                line.append(1)
            else:
                line.append(0)
        # print(line)
        top = bottom = 0
        for i in line:
            if i == 0:
                top += 1
            else:
                break
        for i in reversed(line):
            if i == 0:
                bottom += 1
            else:
                break
        height = X - top - bottom
        padding_top = round((16 - height) / 2)
        pos_td.append((top, X-bottom))
        pad_td.append((padding_top, 16 - height - padding_top))
    return pos_td, pad_td

def _save_split_image(image_clean, cut_points):
    pos_lr = []
    pad_lr = []
    for left, right in cut_points:
        width = right - left
        padding_left = round((14 - width) / 2)
        pos_lr.append((left, right))
        pad_lr.append((padding_left, 14 - width - padding_left))
    pos_td, pad_td = _get_heights_in_range(image_clean, cut_points)

    for i in range(4):
        x1, x2 = pos_td[i]
        y1, y2 = pos_lr[i]
        pad_x1, pad_x2 = pad_td[i]
        pad_y1, pad_y2 = pad_lr[i]
        image = image_clean[x1:x2, y1:y2].copy()
        image_out = np.lib.pad(image, ((int(pad_x1),int(pad_x2)),(int(pad_y1),int(pad_y2))), 'constant', constant_values=255)
        assert(image_out.shape == (16,14))
        cv2.imwrite('split_%1d.png' % (i,), image_out)


def do_split(image_color):
    image_bin = cv2.cvtColor(image_color, cv2.COLOR_RGB2GRAY)
    image_clean = cv2.adaptiveThreshold(image_bin, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 30)
    image_stats, stats = get_stats(image_clean)
    cv2.imwrite('stats.png', image_stats)
    cut_points = split(stats)
    _save_split_image(image_clean, cut_points)

    X, Y = image_clean.shape
    image_split = image_color.copy()
    for y1,y2 in cut_points:
        cv2.line(image_split, (y1,0), (y1,X), (0,0,0), 1)
        cv2.line(image_split, (y2,0), (y2,X), (0,0,0), 1)
    cv2.imwrite('xk_split.png', image_split)

def main1():
    os.chdir('test')
    max_width = 0
    for it in range(1):
        response = requests.get('http://xk.fudan.edu.cn/xk/image.do')
        with open('xk_%03d.png' % it, 'wb') as fd:
            fd.write(response.content)
        image_color = cv2.imread('xk_%03d.png' % it)
        image_bin = cv2.cvtColor(image_color, cv2.COLOR_RGB2GRAY)
        image_clean = cv2.adaptiveThreshold(image_bin, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 30)
        cv2.imwrite('xk_%03d_clean.png' % it, image_clean)
        X, Y = image_clean.shape

        image_stats, stats = get_stats(image_clean)
        cv2.imwrite('xk_%03d_stats.png' % it, image_stats)

        cut_points = split(stats)
        # print(cut_points)

        # for l,r in cut_points:
        #     if r-l > max_width:
        #         max_width = r-l

        image_split = image_color.copy()
        for y1,y2 in cut_points:
            cv2.line(image_split, (y1,0), (y1,X), (0,0,0), 1)
            cv2.line(image_split, (y2,0), (y2,X), (0,0,0), 1)
        cv2.imwrite('xk_%03d_split.png' % it, image_split)
        # print('iter_%d - max width: %d' % (it, max_width))

def get_captcha():
    response = S.get('http://xk.fudan.edu.cn/xk/image.do')
    image_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
    image_color = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
    cv2.imwrite('xk.png', image_color)
    # image_color = cv2.imread('xk.png')

    image_bin = cv2.cvtColor(image_color, cv2.COLOR_RGB2GRAY)
    image_clean = cv2.adaptiveThreshold(image_bin, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 30)
    do_split(image_color)

def check_captcha(captcha):
    response = S.post('http://xk.fudan.edu.cn/xk/loginServlet', data={'studentId':'','password':'','rand':captcha,'Submit2':'Submit'})
    # print(response.content.decode('utf8'))
    return (u'登陆时间不正确' in response.content.decode('utf8'))

if __name__ == '__main__':
    response = requests.get('http://xk.fudan.edu.cn/xk/image.do')
    image_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
    image_color = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
    cv2.imwrite('xk.png', image_color)
    # image_color = cv2.imread('xk.png')

    image_bin = cv2.cvtColor(image_color, cv2.COLOR_RGB2GRAY)
    image_clean = cv2.adaptiveThreshold(image_bin, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 30)
    do_split(image_color)
