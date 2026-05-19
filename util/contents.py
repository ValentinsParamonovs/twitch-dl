from collections import namedtuple

import requests
from requests import codes as status, Response

from util.log import Log

Content = namedtuple('Content', 'decode')


class Error(Exception):
    def __init__(self, value):
        self.headers = value
        self.content = Content(decode=lambda _: value)
        self.json = lambda: value
        self.iter_content = lambda chunk_size: value


class Contents:
    @classmethod
    def utf8(cls, resource, params=None, headers=None, onerror=None):
        return cls.__raw(
            resource,
            params=params,
            headers=headers,
            onerror=onerror
        ).decode('utf-8')

    @classmethod
    def __raw(cls, resource, params=None, headers=None, onerror=None):
        return cls.__get_ok(
            resource,
            params=params,
            headers=headers,
            onerror=onerror
        ).content

    @classmethod
    def json(cls, resource, params=None, headers=None, onerror=None):
        return cls.__get_ok(
            resource,
            params=params,
            headers=headers,
            onerror=onerror
        ).json()

    @classmethod
    def __get_ok(cls, resource, params=None, headers=None, onerror=None):
        return cls.__check_ok(
            cls.__get(resource, params=params, headers=headers),
            onerror=onerror
        )

    @classmethod
    def cookies(cls, resource) -> dict[str, str | None]:
        try:
            return dict(cls.__check_ok(requests.get(resource)).cookies.items())
        except Exception as e:
            Log.fatal(str(e))
            return dict()

    @staticmethod
    def __get(resource, params=None, headers=None):
        try:
            return requests.get(
                resource,
                params=params,
                headers=headers,
                stream=True
            )
        except Exception as e:
            Log.fatal(str(e))

    @staticmethod
    def __check_ok(response: Response, onerror=None) -> Response:
        if response.status_code != status.ok:
            if onerror is None:
                Log.fatal(
                    'Failed to get {url}: got {statusCode} response'.format(
                        url=response.url,
                        statusCode=response.status_code
                    )
                )
            else:
                raise Error(onerror(response.status_code))
        return response

    @classmethod
    def chunked(cls, resource, onerror=None):
        return cls.__get_ok(resource, onerror=onerror).iter_content(chunk_size=2097152)

    @classmethod
    def post(cls, resource, params=None, headers=None, onerror=None, data=None):
        return cls.__check_ok(
            cls.__post(resource, params=params, headers=headers, data=data),
            onerror=onerror
        )

    @classmethod
    def __post(cls, resource, params, headers, data):
        try:
            return requests.post(
                resource,
                params=params,
                headers=headers,
                data=data,
                stream=True
            )
        except Exception as e:
            Log.fatal(str(e))
