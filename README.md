# Image proxy

## Description

Proxy, resize, optimize, share images via python script.
The script will fetch a remote picture, scale it if required, store it on local disk and return the final content.


## Purpose

* Embed images from remote sources. Store them locally preventing data loss on remote side.
* Scale images to fit your site requirements.
* Serve remote images over https channel to keep your site secure and control remote origins.


## Requirements

* Python 2.6, 2.7
* tornado
* swirl
* Pillow


## Config paramteres
* Define maximal image size. If the picture is bigger than this it will be scaled down. The original picture will be saved otherwise.
* Set the local storage path where the images will be saved.
* Set your secret key for url signing.
* Set your preferred output format, like png, jpg, etc.


## Sign key calculation

sign key = md5 of concatenate(secret key + url parameter + width parameter + height parameter)


## Usage

Point the url to your image-proxy instance:
* http://image.proxy:8081/?url=http://somewhere.com/example.jpg?sign=123
* http://image.proxy:8081/?url=http://somewhere.com/example.jpg?sign=123&width=800&height=600

The width and height parameters are optional.

The output will be a scaled png file stored in the storage location.
The images are returned with headers:
* Content-Type: image
* Cache-Control: public, max-age=31536000
* Expires: now + 31536000


## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Added some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create new Pull Request


## License

* Freely distributable and licensed under the [MIT license](http://szelcsanyi.mit-license.org/2015/license.html).
* Copyright (c) 2015 Gabor Szelcsanyi

[![image](https://ga-beacon.appspot.com/UA-56493884-1/image-proxy/README.md)](https://github.com/szelcsanyi/image-proxy)
