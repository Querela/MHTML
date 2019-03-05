# pylint: disable=missing-docstring
# pylint: disable=protected-access
# pylint: disable=fixme

__version__ = '0.1.0'


import logging
import os


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


# ----------------------------------------------------------------------------


class MHTMLArchive:
    def __init__(self, content, headers, header_length, boundary):
        assert isinstance(content, bytes), 'content should be bytes'

        if not isinstance(headers, ResourceHeader):
            logger.warning('headers not from %s type: %s',
                           ResourceHeader.__qualname__, type(headers))
            headers = ResourceHeader()
            header_length = 0  # TODO: WIP

        if not boundary:
            # TODO: create boundary?
            pass

        self._headers = headers
        self._header_length = header_length
        self._boundary = boundary
        self._resources = list()
        self._content = bytearray(content)

    @property
    def resources(self):
        return self._resources

    @property
    def headers(self):
        return self._headers

    @property
    def content_type(self):
        # return get_content_type(self._headers)
        return self.headers.content_type

    @property
    def location(self):
        return self.headers.location

    @property
    def content(self):
        return bytes(self._content)

    @property
    def boundary(self):
        return self._boundary

    def _set_resources(self, resources):
        self._resources = resources

    def _update_offsets(self, amount, from_nr):
        for resource in self._resources[from_nr:]:
            resource._update_offsets(amount)

    def get_resource(self, nr):  # pylint: disable=invalid-name
        if nr < 0 or nr >= len(self._resources):
            return None
        return self._resources[nr]

    def remove_resource(self, nr):  # pylint: disable=invalid-name
        if nr < 0 or nr >= len(self._resources):
            return False

        # compute ranges
        boundary_length = len(self._boundary) + 4
        resource = self._resources[nr]
        start, end = resource.get_resource_range(boundary_length)

        # remove
        del self._content[start:end]
        del self._resources[nr]

        # update offsets of following resources
        resource_length = end - start
        self._update_offsets(-resource_length, nr)

        return True


class ResourceHeader:
    def __init__(self, headers=None):
        self._headers = list()

        if isinstance(headers, list):
            # self._headers.extend(headers)
            for name, value in headers:
                self[name] = value
        elif isinstance(headers, dict):
            for name, value in headers.items():
                # self._headers.append((name, value))
                self[name] = value

    @property
    def content_type(self):
        return get_content_type(self)

    @property
    def encoding(self):
        return self.get('Content-Transfer-Encoding')

    @property
    def location(self):
        loc = self.get('Snapshot-Content-Location')
        if loc:
            return loc

        return self.get('Content-Location')

    def __len__(self):
        return len(self._headers)

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        if name is None:
            logger.warning('Empty Header-key!, val=%s', value)
            return
        self._headers.append((str(name), value))

    def __delitem__(self, name):
        if name is None:
            return

        name = str(name).lower()
        for i in range(len(self._headers) - 1, -1, -1):
            if self._headers[i][0].lower() == name:
                del self._headers[i]

    def __contains__(self, name):
        if not name:
            return False

        return str(name).lower() in {n.lower() for n, _ in self._headers}

    def __iter__(self):
        # TODO: or yield (name, value)
        for name, _ in self._headers:
            yield name

    def items(self):
        # TODO: or return a copy for items()
        return self._headers

    def get(self, name, default=None):
        if name is None:
            return default

        name = str(name).lower()
        for key, value in self._headers:
            if key.lower() == name:
                return value

        return default

    def get_all(self, name, default=None):
        if default is None:
            default = list()

        if name is None:
            return default

        values = list()
        name = str(name).lower()
        for key, value in self._headers:
            if key.lower() == name:
                values.append(value)

        if values:
            return values

        return default

    def __eq__(self, other):
        # needed for assertions
        if not isinstance(other, self.__class__):
            return False
        return self._headers == other._headers

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return str(self._headers)

    def __repr__(self):
        # can be really wierd when in interactive mode ...
        return 'ResourceHeader: ' + repr(self._headers)

    def as_dict(self):
        ret = dict()
        for name, value in self._headers:
            ret[name] = value
        return ret

    def as_list(self):
        return self._headers.copy()


