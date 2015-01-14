#!/usr/bin/env python

__author__ = "Gabor Szelcsanyi - szelcsanyi.gabor@gmail.com"
__license__ = "MIT"
__version__ = "0.1"


import datetime
import time
import hashlib
import urllib2
import sys
import os
import cStringIO
import resource

from PIL import Image

import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.log
import logging

from tornado.options import define, options

import swirl

image_save_path = '/web-data/share-proxy-pic'
image_format = 'png'
secret = '108ae6c6-9b27-11e4-96c1-3c970e5137c2'
max_width = 800
max_height = 600
logger = None

define("port", default=8081, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):
    global logger

    def get(self):
        try:
            url = self.get_argument('url')
            sign = self.get_argument('sign')
        except:
            raise tornado.web.HTTPError(status_code=500, log_message='Parameter missing', reason='Parameter missing')

        try:
            width = min(int(self.get_argument('width')), max_width)
        except:
            width = ''

        try:
            height = min(int(self.get_argument('height')), max_height)
        except:
            height = ''

        try:
            calculated_md5 = str(hashlib.md5(secret + str(url) + str(width) + str(height)).hexdigest())
            if calculated_md5 != str(sign) and calculated_md5 != str('0') + str(sign) and calculated_md5 != str('00') + str(sign):
                raise Exception
        except:
            raise tornado.web.HTTPError(status_code=500, log_message='Sign error (valid: %s)' % calculated_md5, reason='Sign error')

        try:
            image_file_dir = sign[:1] + '/' + sign[1:2] + '/' + sign[2:3]
            image_file_name = sign
            if os.path.exists(image_save_path + '/' + image_file_dir + '/' + image_file_name):
                logger.info('Image found. ' + image_file_name)
                self.do_serv(image_save_path + '/' + image_file_dir + '/' + image_file_name)
                return
        except:
            raise tornado.web.HTTPError(status_code=500, log_message='File search error ' + str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1]), reason='File search error')

        self.get_image(url, width, height, image_file_dir, image_file_name)

    @swirl.asynchronous
    def get_image(self, url, width, height, image_file_dir, image_file_name):
        logger.info("Fetching url: %s" % url)
        http = tornado.httpclient.AsyncHTTPClient()
        response = tornado.httpclient.HTTPResponse
        try:
            response = yield lambda cb: http.fetch(url, cb)
            logger.info('Response time: ' + str(response.request_time))
        except tornado.httpclient.HTTPError:
            raise tornado.web.HTTPError(status_code=500, log_message='Failed to fetch ' + url, reason='Failed to fetch')
        except Exception as e:
            raise tornado.web.HTTPError(status_code=500, log_message='Failed to fetch ' + url, reason='Failed to fetch')

        try:
            image = Image.open(response.buffer)
            width_convert = 0
            height_convert = 0
            if width == '':
                width = max_width
            if height == '':
                height = max_height

            if not os.path.exists(image_save_path + '/' + image_file_dir):
                logger.info('Creating directory: ' + image_file_dir)
                os.makedirs(image_save_path + '/' + image_file_dir)
                os.chmod(image_save_path + '/' + image_file_dir[:-4], 0755)
                os.chmod(image_save_path + '/' + image_file_dir[:-2], 0755)
                os.chmod(image_save_path + '/' + image_file_dir, 0755)

            logger.info("Required: %dx%d" % (width, height))
            logger.info("Image is: %dx%d" % (image.size[0], image.size[1]))

            if image.size[0] > width or image.size[1] > height:
                if image.size[0] > image.size[1]:
                    scale_with = float(width) / float(image.size[0])
                    newsize = (width, int(image.size[1] * scale_with))
                else:
                    scale_with = float(height) / float(image.size[1])
                    newsize = (int(image.size[0] * scale_with), height)
                image = image.resize(newsize, Image.ANTIALIAS)
                logger.info("Image scaled to: %dx%d" % (image.size[0], image.size[1]))
                image.save(image_save_path + '/' + image_file_dir + '/' + image_file_name, format=image_format, optimize=True)
            else:
                f = file
                f = open(image_save_path + '/' + image_file_dir + '/' + image_file_name, 'wb')
                f.write(response.body)
                f.close()

            os.chmod(image_save_path + '/' + image_file_dir + '/' + image_file_name, 0444)
            logger.info('Image saved. ' + image_file_name)
            self.do_serv(image_save_path + '/' + image_file_dir + '/' + image_file_name)
        except:
                raise tornado.web.HTTPError(status_code=500, log_message='Image processing error! ' + str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1]), reason='Image processing error')

    def do_serv(self, path):
        f = file
        try:
            f = open(path, 'rb')
            imagedata = f.read()
            self.set_header("Content-Type", "image")
            self.set_header("Cache-Control", "public, max-age=31536000")
            self.set_header("Expires", datetime.datetime.fromtimestamp(time.time() + 31536000))
            self.write(imagedata)
        except:
            raise tornado.web.HTTPError(status_code=500, log_message='Read error', reason='Read error')
        finally:
            if not f.closed:
                f.close()


def main():
    global logger

    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (15000, 15000))
    except:
        print "Cannot increase ulimit"

    try:
        tornado.options.parse_command_line()
        application = tornado.web.Application([
            (r".*", MainHandler),
        ])
        logger = logging.getLogger("tornado.application")
        logger.info("Starting application")
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        print "Error: %s", e

if __name__ == "__main__":
    main()
