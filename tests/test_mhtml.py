# pylint: disable=missing-docstring,invalid-name

import pytest

import mhtml


def test_get_content_type():
    # more verbose construction
    mock_headers = mhtml.ResourceHeader()
    mock_headers['Content-Type'] = 'text/html'
    assert mhtml.get_content_type(mock_headers) == 'text/html'

    # case insensitive
    assert mhtml.get_content_type(
        mhtml.ResourceHeader([('conTent-TyPe', 'text/html')])
        ) == 'text/html'

    # multipart/related
    assert mhtml.get_content_type(
        mhtml.ResourceHeader([('conTent-TyPe',
                               'multipart/related;\r\n\t...')])
        ) == 'multipart/related'

    # empty headers -> None
    assert mhtml.get_content_type(mhtml.ResourceHeader()) is None

    # no headers
    with pytest.raises(AttributeError):
        mhtml.get_content_type(None)

    # even standard dicts, but case sensitive
    assert mhtml.get_content_type({'Content-Type': 'text/abc'}) == 'text/abc'
    assert mhtml.get_content_type({'conTent-TyPe': 'text/abc'}) is None


def test_get_boundary():
    # no headers
    with pytest.raises(AttributeError):
        mhtml.get_boundary(None)

    # no content-type
    assert mhtml.get_boundary(mhtml.ResourceHeader()) is None
    # missing boundary declaration
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('conTent-TyPe', 'text/html')])
        ) is None

    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('conTent-TyPe',
                               'text/html;\r\n\tabc\r\n\tboundary="'
                               '---test-boundary---'
                               '"')])
        ) is None

    # has to be multipart
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('Content-Type',
                               'multipart/related;\r\n\tabc\r\n'
                               '\tnothing-here')])
        ) is None
    # has to be multipart and contain a boundary declaration
    assert mhtml.get_boundary(
        mhtml.ResourceHeader([('Content-Type',
                               'multipart/related;\r\n\tabc\r\n\tboundary="'
                               '---test-boundary---'
                               '"')])
        ) == '---test-boundary---'


def test_make_filename():
    # no headers given
    assert mhtml.make_filename(None, default='abc') == 'abc'
    # empty header
    assert mhtml.make_filename(mhtml.ResourceHeader(), default='abd') == 'abd'
    assert mhtml.make_filename(mhtml.ResourceHeader([('CH', 'CV')]),
                               default='abd') == 'abd'

    # assume we have extensions
    mock_headers = mhtml.ResourceHeader()
    mock_headers['Content-Location'] = 'proto://path/to/file.ext'
    assert mhtml.make_filename(mock_headers,
                               guess_extension=False) == 'file.ext'
    assert mhtml.make_filename(mock_headers, folder='abc',
                               guess_extension=False) == 'abc/file.ext'
    assert mhtml.make_filename(mock_headers,
                               guess_extension=True) == 'file.ext'
    assert mhtml.make_filename(mock_headers) == 'file.ext'

    # test guessing extensions
    del mock_headers['Content-Location']
    mock_headers['Content-Location'] = 'proto://path/to/file'

    assert mhtml.make_filename(mock_headers, default='abc.hhh') == 'file.hhh'
    # if not extension, then .bin ?
    assert mhtml.make_filename(mock_headers, default=None) == 'file.bin'
    assert mhtml.make_filename(mock_headers, default='ooo') == 'file.bin'

    assert mhtml.make_filename(mock_headers, default='lolo.olo',
                               ext_from_default=True) == 'file.olo'

    # add content-type
    mock_headers['Content-Type'] = 'myster/lexi'
    assert mhtml.make_filename(mock_headers, default='ooo.hhh') == 'file.lexi'
    assert mhtml.make_filename(mock_headers, folder='ddd/bbb/',
                               default='ooo.hhh') == 'ddd/bbb/file.lexi'
    del mock_headers['Content-Type']
    mock_headers['Content-Type'] = 'mystery'
    assert mhtml.make_filename(mock_headers) == 'file.mystery'

    # force use of default extension
    del mock_headers['Content-Location']
    mock_headers['Content-Location'] = 'proto://path/to/file'
    assert mhtml.make_filename(mock_headers, default='lolo.olo',
                               ext_from_default=True) == 'file.olo'


def test_make_uniq_filename(monkeypatch):
    import os.path

    name = 'abc'

    def mock_exists(fn):
        return fn == name

    monkeypatch.setattr(os.path, 'exists', mock_exists)
    assert mhtml.make_uniq_filename('abc', pre_dup_str='dpp_') == 'abc.dpp_1'
    assert mhtml.make_uniq_filename('abc', pre_dup_str='') == 'abc.1'
    assert mhtml.make_uniq_filename('abc', pre_dup_str=None) == 'abc.1'

    name2 = '/kljklk/jkllj/abcd.bi'

    def mock_exists2(fn):
        return fn == name2

    monkeypatch.setattr(os.path, 'exists', mock_exists2)
    assert mhtml.make_uniq_filename(name2, pre_dup_str=None) \
        == name2[:-2] + '1.bi'

    def mock_exists3(fn):
        return fn in (name, name + '.dpd_1')

    monkeypatch.setattr(os.path, 'exists', mock_exists3)
    assert mhtml.make_uniq_filename('abc', pre_dup_str='dpd_') == 'abc.dpd_2'

    monkeypatch.setattr(os.path, 'exists', lambda _: False)
    assert mhtml.make_uniq_filename('abc', pre_dup_str='dpd_') == 'abc'
    assert mhtml.make_uniq_filename('abcd', pre_dup_str='dpd_') == 'abcd'


