# pylint: disable=missing-docstring,invalid-name
# pylint: disable=protected-access

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


def test_parse_mhtml(mocker):
    content = b'content'
    bndry = '--bndry--'
    header_end_pos = 5
    line1 = b'\r\n'
    line2 = b'other\r\n'
    next_pos = 10
    parts = [1, 2, 4]

    mock_meth_parse_header = mocker.Mock()
    mock_meth_next_line = mocker.Mock()
    mock_meth_get_boundary = mocker.Mock()
    mock_meth_parse_parts = mocker.Mock()
    mocker.patch('mhtml.parse_header', mock_meth_parse_header)
    mocker.patch('mhtml.next_line', mock_meth_next_line)
    mocker.patch('mhtml.get_boundary', mock_meth_get_boundary)
    mocker.patch('mhtml.parse_parts', mock_meth_parse_parts)

    # no boundary in header
    mock_meth_parse_header.return_value = (mocker.sentinel.headers,
                                           header_end_pos)
    mock_meth_next_line.return_value = (line1, next_pos)
    mock_meth_get_boundary.return_value = None
    assert mhtml.parse_mhtml(content) == (mocker.sentinel.headers, None)
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_meth_parse_parts.assert_not_called()

    # with boundary
    mock_meth_parse_header.reset_mock()
    mock_meth_next_line.reset_mock()
    mock_meth_get_boundary.reset_mock()
    mock_meth_next_line.return_value = (line1, next_pos)
    mock_meth_get_boundary.return_value = bndry
    mock_meth_parse_parts.return_value = (parts, -1)
    assert mhtml.parse_mhtml(content) == (mocker.sentinel.headers, parts)
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_meth_parse_parts.assert_called_once_with(content, bndry, next_pos)

    # only single empty line after header
    # TODO: should fail if not two empty lines after header?
    mock_meth_next_line.reset_mock()
    mock_meth_get_boundary.reset_mock()
    mock_meth_parse_parts.reset_mock()
    mock_meth_next_line.return_value = (line2, next_pos)
    mock_meth_parse_parts.return_value = (parts, -1)
    assert mhtml.parse_mhtml(content) == (mocker.sentinel.headers, parts)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_meth_parse_parts.assert_called_once_with(content, bndry,
                                                  header_end_pos)

    # invalid parts parse
    mock_meth_parse_parts.reset_mock()
    mock_meth_parse_parts.return_value = (parts, 9001)
    with pytest.raises(AssertionError,
                       match='file should be completly parsed'):
        mhtml.parse_mhtml(content)
    mock_meth_parse_parts.assert_called_once_with(content, bndry,
                                                  header_end_pos)

    # TODO: check if not bytes content?


# ---------------------------------------------------------------------------


def test_parse_mhtml_struct_no_parts(mocker):
    content = b'content'
    bndry = '---bndry---'
    header_end_pos = 6
    next_pos = 55

    mock_mhtarc_class = mocker.patch('mhtml.MHTMLArchive', spec=True)

    mock_meth_parse_header = mocker.patch('mhtml.parse_header')
    mock_meth_next_line = mocker.patch('mhtml.next_line')
    mock_meth_get_boundary = mocker.patch('mhtml.get_boundary')
    mock_meth_parse_parts = mocker.patch('mhtml.parse_parts')

    # only header
    mock_mhtarc_class.return_value = mocker.sentinel.mhtarc
    mock_meth_parse_header.return_value = (mocker.sentinel.headers,
                                           header_end_pos)
    mock_meth_next_line.return_value = (b'\r\n', next_pos)
    mock_meth_get_boundary.return_value = bndry
    assert mhtml.parse_mhtml_struct(content, True) == mocker.sentinel.mhtarc
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_mhtarc_class.assert_called_once_with(content, mocker.sentinel.headers,
                                              next_pos, bndry)
    mock_meth_parse_parts.assert_not_called()

    # no extra free line after header
    mock_mhtarc_class.reset_mock()
    mock_meth_parse_header.reset_mock()
    mock_meth_next_line.reset_mock()
    mock_meth_get_boundary.reset_mock()
    mock_meth_next_line.return_value = (b'start of content or bndry', next_pos)
    assert mhtml.parse_mhtml_struct(content, True) == mocker.sentinel.mhtarc
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_mhtarc_class.assert_called_once_with(content, mocker.sentinel.headers,
                                              header_end_pos, bndry)
    mock_meth_parse_parts.assert_not_called()

    # no boundary
    mock_mhtarc_class.reset_mock()
    mock_meth_parse_header.reset_mock()
    mock_meth_next_line.reset_mock()
    mock_meth_get_boundary.reset_mock()
    mock_meth_get_boundary.return_value = None
    mock_meth_next_line.return_value = (b'\r\n', next_pos)
    assert mhtml.parse_mhtml_struct(content, True) == mocker.sentinel.mhtarc
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_mhtarc_class.assert_called_once_with(content, mocker.sentinel.headers,
                                              next_pos, None)
    mock_meth_parse_parts.assert_not_called()