class Resource:
    # pylint: disable=too-many-arguments
    def __init__(self, mhtml_file, headers,
                 offset_start, offset_content, offset_end):
        assert isinstance(mhtml_file, MHTMLArchive), \
            'mhtml_file should be a MHTMLArchive'

        if not isinstance(headers, ResourceHeader):
            if isinstance(headers, (list, dict)):
                logger.debug('Converting list/dict headers into ResourceHeader')
                headers = ResourceHeader(headers)
            else:
                logger.warning('headers given are not from type %s: %s',
                               ResourceHeader.__qualname__, type(headers))
                headers = ResourceHeader()

        self._mhtml_file = mhtml_file
        self._headers = headers
        self._offset_start = offset_start
        self._offset_content = offset_content
        self._offset_end = offset_end
    # pylint: enable=too-many-arguments

    @property
    def headers(self):
        return self._headers

    @property
    def content_type(self):
        # return get_content_type(self._headers)
        return self.headers.content_type

    @property
    def location(self):
        return self.headers.location

    def get_short_filename(self, default='res.bin'):
        return make_filename(self._headers, default=default)

    @property
    def content(self):
        return self.get_content()

    def get_content(self):
        if not self._mhtml_file:
            return None
        if not self._mhtml_file._content:
            return None

        content = bytes(self._mhtml_file
                        ._content[self._offset_content:self._offset_end])
        encoding = self._headers.get('Content-Transfer-Encoding', None)
        if encoding == 'binary':
            # TODO: base64, quopri?
            return content
        return content

    @property
    def content_and_headers(self):
        if not self._mhtml_file:
            return None
        if not self._mhtml_file._content:
            return None

        content = bytes(self._mhtml_file
                        ._content[self._offset_start:self._offset_end])
        return content

    def get_resource_range(self, boundary_length=0):
        if boundary_length < 0:
            boundary_length = len(self._mhtml_file._boundary) + 4

        start = self._offset_start - boundary_length
        end = self._offset_end

        return start, end

    def _update_offsets(self, amount):
        self._offset_start += amount
        self._offset_content += amount
        self._offset_end += amount


# ----------------------------------------------------------------------------


def find_next_linebreak(content, from_pos):
    next_pos = content.find(b'\r\n', from_pos)
    if next_pos != -1:
        next_pos += 2
    return next_pos


def next_line(content, from_pos):
    next_pos = find_next_linebreak(content, from_pos)

    if next_pos == -1:
        line = content[from_pos:]
    elif next_pos == len(content):
        line = content[from_pos:]
        next_pos = -1
    else:
        while content[next_pos] == ord(b'\t'):
            next_pos = find_next_linebreak(content, next_pos)

        line = content[from_pos:next_pos]

    return line, next_pos


def parse_header(content, from_pos):
    header = ResourceHeader()
    next_pos = from_pos

    num_empty_lines = 0
    while next_pos != -1:
        line, next_pos = next_line(content, next_pos)

        if len(line) <= 2:
            num_empty_lines += 1
            break

        line = line[:-2]
        line = line.decode()

        parts = line.split(': ', 1)
        if len(parts) != 2:
            logger.warning('No separator in line: %s', line)
            continue

        header[parts[0]] = parts[1]

    assert num_empty_lines >= 1, 'after header at least one empty line!'

    return header, next_pos


def get_content_type(header_fields):
    ctype = header_fields.get('Content-Type', None)

    if ctype is None:
        logger.warning('No Content-Type?')
        return None

    if ';' not in ctype:
        return ctype

    return ctype.split(';', 1)[0]


def get_boundary(header_fields):
    ctype = header_fields.get('Content-Type', None)

    if ctype is None:
        logger.warning('No Content-Type?')
        return None
    if ';' not in ctype:
        logger.warning('Content-Type too short?')
        return None

    mimetype = ctype.split(';', 1)[0]
    if mimetype != 'multipart/related':
        logger.warning('Wrong mimetype, no multipart message?, %s', mimetype)
        return None

    bpos = ctype.find('boundary="')
    if bpos == -1:
        logger.warning('Missing boundary declaration?, %s', ctype)
        return None

    boundary = ctype[bpos:].split('"', 2)[1]
    # boundary = '--' + boundary

    return boundary


def make_filename(headers, folder=None, default='index.html',
                  guess_extension=True, ext_from_default=False):
    if not headers:
        return default

    name = headers.location
    if not name:
        return default

    name = name.split('?', 1)[0]
    name = name.split('#', 1)[0]
    name = name.rsplit('/', 1)[-1]
    name = name.split('=', 1)[0]

    if not guess_extension:
        if folder:
            name = os.path.join(folder, name)
        return name

    if '.' not in name:
        ext = None
        if not ext_from_default:
            ext = headers.content_type

        if not ext:
            if default and '.' in default:
                ext = default.rsplit('.', 1)[-1]
            else:
                ext = 'bin'
        else:
            # TODO: use `mimetype.guess_extension()` ?
            ext = ext.split('/')[-1]

        name = '{}.{}'.format(name, ext)

    if folder:
        name = os.path.join(folder, name)

    return name