# ---------------------------------------------------------------------------


def test_find_next_linebreak():
    assert mhtml.find_next_linebreak(b'', 0) == -1
    # index after linebreak, start of new content
    assert mhtml.find_next_linebreak(b'abc\r\ndef', 0) == 5
    assert mhtml.find_next_linebreak(b'abc\r\ndef', 6) == -1

    # currently wants '\r\n' as separator
    assert mhtml.find_next_linebreak(b'abc\rdef', 0) == -1
    assert mhtml.find_next_linebreak(b'abc\ndef', 0) == -1

    assert mhtml.find_next_linebreak(b'abc\r\ndef', -1) == -1

    # works on bytes
    with pytest.raises(TypeError):
        mhtml.find_next_linebreak('abc\r\ndef', 0)


def test_next_line():
    assert mhtml.next_line(b'', 0) == (b'', -1)
    assert mhtml.next_line(b'abc\r\ndef', 0) == (b'abc\r\n', 5)
    assert mhtml.next_line(b'abc\r\ndef', 1) == (b'bc\r\n', 5)

    # with linebreak continuation
    assert mhtml.next_line(b'abc;\r\n\tcba\r\ndef', 1) == \
        (b'bc;\r\n\tcba\r\n', 12)

    # unspecified, tries to get content from -1 to end
    # really should not happen -> so ignore it
    assert mhtml.next_line(b'abc\r\ndef', -1) == (b'f', -1)

    with pytest.raises(AttributeError):
        mhtml.next_line(None, -1)


def test_parse_header():
    assert mhtml.parse_header(b'', 0) == (mhtml.ResourceHeader(), -1)

    # needs two linebreaks (a single empty line) after the header fields
    with pytest.raises(AssertionError):
        assert mhtml.parse_header(b'CH: CV\r\n', 0) == \
            (mhtml.ResourceHeader([('CH', 'CV')]), -1)

    # really short header
    assert mhtml.parse_header(b'CH: CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV')]), -1)
    assert mhtml.parse_header(b'CH: CV\r\nCH2: CV2\r\nCH3: CV3\r\n\r\n', 0) \
        == (mhtml.ResourceHeader([('CH', 'CV'), ('CH2', 'CV2'),
                                  ('CH3', 'CV3')]), -1)

    # TODO: how to handle multiple spaces -> trim()?
    assert mhtml.parse_header(b'CH:     CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', '    CV')]), -1)
    # needs at least a single space
    assert mhtml.parse_header(b'CH:CV\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([]), -1)

    assert mhtml.parse_header(b'CH: CV\r\n\r\n\r\n-----boundary---', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV')]), 10)

    # value with linebreaks
    assert mhtml.parse_header(b'CH: CV;\r\n\tCV2\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV;\r\n\tCV2')]), -1)

    assert mhtml.parse_header(b'CH: CV;\r\n\tCV2\r\nCH2: CV3\r\n\r\n', 0) == \
        (mhtml.ResourceHeader([('CH', 'CV;\r\n\tCV2'), ('CH2', 'CV3')]), -1)


def test_find_next_boundary():
    # no boundary found
    assert mhtml.find_next_boundary(b'', '---boundary---', 0) == (-1, -1)

    # missing linebreak beforehand
    assert mhtml.find_next_boundary(b'--'
                                    b'---boundary---'
                                    b'\r\n', '---boundary---', 0) == (-1, -1)

    # needs a linebreak before
    assert mhtml.find_next_boundary(b'\r\n'
                                    b'--'
                                    b'---boundary---'
                                    b'\r\n', '---boundary---', 0) == (2, 20)

    # end-of-parts (of file?) boundary
    assert mhtml.find_next_boundary(b'\r\n'
                                    b'--'
                                    b'---boundary---'
                                    b'--\r\n', '---boundary---', 0) == (2, -1)


def test_parse_part():
    # boundary is string (because from header)
    with pytest.raises(TypeError):
        mhtml.parse_part(b'', b'', 0)

    bndry = '---boundary---'
    part_bndry = bytes('--' + bndry + '\r\n', 'ascii')
    file_bndry = bytes('--' + bndry + '--\r\n', 'ascii')

    # this case should not happen, because there will always be a part when
    # the function is called?
    assert mhtml.parse_part(b'', bndry, 0) == \
        ((mhtml.ResourceHeader(), 0, -1, 0), -1)
    # simulate last part (end-of-parts boundary) (see the extra dashes)
    assert mhtml.parse_part(b'CH: CV\r\n\r\ncontent\r\n'
                            + file_bndry,
                            bndry, 0) == \
        ((mhtml.ResourceHeader([('CH', 'CV')]), 0, 10, 19), -1)
    # simulate more parts (end-of-part boundary)
    assert mhtml.parse_part(b'CH: CV\r\n\r\ncontent\r\n'
                            + part_bndry,
                            bndry, 0) == \
        ((mhtml.ResourceHeader([('CH', 'CV')]), 0, 10, 19), 37)


