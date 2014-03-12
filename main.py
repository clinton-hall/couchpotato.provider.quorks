[url]from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.providers.torrent.base import TorrentProvider
import traceback


log = CPLog(__name__)


class Quorks(TorrentProvider):

    urls = {
        'test' : 'https://quorks.net',
        'login' : 'https://quorks.net/takelogin.php',
        'login_check': 'https://quorks.net/index.php',
        'detail' : 'https://quorks.net/details.php?id=%s',
        'search' : 'https://quorks.net/browse.php?c%d=%d&search=%s&dead=active',
        'download' : 'https://quorks.net/downloadhttps.php/%s',
    }

    cat_ids = [
        ([28], ['720p', '1080p']),
        ([2], ['cam', 'ts', 'tc', 'r5', 'scr', 'dvdrip', 'brrip']),
        ([3], ['dvdr']),
    ]

    http_time_between_calls = 1 #seconds
    cat_backup_id = None

    def _searchOnTitle(self, title, movie, quality, results):

        url = self.urls['search'] % (self.getCatId(quality['identifier'])[0], self.getCatId(quality['identifier'])[0], 'title:"' + title.replace(':', '') + '"')
        data = self.getHTMLData(url)

        log.debug('Received data from Quorks')
        if data:
            log.debug('Data is valid from Quorks')
            html = BeautifulSoup(data)

            try:
                result_table = html.find('table', attrs = {'id' : 'browsetable'})
                if not result_table:
                    log.debug('No table results from Quorks')
                    return

                torrents = result_table.find_all('tr', attrs = {'class' : 'browse'})
                for result in torrents:
                    entry = result.find_all('table')
                    entry = entry[0].find_all('tr')
                    entry = entry[0].find_all('a')
                    details = entry[0]
                    release_name = details['title']
                    if self.conf('ignore_year') and not str(movie['library']['year']) in release_name:
                        words = title.replace(':','').split()
                        index = release_name.find(words[-1] if words[-1] != 'the' else words[-2]) + len(words[-1] if words[-1] != 'the' else words[-2]) +1
                        release_name = release_name[0:index] + '.(' + str(movie['library']['year']) + ').' + release_name[index:]
                    link = entry[0]
                    url = entry[1]
                    seed = result.find_all('b')
                    seeders = [item for item in seed if 'seeders' in item.find('a')['href']]
                    num_seeders = 0
                    num_leechers = 0
                    if len(seeders) > 0:
                        num_seeders = tryInt(seeders[0].get_text())
                    leechers = [item for item in seed if 'snatchers' in item.find('a')['href']]
                    if len(leechers) > 0:
                        num_leechers = tryInt(leechers[0].get_text())
                    size = [ item.get_text() for item in result.find_all('td') if ('GB' in item.get_text()) or ('MB' in item.get_text()) or ('KB' in item.get_text())]
                    results.append({
                        'id': result['torrentid'],
                        'name': release_name,
                        'url': self.urls['download'] % url['href'],
                        'detail_url': self.urls['download'] % details['href'],
                        'size': self.parseSize(size[0].replace(',','.')),
                        'seeders': num_seeders,
                        'leechers': num_leechers,
                    })

            except:
                log.error('Failed to parsing %s: %s', (self.getName(), traceback.format_exc()))

    def getLoginParams(self):
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
            'login': 'Einloggen!',
        }

    def loginSuccess(self, output):
        return 'logout.php' in output.lower() or 'Willkommen zur&uuml;ck' in output.lower()

    loginCheckSuccess = loginSuccess[/url]