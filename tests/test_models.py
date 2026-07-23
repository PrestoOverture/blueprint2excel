from drawing_inspector.models import Dimension, TextObject


def test_text_object_stores_pdf_word_properties() -> None:
    text_object = TextObject(
        text="920",
        x=1.0,
        y=2.0,
        width=3.0,
        height=4.0,
        rotation=0.0,
        font_name="Arial",
        font_size=5.0,
    )

    assert text_object.text == "920"
    assert text_object.rotation == 0.0


def test_dimension_stores_reassembled_measurement() -> None:
    dimension = Dimension(
        nominal=15.0,
        upper_deviation=0.018,
        lower_deviation=0.0,
        tolerance_grade=None,
        dimension_type="linear",
        x=10.0,
        y=20.0,
        bubble_id=None,
    )

    assert dimension.nominal == 15.0
    assert dimension.upper_deviation == 0.018
