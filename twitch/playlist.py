import base64
from urllib.parse import quote_plus as urlencode

import m3u8
from m3u8 import M3U8

from twitch.constants import Twitch
from twitch.token import Token
from util.contents import Contents
from util.persistent_resource import PersistentJsonResource


class Playlist:
    __playlist_link_file = '~/.cache/twitch-dl/{}-playlist-link.json'

    def __init__(self):
        self.__token = Token()
        self.__best_quality_link_resource = None

    def fetch_for_channel(self, channel_name):
        if not self.__best_quality_link_resource:
            self.__best_quality_link_resource = PersistentJsonResource(
                self.__playlist_link_file.format(channel_name)
            )
            if self.__best_quality_link_resource.value():
                self.__try_playlist_link()
        if not self.__best_quality_link_resource.value():
            return self.__fetch_new(channel_name)
        return self.fetch_playlist(self.__best_quality_link_resource.value())

    def __try_playlist_link(self):
        playlist = self.fetch_playlist(self.__best_quality_link_resource.value())
        if len(playlist.segments) == 0:
            self.__best_quality_link_resource.clear()

    def __fetch_new(self, channel_name):
        token = self.__token.fetch_for_channel(channel_name)
        playlist_link = Twitch.channel_playlist_link.format(channel_name)
        return self.__fetch_playlist(playlist_link, token)

    def __fetch_playlist(self, playlist_link, source_format):
        playlist_container = self.fetch_playlist(playlist_link)
        if len(playlist_container.playlists) == 0:
            return playlist_container
        playlist_uri = next(
            (
                p.uri
                for p in playlist_container.playlists
                if p.stream_info.stable_variant_id.startswith(source_format)
            ),
            None
        ) if source_format else playlist_container.playlists[0].uri
        if playlist_uri:
            self.__best_quality_link_resource.store(playlist_uri)
        else:
            raise Exception("Can't find playlist by format \"{}\"".format(source_format))
        return self.fetch_playlist(self.__best_quality_link_resource.value())

    @staticmethod
    def fetch_playlist(link, token=None):
        raw_playlist = Contents.utf8(link, onerror=lambda _: None)
        if raw_playlist is None:
            return M3U8(None)
        return m3u8.loads(raw_playlist)

    def fetch_for_vod(self, vod_id, source_format):
        token = Token.fetch_for_vod(vod_id)
        playlist_link = self.build_playlist_link(token, vod_id)
        self.__best_quality_link_resource = PersistentJsonResource('/dev/null')
        playlist = self.__fetch_playlist(playlist_link, source_format)
        playlist.base_path = self.__best_quality_link_resource.value().rsplit('/', 1)[0]
        return playlist

    def list_formats_for_vod(self, vod_id):
        token = Token.fetch_for_vod(vod_id)
        playlist_link = self.build_playlist_link(token, vod_id)
        return self.__fetch_format_list(playlist_link)

    @staticmethod
    def build_playlist_link(token, vod_id) -> str:
        return Twitch.vod_playlist_link.format(
            vodId=vod_id,
            acmb=urlencode(
                base64.b64encode(Twitch.acmb_json.replace('#vodId', str(vod_id)).encode('utf-8')).decode('ascii')
            ),
            token=urlencode(token['value']),
            tokenSignature=urlencode(token['signature']),
        )

    def __fetch_format_list(self, playlist_link):
        playlist_container = self.fetch_playlist(playlist_link)
        if len(playlist_container.playlists) == 0:
            raise Exception('No formats found!')
        return [p.stream_info.stable_variant_id for p in playlist_container.playlists]
