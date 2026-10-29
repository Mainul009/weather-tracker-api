from app import create_app


def test_app_factory_creates_app():
    app = create_app()
    assert app is not None
    assert app.url_map
    assert "auth" in {bp.name for bp in app.blueprints.values()}