def test_parse_parts_missing_head_boundary():
    bndry = '---boundary---'
    part_bndry = bytes('--' + bndry + '\r\n', 'ascii')
    file_bndry = bytes('--' + bndry + '--\r\n', 'ascii')
    assert mhtml.parse_parts(b'', bndry, 0) == ([], -1)

    # missing head boundary - should not happen
    # TODO: raise Error on missing boundary?
    assert mhtml.parse_parts(b'CH: CV\r\n\r\n', bndry, 0) == \
        ([], -1)
    assert mhtml.parse_parts(b'CH: CV\r\n\r\n'
                             + file_bndry, bndry, 0) \
        == ([], -1)
    assert mhtml.parse_parts(b'CH: CV\r\n\r\n'
                             b'content\r\n'
                             + file_bndry, bndry, 0) \
        == ([], -1)


def test_parse_parts_with_head_boundary():
    bndry = '---boundary---'
    part_bndry = bytes('--' + bndry + '\r\n', 'ascii')
    file_bndry = bytes('--' + bndry + '--\r\n', 'ascii')
    # head boundary - announce part
    assert mhtml.parse_parts(b'\r\n' + part_bndry +
                             b'CH: CV\r\n\r\n'
                             b'content\r\n', bndry, 2) \
        == ([(mhtml.ResourceHeader([('CH', 'CV')]),
              20, 30, 39)], -1)

    # TODO: work with monkeypatching?

    # TODO: should recognize empty part?
    # something like first part, then another follows but is somewhat vague ...
    assert mhtml.parse_parts(b'\r\n' + part_bndry +
                             b'CH: CV\r\n\r\n'
                             b'content\r\n'
                             + part_bndry, bndry, 2) \
        == ([(mhtml.ResourceHeader([('CH', 'CV')]),
              20, 30, 39),
             (mhtml.ResourceHeader(),
              57, -1, 57)], -1)

    # single part (use-case: last-part before file boundary)
    assert mhtml.parse_parts(b'\r\n' + part_bndry +
                             b'CH: CV\r\n\r\n'
                             b'content\r\n'
                             + file_bndry, bndry, 0) \
        == ([(mhtml.ResourceHeader([('CH', 'CV')]),
              20, 30, 39)], -1)


def test_parse_mhtml(monkeypatch):
    pass


# ---------------------------------------------------------------------------


def test_parse_mhtml_struct(monkeypatch):
    pass


def _get_open_ref():
    '''
    see: https://github.com/andras-tim/octoconf/blob/master/tests/common.py
    :rtype str
    '''
    # noqa: E501 pylint: disable=import-error,redefined-builtin,unused-import,unused-variable
    try:
        from builtins import open
        return 'builtins.open'
    except ImportError:
        from __builtin__ import open  # noqa: F401
        return '__builtin__.open'


def test_MHTMLArchive_from_file(mocker):  # noqa: N80
    mock_open = mocker.mock_open(read_data=b'abc')
    mocker.patch(_get_open_ref(), mock_open)
    mock_parse = mocker.patch('mhtml.parse_mhtml_struct')

    mhtml.MHTMLArchive_from_file('somefilename', only_header=True)

    mock_open.assert_called_once_with('somefilename', 'rb')
    mock_parse.assert_called_once_with(b'abc', only_header=True)


def test_MHTMLArchive_to_file(mocker):  # noqa: N80
    mock_open = mocker.mock_open()
    mock_mhtarc = mocker.Mock()
    mock_mhtarc.content = b'abc2'
    mocker.patch(_get_open_ref(), mock_open)

    mhtml.MHTMLArchive_to_file(mock_mhtarc, 'somefilename')

    mock_open.assert_called_once_with('somefilename', 'wb')
    mock_handle = mock_open()
    mock_handle.write.assert_called_once_with(b'abc2')


# ---------------------------------------------------------------------------


# pylint: disable=protected-access
def test_MHTMLArchive_properties(mocker):  # noqa: N802
    mhtarc = mhtml.MHTMLArchive(b'content', mhtml.ResourceHeader(), 0,
                                '---boundary---')
    assert mhtarc.headers == mhtml.ResourceHeader()
    mhtarc = mhtml.MHTMLArchive(b'content', None, 0, '---boundary---')
    assert mhtarc.headers == mhtml.ResourceHeader()

    mock_headers = mocker.Mock(content_type='content-abc',
                               location='location-abc')
    mhtarc._headers = mock_headers
    assert mhtarc.headers == mock_headers
    assert mhtarc.content_type == 'content-abc'
    assert mhtarc.location == 'location-abc'
    assert mhtarc.boundary == '---boundary---'

    assert mhtarc.content == b'content'


def test_MHTMLArchive_properties_resources(mocker):  # noqa: N802
    mhtarc = mhtml.MHTMLArchive(b'content', mhtml.ResourceHeader(), 0,
                                '---boundary---')
    assert mhtarc.resources == []
    assert mhtarc.get_resource(0) is None
    assert mhtarc.get_resource(-1) is None
    assert mhtarc.get_resource(10) is None

    # setting resources
    mhtarc._set_resources(None)
    assert isinstance(mhtarc.resources, list)
    mhtarc._set_resources('a')
    assert isinstance(mhtarc.resources, list)
    mhtarc._set_resources([])
    assert isinstance(mhtarc.resources, list)

    # TODO: checking resources from type Resource?
    mhtarc._set_resources([1])
    assert mhtarc.resources == [1]
    assert mhtarc.get_resource(0) == 1
    assert mhtarc.get_resource(1) is None
    assert mhtarc.remove_resource(-1) is False
    # wrong resource type should raise an error
    with pytest.raises(AttributeError,
                       match="""'int' object has no attribute 'get_resource_range'"""):  # noqa: E501  pylint: disable=line-too-long
        mhtarc.remove_resource(0)


