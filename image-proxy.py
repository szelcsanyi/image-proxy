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

from tornado.options import define, options

import swirl

image_save_path = '/tmp/pic'
image_format = 'png'
secret = '108ae6c6-9b27-11e4-96c1-3c970e5137c2'
max_width = 800
max_height = 600

define("port", default=8081, help="run on the given port", type=int)


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        try:
            url = self.get_argument('url')
            sign = self.get_argument('sign')
        except:
            print 'Parameter missing!'
            self.do_serv_error('Parameter missing!')
            return

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
            print "Sign error (valid: %s)" % (calculated_md5,)
            self.do_serv_error('Sign error')
            return

        try:
            image_file_dir = sign[:1] + '/' + sign[1:2] + '/' + sign[2:3]
            image_file_name = sign
            if os.path.exists(image_save_path + '/' + image_file_dir + '/' + image_file_name):
                print 'Image found. ' + image_file_name
                self.do_serv(image_save_path + '/' + image_file_dir + '/' + image_file_name)
                return
        except:
            print 'File search error ' + str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1])
            self.do_serv_error('File search error')
            return

        self.get_image(url, width, height, image_file_dir, image_file_name)

    @swirl.asynchronous
    def get_image(self, url, width, height, image_file_dir, image_file_name):
        http = tornado.httpclient.AsyncHTTPClient()
        response = tornado.httpclient.HTTPResponse
        try:
            response = yield lambda cb: http.fetch(url, cb)
            print 'Response time: ' + str(response.request_time)
        except:
            print 'Failed to fetch'
            self.do_serv_error('Failed to fetch')
            return

        try:
            image = Image.open(response.buffer)
            width_convert = 0
            height_convert = 0
            if width == '':
                width = max_width
            if height == '':
                height = max_height

            if not os.path.exists(image_save_path + '/' + image_file_dir):
                print 'Creating directory: ' + image_file_dir
                os.makedirs(image_save_path + '/' + image_file_dir)
                os.chmod(image_save_path + '/' + image_file_dir[:-4], 0755)
                os.chmod(image_save_path + '/' + image_file_dir[:-2], 0755)
                os.chmod(image_save_path + '/' + image_file_dir, 0755)
            print 'Saving file: ' + image_file_name

            print "Required: %dx%d" % (width, height)
            print "Image is: %dx%d" % (image.size[0], image.size[1])
            
            if image.size[0] > width or image.size[1] > height:
                if image.size[0] > image.size[1]:
                    scale_with = float(width) / float(image.size[0])
                    newsize = (width, int(image.size[1] * scale_with))
                else:
                    scale_with = float(height) / float(image.size[1])
                    newsize = (int(image.size[0] * scale_with), height)
                image = image.resize(newsize, Image.ANTIALIAS)
                image.save(image_save_path + '/' + image_file_dir + '/' + image_file_name, format=image_format, optimize=True)
            else:
                f = file
                f = open(image_save_path + '/' + image_file_dir + '/' + image_file_name, 'wb')
                f.write(response.body)
                f.close()

            os.chmod(image_save_path + '/' + image_file_dir + '/' + image_file_name, 0444)
            print 'Image generated. ' + image_file_name
            self.do_serv(image_save_path + '/' + image_file_dir + '/' + image_file_name)
        except:
                print 'Image processing error!' + str(sys.exc_info()[0]) + ' - ' + str(sys.exc_info()[1])
                self.do_serv_error('Image processing error')
                return

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
            self.do_serv_error("Read error")
        finally:
            if not f.closed:
                f.close()

    def do_serv_error(self, error):
        self.set_header("Content-Type", "text/plain")
        self.set_header("Cache-Control", "no-cache, must-revalidate")
        self.write("Error: %s\n" % (error,))
        self.set_status(500)


def main():
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (15000, 15000))
    except:
        print "Cannot increase ulimit"

    try:
        tornado.options.parse_command_line()
        application = tornado.web.Application([
            (r".*", MainHandler),
        ])
        http_server = tornado.httpserver.HTTPServer(application)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as e:
        print "Error: %s", e

if __name__ == "__main__":
    main()