def test_parse_mhtml_struct_with_parts(mocker):
    content = b'content'
    bndry = '---bndry---'
    header_end_pos = 6
    next_pos = 55
    parts = [(1, 2, 3, 4), (11, 22, 33, 44), (111, 222, 333, 444)]  # dummies

    mock_mhtarc_class = mocker.patch('mhtml.MHTMLArchive', spec=True)
    mock_res_class = mocker.patch('mhtml.Resource', spec=True)

    mock_meth_parse_header = mocker.patch('mhtml.parse_header')
    mock_meth_next_line = mocker.patch('mhtml.next_line')
    mock_meth_get_boundary = mocker.patch('mhtml.get_boundary')
    mock_meth_parse_parts = mocker.patch('mhtml.parse_parts')

    # only header
    mock_mhtarc_class.return_value = mocker.sentinel.mhtarc
    mock_meth_parse_header.return_value = (mocker.sentinel.headers,
                                           header_end_pos)
    mock_meth_set_res = mocker.Mock()
    mocker.sentinel.mhtarc._set_resources = mock_meth_set_res
    mock_meth_next_line.return_value = (b'\r\n', next_pos)
    mock_meth_get_boundary.return_value = bndry
    mock_meth_parse_parts.return_value = (parts, -1)
    mock_res_class.side_effect = [mocker.sentinel.res1, mocker.sentinel.res2,
                                  mocker.sentinel.res3]
    assert mhtml.parse_mhtml_struct(content, False) == mocker.sentinel.mhtarc
    mock_meth_parse_header.assert_called_once_with(content, 0)
    mock_meth_next_line.assert_called_once_with(content, header_end_pos)
    mock_meth_get_boundary.assert_called_once_with(mocker.sentinel.headers)
    mock_mhtarc_class.assert_called_once_with(content, mocker.sentinel.headers,
                                              next_pos, bndry)
    mock_meth_parse_parts.assert_called_once_with(content, bndry, next_pos)
    mock_meth_set_res.assert_called_once_with([mocker.sentinel.res1,
                                               mocker.sentinel.res2,
                                               mocker.sentinel.res3])
    mock_res_class.assert_has_calls([
        mocker.call(mocker.sentinel.mhtarc, 1, 2, 3, 4),
        mocker.call(mocker.sentinel.mhtarc, 11, 22, 33, 44),
        mocker.call(mocker.sentinel.mhtarc, 111, 222, 333, 444)])

    # no end of parts parse
    mock_res_class.reset_mock()
    mock_meth_set_res.reset_mock()
    mock_meth_parse_parts.return_value = (parts, 2)
    with pytest.raises(AssertionError,
                       match='file should be completly parsed'):
        mhtml.parse_mhtml_struct(content, False)
    mock_res_class.assert_not_called()
    mock_meth_set_res.assert_not_called()


def _get_open_ref():  # pragma: no cover
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
