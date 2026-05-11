from urllib.parse import parse_qs


def application(environ, start_response):
    get_params = parse_qs(environ.get('QUERY_STRING', ''))

    content_length = int(environ.get('CONTENT_LENGTH') or 0)
    body = environ['wsgi.input'].read(content_length) if content_length else b''
    post_params = parse_qs(body.decode('utf-8', errors='replace'))

    lines = ['GET parameters:']
    lines += [f'  {k} = {v}' for k, v in get_params.items()] or ['  (none)']
    lines += ['', 'POST parameters:']
    lines += [f'  {k} = {v}' for k, v in post_params.items()] or ['  (none)']

    response_body = '\n'.join(lines).encode('utf-8')
    start_response('200 OK', [
        ('Content-Type', 'text/plain; charset=utf-8'),
        ('Content-Length', str(len(response_body))),
    ])
    return [response_body]