def test_MHTMLArchive_helpers(mocker):  # noqa: N802
    mhtarc = mhtml.MHTMLArchive(b'content', mhtml.ResourceHeader(), 0,
                                '---boundary---')

    # valid resource index
    assert mhtarc._is_valid_resource_index(None) is False
    assert mhtarc._is_valid_resource_index(3.4) is False
    assert mhtarc._is_valid_resource_index(-1) is False
    assert mhtarc._is_valid_resource_index(0) is False
    assert mhtarc._is_valid_resource_index(1) is False

    mock_resource = mocker.Mock(spec=mhtml.Resource)
    mock_resource2 = mocker.Mock(spec=mhtml.Resource)
    mhtarc._set_resources([mock_resource, mock_resource2])

    assert mhtarc._is_valid_resource_index(-1) is False
    assert mhtarc._is_valid_resource_index(0) is True
    assert mhtarc._is_valid_resource_index(1) is True
    assert mhtarc._is_valid_resource_index(2) is False
    assert mhtarc._is_valid_resource_index('1') is False

    # get resource nr
    mhtarc._set_resources([])
    assert mhtarc._resource_to_nr(mock_resource) is None
    mhtarc._set_resources([mock_resource, mock_resource2])
    assert mhtarc._resource_to_nr(mock_resource) == 0
    assert mhtarc._resource_to_nr(mock_resource2) == 1
    assert mhtarc._resource_to_nr(None) is None
    assert mhtarc._resource_to_nr(0) is None

    # get resource + nr
    mhtarc._set_resources([])
    assert mhtarc._get_resource_and_nr(None) == (None, None, False)
    assert mhtarc._get_resource_and_nr(mock_resource)[2] is False
    assert mhtarc._get_resource_and_nr(0)[2] is False
    mhtarc._set_resources([mock_resource])
    assert mhtarc._get_resource_and_nr(mock_resource) == \
        (0, mock_resource, True)
    assert mhtarc._get_resource_and_nr(mock_resource2)[2] is False
    assert mhtarc._get_resource_and_nr(1)[2] is False
    assert mhtarc._get_resource_and_nr(-1)[2] is False
    mhtarc._set_resources([mock_resource, mock_resource2])
    assert mhtarc._get_resource_and_nr(mock_resource2) == \
        (1, mock_resource2, True)
    assert mhtarc._get_resource_and_nr('1') == (None, None, False)


def test_MHTMLArchive_remove_resource(mocker):  # noqa: N802
    mhtarc = mhtml.MHTMLArchive(b'content', mhtml.ResourceHeader(), 0,
                                '---boundary---')

    mock_resource = mocker.Mock(spec=mhtml.Resource)
    mock_resource.get_resource_range.return_value = (2, 5)
    mock_method = mocker.Mock()
    mhtarc._update_offsets = mock_method
    mhtarc._set_resources([mock_resource])

    assert mhtarc.remove_resource(0) is True
    assert mhtarc.remove_resource(0) is False

    assert mhtarc.content == b'cont'
    assert mhtarc.resources == []
    mock_resource.get_resource_range.assert_called_once_with(18)
    mock_method.assert_called_once_with(-3, 0)


def test_MHTMLArchive_insert_resource_reslist_nonempty(mocker):  # noqa: N802
    bndry = '---boundary---'
    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    header = b'H: V\r\n\r\n\r\n'
    content1 = b'H1: V2\r\n\r\ncontent\r\n'
    content2_header = b'H2: V33\r\n\r\n'
    content2_content = b'123\r\n'
    content2 = content2_header + content2_content
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc = mhtml.MHTMLArchive(content, mhtml.ResourceHeader(), len(header),
                                bndry)
    # existing resource in archive
    mock_resource = mocker.Mock(spec=mhtml.Resource)
    mock_resource.get_resource_range.return_value = (len(header), len(header) +
                                                     len(bndry_part) +
                                                     len(content1))
    mock_resource._offset_start = len(header) + len(bndry_part)
    mock_resource._offset_content = len(header) + len(bndry) + 10
    # resource to insert
    mock_resource2 = mocker.Mock(spec=mhtml.Resource)
    mock_resource2.headers = mhtml.ResourceHeader({'H2': 'V33'})
    mock_resource2.content_with_headers = content2
    mock_resource2._offset_start = 0
    mock_resource2._offset_content = len(content2_header)
    mhtarc._set_resources([mock_resource])

    assert mhtarc.insert_resource(-1, mock_resource2) is False
    assert mhtarc.insert_resource(3.14, mock_resource2) is False

    # insert at start
    assert mhtarc.insert_resource(0, mock_resource2) is True
    # mock_method = mocker.Mock()
    assert mhtarc.content == header \
        + bndry_part \
        + content2 \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    assert mhtarc.resources[1] == mock_resource
    assert mhtarc.resources[0] != mock_resource2
    assert mhtarc.resources[0]._offset_start == \
        len(header) + len(bndry_part)
    assert mhtarc.resources[0]._offset_content == \
        len(header) + len(bndry_part) + len(content2_header)
    assert mhtarc.resources[0]._offset_end == \
        len(header) + len(bndry_part) + len(content2)
    assert mhtarc.resources[0].headers == mock_resource2.headers

    # insert at end
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([mock_resource])
    assert mhtarc.insert_resource(9001, mock_resource2) is True
    assert mhtarc.content == header \
        + bndry_part \
        + content1 \
        + bndry_part \
        + content2 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    assert mhtarc.resources[0] == mock_resource
    assert len(mhtarc.resources) == 2


