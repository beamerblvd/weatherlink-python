"""
This script can be used is a proxy to intercept calls between WeatherLinkIP and the WeatherLink.com server. This
enables analysis of the protocol through which WeatherLinkIP communicates with the WeatherLink.com servers.

It should be called with `sudo python tests/scripts/http-proxy.py weatherlink.com [ip_address]` where [ip_address] is
the IP address on the network on which this script should listen. DNS (for the WeatherLinkIP device only) must be
configured to spoof weatherlink.com's DNS A record to point to the same IP address, otherwise it will not
intercept requests from the WeatherLinkIP device. If the DNS for the machine on which this script runs is also spoofed,
it will block indefinitely since this script handles only one connection at a time.

To exit the proxy, press Ctrl+C.
"""

from __future__ import absolute_import

import collections
import socket
import sys


def process_prelude(last_four, read_from, write_to):
	prelude = ''
	while True:
		data = read_from.recv(1)
		write_to.sendall(data)
		last_four.append(data)
		prelude += data
		if data == '\n':
			break
	return prelude


def process_headers(last_four, read_from, write_to):
	headers = {}
	while True:
		header = ''
		while True:
			data = read_from.recv(1)
			write_to.sendall(data)
			last_four.append(data)
			header += data
			if data == '\n':
				break
		header = header.strip()
		if header:
			k, v = header.strip().split(':', 1)
			headers[k.lower()] = v
		l4 = tuple(last_four)
		if l4 == ('\r', '\n', '\r', '\n') or l4[-2:] == ('\n', '\n'):
			break
	return headers


def process_data(headers, read_from, write_to):
	data = None
	if 'content-length' in headers:
		length = int(headers['content-length'])
		read_file = read_from.makefile()
		data = read_file.read(length)
		read_file.close()
		write_to.sendall(data)
	return data


def main():
	proxy_to, proxy_listen = sys.argv[1], sys.argv[2]
	print 'Proxying connections to server %s on address %s:80.' % (proxy_to, proxy_listen, )

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.bind((proxy_listen, 80))
	server.listen(1)

	i = 0
	while True:
		incoming = outgoing = None
		try:
			# Blocks until an application comes in
			incoming, _ = server.accept()

			i += 1
			print

			with open('tests/data/http-proxy-request-%s.bin' % i, 'wb') as handle:
				outgoing = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				outgoing.connect((proxy_to, 80))

				last_four = collections.deque(maxlen=4)

				# Read and forward the URL
				prelude = process_prelude(last_four, incoming, outgoing)
				print 'Passing through request to server: %s' % prelude.strip()
				handle.write(prelude)

				# Read and forward the headers
				headers = process_headers(last_four, incoming, outgoing)
				print 'Request headers: %s ' % headers
				handle.write('%s\n' % headers)

				# If there's a content length, we need to send data, too
				data = process_data(headers, incoming, outgoing)
				if data:
					print 'Data sent: %s' % repr(data)
					handle.write(data)
					handle.write('\n')
				handle.write('\n')

				last_four = collections.deque(maxlen=4)

				# Read and return the response
				prelude = process_prelude(last_four, outgoing, incoming)
				print 'Passing through response to client: %s' % prelude.strip()
				handle.write(prelude)

				# Read and return the headers
				headers = process_headers(last_four, outgoing, incoming)
				print 'Response headers: %s ' % headers
				handle.write('%s\n' % headers)

				# If there's a content length, we need to receive data, too
				data = process_data(headers, outgoing, incoming)
				if data:
					print 'Data received: %s' % repr(data)
					handle.write(data)
		except KeyboardInterrupt:
			server.close()
			print
			break
		finally:
			if incoming:
				try:
					incoming.close()
				except:
					pass

			if outgoing:
				try:
					outgoing.close()
				except:
					pass


main()
