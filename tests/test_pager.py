from lang_qc.models.pager import PagedResponse


def test_slicing():

    input_list = []
    input_list.extend(range(1, 21))

    pager = PagedResponse(page_size=5, page_number=1)
    assert pager.slice_data(input_list) == [1, 2, 3, 4, 5]

    pager = PagedResponse(page_size=5, page_number=3)
    assert pager.slice_data(input_list) == [11, 12, 13, 14, 15]

    pager = PagedResponse(page_size=5, page_number=4)
    assert pager.slice_data(input_list) == [16, 17, 18, 19, 20]

    pager = PagedResponse(page_size=5, page_number=5)
    assert pager.slice_data(input_list) == []

    pager = PagedResponse(page_size=3, page_number=7)
    assert pager.slice_data(input_list) == [19, 20]

    pager = PagedResponse(page_size=25, page_number=1)
    assert pager.slice_data(input_list) == input_list