def test_MHTMLArchive_insert_resource_reslist_empty(mocker):  # noqa: N802
    bndry = '---boundary---'
    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    header = b'H: V\r\n\r\n\r\n'
    content1 = b'H1: V2\r\n\r\ncontent\r\n'
    content2_header = b'H2: V33\r\n\r\n'
    content2_content = b'123\r\n'
    content2 = content2_header + content2_content
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc = mhtml.MHTMLArchive(content, mhtml.ResourceHeader(), len(header),
                                bndry)
    # existing resource in archive
    mock_resource = mocker.Mock(spec=mhtml.Resource)
    mock_resource.get_resource_range.return_value = (len(header), len(header) +
                                                     len(bndry_part) +
                                                     len(content1))
    mock_resource._offset_start = len(header) + len(bndry_part)
    mock_resource._offset_content = len(header) + len(bndry) + 10
    # resource to insert
    mock_resource2 = mocker.Mock(spec=mhtml.Resource)
    mock_resource2.headers = mhtml.ResourceHeader({'H2': 'V33'})
    mock_resource2.content_with_headers = content2
    mock_resource2._offset_start = 0
    mock_resource2._offset_content = len(content2_header)
    mhtarc._set_resources([mock_resource])

    # insert when empty
    content = header \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([])
    assert mhtarc.insert_resource(9001, mock_resource2) is True
    assert mhtarc.content == header \
        + bndry_part \
        + content2 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    assert len(mhtarc.resources) == 1
    assert mhtarc.resources[0]._offset_start == \
        len(header) + len(bndry_part)
    assert mhtarc.resources[0]._offset_content == \
        len(header) + len(bndry_part) + len(content2_header)
    assert mhtarc.resources[0]._offset_end == \
        len(header) + len(bndry_part) + len(content2)
    assert mhtarc.resources[0].headers == mock_resource2.headers

    content = header \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([])
    assert mhtarc.insert_resource(0, mock_resource2) is True
    assert mhtarc.content == header \
        + bndry_part \
        + content2 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    assert len(mhtarc.resources) == 1
    assert mhtarc.resources[0]._offset_start == \
        len(header) + len(bndry_part)
    assert mhtarc.resources[0]._offset_content == \
        len(header) + len(bndry_part) + len(content2_header)
    assert mhtarc.resources[0]._offset_end == \
        len(header) + len(bndry_part) + len(content2)

    # check that not called (not neccessary)
    mock_method = mocker.Mock()
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([])
    mhtarc._update_offsets = mock_method

    assert mhtarc.insert_resource(0, mock_resource2) is True
    mock_method.assert_not_called()


def test_MHTMLArchive_insert_resource_update_calls(mocker):  # noqa: N802
    bndry = '---boundary---'
    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    header = b'H: V\r\n\r\n\r\n'
    content1 = b'H1: V2\r\n\r\ncontent\r\n'
    content2_header = b'H2: V33\r\n\r\n'
    content2_content = b'123\r\n'
    content2 = content2_header + content2_content
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc = mhtml.MHTMLArchive(content, mhtml.ResourceHeader(), len(header),
                                bndry)
    # existing resource in archive
    mock_resource = mocker.Mock(spec=mhtml.Resource)
    mock_resource.get_resource_range.return_value = (len(header), len(header) +
                                                     len(bndry_part) +
                                                     len(content1))
    mock_resource._offset_start = len(header) + len(bndry_part)
    mock_resource._offset_content = len(header) + len(bndry) + 10
    # resource to insert
    mock_resource2 = mocker.Mock(spec=mhtml.Resource)
    mock_resource2.headers = mhtml.ResourceHeader({'H2': 'V33'})
    mock_resource2.content_with_headers = content2
    mock_resource2._offset_start = 0
    mock_resource2._offset_content = len(content2_header)
    mhtarc._set_resources([mock_resource])

    # check that not called (not neccessary)
    mock_method1 = mocker.Mock()
    content = header \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([])
    mhtarc._update_offsets = mock_method1

    assert mhtarc.insert_resource(0, mock_resource2) is True
    mock_method1.assert_not_called()

    # check offset updates
    mock_method2 = mocker.Mock()
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([mock_resource])
    mhtarc._update_offsets = mock_method2
    assert mhtarc.insert_resource(9001, mock_resource2) is True
    mock_method2.assert_not_called()

    mock_method3 = mocker.Mock()
    content = header \
        + bndry_part \
        + content1 \
        + bytes('--' + bndry + '--\r\n', 'ascii')
    mhtarc._content = bytearray(content)
    mhtarc._set_resources([mock_resource])
    mhtarc._update_offsets = mock_method3
    assert mhtarc.insert_resource(0, mock_resource2) is True
    mock_method3.assert_called_once_with(len(bndry_part) + len(content2), 1)


