"""
	EnsemblRest is a library for Python that wrap the EnsEMBL REST API.
	It simplifies all the API endpoints by abstracting them away from the
	end user and thus also ensures that an amendments to the library and/or
	EnsEMBL REST API won't cause major problems to the end user.

	Any questions, comments or issues can be made via gawbul@gmail.com
"""

__author__ = "Steve Moss"
__copyright__ = "Copyright 2013, Steve Moss"
__credits__ = ["Steve Moss"]
__license__ = "GPL"
__version__ = "0.0.1-dev"
__maintainer__ = "Steve Moss"
__email__ = "gawbul@gmail.com"
__status__ = "alpha"

import re
import sys
import requests
import json
from urlparse import parse_qsl

from ensembl_config import base_url, genomes_url, api_table, http_status_codes

class EnsemblRest(object):
	"""The REST API object"""
	def __init__(self, server=None, proxies=None):
		if server == None:
			server = get_default_url()

		self.server = server

		self.client = requests.Session()
		self.client.headers = {'Content-Type': 'application/json',
								'User-Agent': 'pyEnsemblRest v' + __version__}
		self.client.proxies = proxies

        # register available funcs to allow listing name when debugging.
		def setFunc(key):
			return lambda **kwargs: self._constructFunc(key, **kwargs)
		for key in api_table.keys():
			self.__dict__[key] = setFunc(key)

	def _constructFunc(self, api_call, **kwargs):
		# Go through and replace any mustaches that are in our API url.
		fn = api_table[api_call]
		url = re.sub(
			'\{\{(?P<m>[a-zA-Z_]+)\}\}',
			lambda m: "%s" % kwargs.get(m.group(1)), base_url + fn['url']
		)
		content = self._request(url, method=fn['method'], params=kwargs)

		return content

	def _request(self, url, method='GET', params=None, files=None, api_call=None):
		'''
			Internal response generator, no sense in repeating the same code twice, right? ;)
		'''
		method = method.lower()
		if not method in ('get', 'post'):
			raise Exception('Method must be of GET or POST')

		params = params or {}
		# requests doesn't like items that can't be converted to unicode,
		# so let's be nice and do that for the user
		for k, v in params.items():
			if isinstance(v, (int, bool)):
				params[k] = u'%s' % v

		func = getattr(self.client, method)
		if method == 'get':
			response = func(url, params=params)
		else:
			response = func(url, data=params, files=files)
		content = response.content.decode('utf-8')

		# create stash for last function intel
		self._last_call = {
			'api_call': api_call,
			'api_error': None,
			'cookies': response.cookies,
			'headers': response.headers,
			'status_code': response.status_code,
			'url': response.url,
			'content': content,
		}
		
		# wrap the json loads in a try, and defer an error
        # why? twitter will return invalid json with an error code in the headers
		json_error = False
		try:
			try:
				# try to get json
				content = content.json()
			except AttributeError:
				# if unicode detected
				content = json.loads(content)
		except ValueError:
			json_error = True
			content = {}

		return content

def get_default_url():
	return base_url

def get_genomes_url():
	return genomes_url

if __name__ == "__main__":
    server = get_default_url()
