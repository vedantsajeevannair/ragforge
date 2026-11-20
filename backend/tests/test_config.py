from app.config import BACKEND_DIR, Settings


def test_default_data_dir_is_inside_backend():
    assert Settings().data_dir == BACKEND_DIR / "data"


def test_relative_data_dir_is_anchored_to_backend(tmp_path):
    assert Settings(data_dir="var/x").data_dir == (BACKEND_DIR / "var/x").resolve()
    assert Settings(data_dir=tmp_path).data_dir == tmp_path