def test_MHTMLArchive_change_resource_content(mocker):  # noqa: E501,N802 pylint: disable=too-many-locals
    bndry = '---boundary---'
    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    header = b'H: V\r\n\r\n\r\n'
    content1 = b'H1: V2\r\n\r\ncontent\r\n'
    content2_header = b'H2: V33\r\n\r\n'
    content2_content = b'123\r\n'
    content2_content_new = b'new_content_abc'
    content2 = content2_header + content2_content
    content = header \
        + bndry_part \
        + content1 \
        + bndry_part \
        + content2 \
        + bytes('--' + bndry + '--\r\n', 'ascii')

    mhtarc = mhtml.MHTMLArchive(content, mhtml.ResourceHeader(), len(header),
                                bndry)

    assert mhtarc.replace_content(0, content2_content_new) is False
    assert mhtarc.replace_content(None, content2_content_new) is False

    mock_resource = mocker.Mock(spec=mhtml.Resource)
    # resource to change
    mock_resource2 = mocker.Mock(spec=mhtml.Resource)
    offset = len(header) + len(bndry_part) + len(content1) + len(bndry_part)
    mock_resource2._offset_start = offset
    mock_resource2._offset_content = offset + len(content2_header)
    mock_resource2._offset_end = offset + len(content2)
    mhtarc._set_resources([mock_resource, mock_resource2])

    mock_method_get = mocker.Mock(return_value=(1, mock_resource2, True))
    mhtarc._get_resource_and_nr = mock_method_get
    mock_method_update = mocker.Mock()
    mhtarc._update_offsets = mock_method_update

    assert mhtarc.replace_content(mock_resource2, content2_content_new) is True
    mock_method_get.assert_called_once_with(mock_resource2)
    # difference between content, nr nach resource
    mock_method_update.assert_called_once_with(
        len(content2_content_new) - len(content2_content), 2)
    assert mock_resource2._offset_end == mock_resource2._offset_content \
        + len(content2_content_new)
    assert mhtarc.content == header \
        + bndry_part \
        + content1 \
        + bndry_part \
        + content2_header + content2_content_new \
        + bytes('--' + bndry + '--\r\n', 'ascii')


def test_MHTMLArchive_update_offsets(mocker):  # noqa: N802
    mhtarc = mhtml.MHTMLArchive(b'content', mhtml.ResourceHeader(), 0,
                                '---boundary---')

    mock_resource = mocker.Mock()
    mock_resource2 = mocker.Mock()
    mhtarc._set_resources([mock_resource, mock_resource2])

    # abort if not valid
    mhtarc._update_offsets(-5, None)
    mock_resource._update_offsets.assert_not_called()
    mock_resource2._update_offsets.assert_not_called()

    mhtarc._update_offsets(-5, 1)
    mock_resource._update_offsets.assert_not_called()
    mock_resource2._update_offsets.assert_called_once_with(-5)

    mhtarc._update_offsets(2, 0)
    mock_resource._update_offsets.assert_called_once_with(2)
    mock_resource2._update_offsets.assert_any_call(2)

    mock_method = mocker.Mock(return_value=False)
    mhtarc._is_valid_resource_index = mock_method
    mhtarc._update_offsets(2, 0)
    mock_method.assert_called_once_with(0)


def test_ContentEncoding():  # noqa: N802
    assert mhtml.ContentEncoding.parse('') is mhtml.ContentEncoding.UNKNOWN
    assert mhtml.ContentEncoding.parse(' ') is mhtml.ContentEncoding.UNKNOWN
    assert mhtml.ContentEncoding.parse('binary') is \
        mhtml.ContentEncoding.BINARY
    assert mhtml.ContentEncoding.parse(' bInAry') is \
        mhtml.ContentEncoding.BINARY
    assert mhtml.ContentEncoding.parse('B In Ary') is \
        mhtml.ContentEncoding.UNKNOWN


def test_ResourceHeader_headers():  # noqa: N802
    # single header as list or dict
    rh = mhtml.ResourceHeader([('a', 'b')])
    assert rh._headers == [('a', 'b')]
    rh = mhtml.ResourceHeader({'aA': 'BbC'})
    assert rh._headers == [('aA', 'BbC')]

    # empty header + add some
    rh = mhtml.ResourceHeader()
    assert rh._headers == []
    assert len(rh) == 0  # pylint: disable=len-as-condition
    rh['C'] = 'BbBb'
    rh['AAaA'] = 'BbBb'
    rh['AAaA'] = 'BbBb'
    rh['aaaa'] = 'bbbb'
    assert rh._headers == [('C', 'BbBb'), ('AAaA', 'BbBb'), ('AAaA', 'BbBb'),
                           ('aaaa', 'bbbb')]
    assert rh.items() == [('C', 'BbBb'), ('AAaA', 'BbBb'), ('AAaA', 'BbBb'),
                          ('aaaa', 'bbbb')]
    assert len(rh) == 4

    # none as key is ignored
    rh[None] = 1
    assert len(rh) == 4
    rh[''] = 1
    assert len(rh) == 5

    # set converts name to string
    rh[1] = 2
    assert len(rh) == 6
    assert rh._headers[5] == ('1', 2)

    # check contains, case insensitive
    assert '1' in rh
    assert 'c' in rh
    assert 'aaaa' in rh
    assert 'AAAA' in rh
    assert 'xxxxx' not in rh
    assert not 'xxxxx' in rh  # noqa: E713 pylint: disable=unneeded-not

    rh[None] = 1
    assert None not in rh


