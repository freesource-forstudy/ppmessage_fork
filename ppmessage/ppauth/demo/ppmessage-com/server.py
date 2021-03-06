# -*- coding: utf-8 -*-

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import tornado.httpclient

from data import BOOTSTRAP_DATA

import os
import json
import uuid
import logging

def createBodyString(params):
    body = ""
    for param in params:
        body += "&" + param + "=" + str(params[param])
    return body.lstrip("&")

def getAppServiceUserList(api_uuid, token):
    api_uri = API_URI + "/PP_GET_APP_SERVICE_USER_LIST"
    body = json.dumps({ "app_uuid": api_uuid })
    headers = {
        "Content-Type": "application/json",
        "Authorization": "OAuth " + token
    }
    request = tornado.httpclient.HTTPRequest(api_uri, method="POST", headers=headers, body=body)
    client = tornado.httpclient.HTTPClient()
    response = client.fetch(request)
    res_body = json.loads(response.body)
    return res_body

class AuthCallbackHandler(tornado.web.RequestHandler):
    def get(self):
        code = self.get_query_argument("code")
        state = self.get_query_argument("state")

        if state == "kefu":
            api_uuid = KEFU_API_UUID
            client_id = KEFU_CLIENT_ID
            client_secret = KEFU_CLIENT_SECRET
        elif state == "console":
            api_uuid = CONSOLE_API_UUID
            client_id = CONSOLE_CLIENT_ID
            client_secret = CONSOLE_CLIENT_SECRET
        else:
            self.send_error(400)
            return
        
        body = createBodyString({
            "code": code,
            "client_id": client_id,
            "redirect_uri": REDIRECT_URI,
            "client_secret": client_secret,
            "grant_type": "authorization_code"
        })

        request = tornado.httpclient.HTTPRequest(TOKEN_URI, method="POST", body=body)
        client = tornado.httpclient.HTTPClient()
        response = client.fetch(request)

        res_body = json.loads(response.body)
        logging.info(res_body)
        self.write("code: "+ code + "<hr>" + "state: " + state + "<hr>")
        for item in res_body:
            self.write(item + ": " + str(res_body[item]) + "<hr>")

        # a test
        user_list = getAppServiceUserList(api_uuid, res_body["access_token"])
        self.write("<h1>test getappserviceuserlist using access_token</h1>");
        for item in user_list:
            self.write(item + ": " + str(user_list[item]) + "<hr>")
        return
            
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        index_path = os.path.abspath(os.path.dirname(__file__)) + "/index.html";
        with open(index_path, "r") as f:
            self.write(f.read())
        return
    
class RequestKefuAuthHandler(tornado.web.RequestHandler):
    def get(self):
        params = {
            "state": "kefu",
            "client_id": KEFU_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code"
        }
        logging.info("request kefu auth params: %s" %params)
        target_url = AUTH_URI + "?" + createBodyString(params)
        self.redirect(target_url)
        return

class RequestConsoleAuthHandler(tornado.web.RequestHandler):
    def get(self):
        logging.info(" ------- %s" % self.request)
        params = {
            "state": "console",
            "client_id": CONSOLE_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code"
        }
        logging.info("request console auth params: %s" %params)
        target_url = AUTH_URI + "?" + createBodyString(params)
        self.redirect(target_url)
        return
    
class App(tornado.web.Application):
    def __init__(self):
        settings = {}
        settings["debug"] = True
        settings["static_path"] = os.path.abspath(os.path.dirname(__file__))
        handlers = [
            ("/", MainHandler),
            ("/request_kefu_auth", RequestKefuAuthHandler),
            ("/request_console_auth", RequestConsoleAuthHandler),
            ("/auth_callback", AuthCallbackHandler), 
        ]
        super(App, self).__init__(handlers, **settings)
        return
    
if __name__ == "__main__":
    server = "https://www.ppmessage.com"
    
    API_URI = server + "/api"
    AUTH_URI = server + "/ppauth/auth"
    TOKEN_URI = server + "/ppauth/token"
    REDIRECT_URI = "http://localhost:8090/auth_callback"

    kefu = BOOTSTRAP_DATA.get("THIRD_PARTY_KEFU")
    KEFU_API_UUID = kefu.get("api_uuid")
    KEFU_CLIENT_ID = kefu.get("api_key")
    KEFU_CLIENT_SECRET = kefu.get("api_secret")

    console = BOOTSTRAP_DATA.get("THIRD_PARTY_CONSOLE")    
    CONSOLE_API_UUID = console.get("api_uuid")
    CONSOLE_CLIENT_ID = console.get("api_key")
    CONSOLE_CLIENT_SECRET = console.get("api_secret")
    
    tornado.options.define("port", default=8090, help="", type=int)
    tornado.options.parse_command_line()
    app = App()
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(tornado.options.options.port)
    logging.info("Starting Auth Callback servcie.")
    tornado.ioloop.IOLoop.instance().start()