def make_uniq_filename(name, pre_dup_str='dup_'):
    if os.path.exists(name):
        # check extension
        last_name = name.rsplit('/', 1)[-1]
        if '.' in last_name:
            ext = '.' + last_name.rsplit('.', 1)[-1]
            base = name[:-len(ext)]
        else:
            ext = ''
            base = name

        if pre_dup_str is None:
            pre_dup_str = ''

        # try renames
        dup_cnt = 1
        name = '{}.{}{}{}'.format(base, pre_dup_str, dup_cnt, ext)
        while os.path.exists(name):
            dup_cnt += 1
            name = '{}.{}{}{}'.format(base, pre_dup_str, dup_cnt, ext)
        logger.debug('Found duplicate output name, auto rename to: "%s"',
                     name)

    return name


def find_next_boundary(content, boundary, from_pos):
    needle = bytes('--' + boundary + '\r\n', 'ascii')
    next_pos = content.find(needle, from_pos)

    if next_pos == -1:
        needle_end = bytes('--' + boundary + '--\r\n', 'ascii')
        next_pos = content.find(needle_end, from_pos)
        if next_pos != -1 and next_pos + len(needle_end) == len(content):
            return next_pos, -1

        return next_pos, next_pos

    if content[next_pos - 2:next_pos] != b'\r\n':
        logger.debug('Found boundary in content?, %d, Search more ...',
                     next_pos)
        return find_next_boundary(content, boundary, next_pos + len(needle))

    return next_pos, next_pos + len(needle)


def parse_part(content, boundary, from_pos):
    start_pos = from_pos
    end_pos, next_pos = find_next_boundary(content, boundary, from_pos)

    if end_pos == -1:
        logging.debug('case -1 should not really happen anymore ...')
        end_pos = len(content)

    # TODO: remove last `\r\n` from content?
    # won't cause serious problems when kept ...

    # TODO: include boundary in start offset?

    headers, content_pos = parse_header(content, start_pos)

    return (headers, start_pos, content_pos, end_pos), next_pos


def parse_parts(content, boundary, from_pos):
    end_pos, next_pos = find_next_boundary(content, boundary, from_pos)

    if end_pos == -1:
        logger.warning('No parts in file?, %d', from_pos)
        return [], -1

    if from_pos != end_pos:
        logger.warning('Should have found first boundary?')

    parts = list()

    while next_pos != -1:
        logger.debug(next_pos)
        part_data, next_pos = parse_part(content, boundary, next_pos)
        parts.append(part_data)

    return parts, next_pos


def parse_mhtml(content):
    pos = 0

    # parse main header
    headers, header_end_pos = parse_header(content, 0)
    line, next_pos = next_line(content, header_end_pos)
    if len(line) != 2:
        logger.warning('After main header should follow two empty lines?, %d',
                       header_end_pos)
    else:
        header_end_pos = next_pos
    logger.debug('Header: %d -- %d: %s', pos, header_end_pos, headers)

    boundary = get_boundary(headers)
    if boundary is None:
        logger.warning('Found no boundary in header!')
        return headers, None
    logger.debug('Bounary: %s', boundary[2:])

    # parse body parts ...
    parts, parts_end_pos = parse_parts(content, boundary, header_end_pos)
    logger.debug('Got %d parts.', len(parts))
    assert parts_end_pos == -1, 'file should be completly parsed'
    return headers, parts


# ----------------------------------------------------------------------------


def parse_mhtml_struct(content, only_header=False):  # noqa: E501 pylint: disable=too-many-locals
    pos = 0

    # parse main header
    headers, header_end_pos = parse_header(content, 0)
    line, next_pos = next_line(content, header_end_pos)
    if len(line) != 2:
        logger.warning('After main header should follow two empty lines?, %d',
                       header_end_pos)
    else:
        header_end_pos = next_pos
    logger.debug('Header: %d -- %d: %s', pos, header_end_pos, headers)

    boundary = get_boundary(headers)
    if boundary is None:
        logger.warning('Found no boundary in header!')
    else:
        logger.debug('Bounary: %s', boundary[2:])

    mhtml_file = MHTMLArchive(content, headers, header_end_pos, boundary)

    if only_header:
        return mhtml_file

    # parse body parts ...
    parts, parts_end_pos = parse_parts(content, boundary, header_end_pos)
    logger.debug('Got %d parts.', len(parts))
    assert parts_end_pos == -1, 'file should be completly parsed'

    resources = list()
    for part_data in parts:
        headers, start_pos, content_pos, end_pos = part_data
        resource = Resource(mhtml_file, headers,
                            start_pos, content_pos, end_pos)
        resources.append(resource)
    mhtml_file._set_resources(resources)

    return mhtml_file


# pylint: disable=invalid-name
def MHTMLArchive_from_file(filename, only_header=False):  # noqa: N802
    with open(filename, 'rb') as fin:
        content = fin.read()

    return parse_mhtml_struct(content, only_header=only_header)


def MHTMLArchive_to_file(mhtml_archive, filename):  # noqa: N802
    with open(filename, 'wb') as fout:
        fout.write(mhtml_archive.content)
# pylint: enable=invalid-name


# EOF