def test_ResourceHeader_properties(mocker):  # noqa: N802
    rh = mhtml.ResourceHeader()
    rh['C'] = 'BbBb'

    # content type
    mock_method = mocker.patch('mhtml.get_content_type')
    mock_method.return_value = 'ab'
    assert rh.content_type == 'ab'
    mock_method.assert_called_once_with(rh)

    # encoding
    mock_get = mocker.Mock()
    mock_get.return_value = 1
    rh.get = mock_get
    assert rh.encoding == 1
    mock_get.assert_called_once_with('Content-Transfer-Encoding')

    # location
    mock_get = mocker.Mock()
    mock_get.return_value = None
    rh.get = mock_get
    assert rh.location is None
    assert mock_get.call_args_list == [
        mocker.call('Snapshot-Content-Location'),
        mocker.call('Content-Location')]

    def mock_get_sideeffect(name):
        if name == 'Snapshot-Content-Location':
            return 5
        return None

    mock_get = mocker.Mock(side_effect=mock_get_sideeffect)
    rh.get = mock_get
    assert rh.location == 5

    def mock_get_sideeffect2(name):
        if name == 'Content-Location':
            return 6
        return None

    mock_get = mocker.Mock(side_effect=mock_get_sideeffect2)
    rh.get = mock_get
    assert rh.location == 6


def test_ResourceHeader_magic():  # noqa: N802
    # eq / ne
    rh1 = mhtml.ResourceHeader([('a', 'b')])
    rh2 = mhtml.ResourceHeader([('A', 'b')])
    rh3 = mhtml.ResourceHeader([('A', 'b')])
    rh4 = mhtml.ResourceHeader([('c', 'b')])
    assert not rh1 == rh2  # pylint: disable=unneeded-not
    assert rh2 == rh3
    assert rh1 != rh2
    assert not rh2 != rh3  # pylint: disable=unneeded-not
    assert rh2 != rh4
    assert not rh1 == rh4  # pylint: disable=unneeded-not
    assert (not rh1.__eq__(rh2)) == rh1.__ne__(rh2)
    assert rh3.__eq__(rh2) == (not rh3.__ne__(rh2))

    # checks type, not only content
    assert rh1 != rh1._headers

    # str / repr
    assert str(rh2) == str(rh2._headers)
    assert repr(rh2) == 'ResourceHeader: ' + repr(rh2._headers)

    # as_list
    rh = mhtml.ResourceHeader([('a', 'b'), ('A', 'c'), ('D', 'e')])
    assert rh.as_list() == [('a', 'b'), ('A', 'c'), ('D', 'e')]

    hl = rh.as_list()
    hl.append(('t', 't'))
    assert rh.as_list() != hl

    # as_dict
    rh = mhtml.ResourceHeader([('a', 'b'), ('A', 'c'), ('D', 'e')])
    assert rh.as_dict() == {'a': 'b', 'A': 'c', 'D': 'e'}

    # iter
    rh = mhtml.ResourceHeader([('a', 'b'), ('A', 'c'), ('D', 'e')])
    assert iter(rh)
    assert list(rh) == ['a', 'A', 'D']

    # del
    rh = mhtml.ResourceHeader([('a', 'b'), ('A', 'c'), ('D', 'e')])
    del rh['a']
    assert rh.items() == [('D', 'e')]
    del rh[None]
    assert len(rh) == 1

    # TODO: get/del/set empty strings?
    rh = mhtml.ResourceHeader()
    rh[''] = 'h'
    assert len(rh) == 1
    assert rh[''] == 'h'
    del rh['']
    assert len(rh) == 0


def test_ResourceHeader_methods_get():  # noqa: N802
    rh = mhtml.ResourceHeader()
    rh['a'] = 'b'

    assert rh.get(None, None) is None
    assert rh.get(None, 'y') == 'y'

    assert rh.get('A') == 'b'
    assert rh.get('a') == 'b'
    assert rh.get('a', None) == 'b'
    assert rh.get('c', 'x') == 'x'

    assert rh.get_all('a') == ['b']
    assert rh.get_all('c') == []
    # return default list on invalid key/name
    assert rh.get_all(None) == []
    assert rh.get_all(None, default=1) == 1

    rh['A'] = 'F'
    assert rh.get_all('a') == ['b', 'F']

    # getter
    assert rh['a'] == 'b'
    rh['C'] = 1
    rh['c'] = 2
    assert rh['c'] == 1


