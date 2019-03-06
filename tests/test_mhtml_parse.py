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
