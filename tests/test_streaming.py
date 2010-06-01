# -*- coding: utf-8 -*-
from unittest import TestCase
import poster
import webob
from paste import httpserver
import urllib2
import threading, time
import sys

poster.streaminghttp.register_openers()

port = 5123

class TestStreaming(TestCase):
    def setUp(self):
        self.request = None

        def app(environ, start_response):
            start_response("200 OK", [("Content-Type", "text/plain")])
            self.request = webob.Request(environ)
            # We need to look at the request's parameters to force webob
            # to consume the POST body
            # The cat is alive
            self.params = self.request.params
            return "OK"

        self.server = httpserver.WSGIServer(app, ("localhost", port), httpserver.WSGIHandler)

        self.server_thread = threading.Thread(target = self.server.handle_request)
        self.server_thread.start()

    def tearDown(self):
        self.server.server_close()
        self.server_thread.join()

    def _open(self, url, params=None, headers=None):
        if headers is None:
            headers = {}
        req = urllib2.Request("http://localhost:%i/%s" % (port, url), params,
                headers)
        return urllib2.urlopen(req)

    def test_basic(self):
        response = self._open("testing123")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(self.request.path, "/testing123")

    def test_basic2(self):
        response = self._open("testing?foo=bar")

        self.assertEqual(response.read(), "OK")
        self.assertEqual(self.request.path, "/testing")
        self.assertEqual(self.params.get("foo"), "bar")

    def test_nonstream_uploadfile(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        data = "".join(datagen)

        response = self._open("upload", data, headers)
        self.assertEqual(self.params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(self.params.get("foo"), "bar")

    def test_stream_uploadfile(self):
        datagen, headers = poster.encode.multipart_encode([
            poster.encode.MultipartParam.from_file("file", __file__),
            poster.encode.MultipartParam("foo", "bar")])

        response = self._open("upload", datagen, headers)
        self.assertEqual(self.params.get("file").file.read(),
                open(__file__).read())
        self.assertEqual(self.params.get("foo"), "bar")