def test_Resource_properties(mocker):  # noqa: N802
    with pytest.raises(AssertionError,
                       match='mhtml_file should be a MHTMLArchive'):
        mhtml.Resource(None, None, 0, 0, 0)

    mhtarc = mhtml.MHTMLArchive(b'', None, 0, '---boundary---')

    # default resource headers
    res = mhtml.Resource(mhtarc, None, 0, 0, 0)
    assert res.headers == mhtml.ResourceHeader()
    assert res.headers == res._headers

    assert mhtml.Resource(mhtarc, None, 0, 0, 0).headers == \
        mhtml.ResourceHeader()
    assert mhtml.Resource(mhtarc, [], 0, 0, 0).headers == \
        mhtml.ResourceHeader()
    assert mhtml.Resource(mhtarc, {}, 0, 0, 0).headers == \
        mhtml.ResourceHeader()

    # properties
    mock_headers = mocker.Mock(content_type='content-abc',
                               location='location-abc',
                               encoding='encoding-123')
    res._headers = mock_headers
    assert res.content_type == 'content-abc'
    assert res.location == 'location-abc'
    assert res.encoding == 'encoding-123'

    # filename
    mock_method = mocker.patch('mhtml.make_filename')
    mock_method.return_value = 'name'
    assert res.get_short_filename(default='foo') == 'name'
    mock_method.assert_called_once_with(res._headers, default='foo')

    # content
    mock_prop = mocker.Mock(return_value=b'123')
    res.get_content = mock_prop
    assert res.content == b'123'
    mock_prop.assert_called_once_with()

    # content set
    mock_prop_set = mocker.Mock()
    res.set_content = mock_prop_set
    res.content = b'abc123'
    mock_prop_set.assert_called_once_with(b'abc123')


def test_Resource_content():  # noqa: N802
    bndry = '---boundary1---'
    content = b'-'
    mhtarc = mhtml.MHTMLArchive(content, None, 0, bndry)

    # this should not happen
    # TODO: maybe later a way to construct a Resource without a MHTMLArchive?
    # but how to use standalone? (rather a construction method/factory)
    res = mhtml.Resource(mhtarc, None, 0, 0, 0)
    res._mhtml_file._content = None
    assert res.get_content() is None
    assert res.content is None
    assert res.content_with_headers is None
    res._mhtml_file = None
    assert res.get_content() is None
    assert res.content is None
    assert res.content_with_headers is None

    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    bndry_end = bytes('--' + bndry + '--\r\n', 'ascii')
    content_header = b'H1: V1\r\n\r\n'
    content_content = b'Content\r\n'
    content = bndry_part + content_header + content_content + bndry_end
    # offsets in content
    offset = len(bndry_part)
    offset_content = offset + len(content_header)
    offset_end = offset_content + len(content_content)
    # objects
    mhtarc = mhtml.MHTMLArchive(content, None, 0, bndry)
    res = mhtml.Resource(mhtarc, None, offset, offset_content, offset_end)
    # check
    assert res.get_content() == content_content
    assert res.content_with_headers == content_header + content_content
    assert res.get_resource_range(-1) == (0, offset_end)
    assert res.get_resource_range(offset) == (0, offset_end)

    # TODO: may need an error case?
    # wrong offset or missing content?

    # update offsets wrong
    with pytest.raises(AssertionError):
        res._update_offsets('a')
    with pytest.raises(AssertionError):
        res._update_offsets(-3.4)
    with pytest.raises(AssertionError):
        res._update_offsets(None)

    # update offsets right
    res._update_offsets(-1)
    assert res._offset_start == offset - 1
    assert res._offset_content == offset_content - 1
    assert res._offset_end == offset_end - 1
    res._update_offsets(3)
    assert res._offset_start == offset - 1 + 3
    assert res._offset_content == offset_content - 1 + 3
    assert res._offset_end == offset_end - 1 + 3


def test_Resource_content_get(mocker):  # noqa: N802
    bndry = '---boundary1---'
    bndry_part = bytes('--' + bndry + '\r\n', 'ascii')
    bndry_end = bytes('--' + bndry + '--\r\n', 'ascii')
    content_header = b'H1: V1\r\n\r\n'
    content_content = b'Content\r\n'
    content = bndry_part + content_header + content_content + bndry_end
    # offsets in content
    offset = len(bndry_part)
    offset_content = offset + len(content_header)
    offset_end = offset_content + len(content_content)
    # objects
    mhtarc = mhtml.MHTMLArchive(content, None, 0, bndry)
    res = mhtml.Resource(mhtarc, None, offset, offset_content, offset_end)

    assert res.get_content() == content_content
    assert res.get_content(decode=False) == content_content

    # TODO: decoded content is currently None since no decoder implemented
    assert res.get_content(decode=True) is None

    # TODO: this currently needs work ...
    mock_headers = mocker.Mock()
    res._headers = mock_headers

    mock_headers.encoding = 'binary'
    assert res.get_content(decode=True) == content_content

    mock_headers.encoding = 'base64'
    assert res.get_content(decode=True) is None
    mock_headers.encoding = 'Quoted-Printable'
    assert res.get_content(decode=True) is None

    # default to binary
    # TODO: or should default to None?
    mock_headers.encoding = 'base64binary'
    assert res.get_content(decode=True) is None


def test_Resource_content_set(mocker):  # noqa: N802
    bndry = '---boundary1---'
    content = b'-'
    mhtarc = mhtml.MHTMLArchive(content, None, 0, bndry)
    res = mhtml.Resource(mhtarc, None, 0, 0, 0)

    # check for correct references
    res._mhtml_file._content = 'abc'
    assert res.set_content(b'') is False
    res._mhtml_file = None
    assert res.set_content(b'') is False

    # test that calls are done
    mhtarc = mhtml.MHTMLArchive(content, None, 0, bndry)
    res = mhtml.Resource(mhtarc, None, 0, 0, 0)
    mock_method_replace = mocker.Mock(return_value=1)
    mhtarc.replace_content = mock_method_replace
    assert res.set_content(b'abc123') == 1
    mock_method_replace.assert_called_once_with(res, b'abc123')


def test_Resource():  # noqa: N802
    pass


# pylint: enable=protected-access
