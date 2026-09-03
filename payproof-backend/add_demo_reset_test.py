import pathlib
p = pathlib.Path('tests/test_cases_api.py')
text = p.read_text(encoding='utf-8')

test_code = """
def test_demo_reset_disabled_in_production():
    from app.config import settings
    
    # Save original
    original_env = settings.environment
    original_demo = settings.demo_mode
    
    try:
        # Simulate production environment
        settings.environment = "production"
        settings.demo_mode = False
        
        r = client.delete("/cases/demo-reset")
        assert r.status_code == 403
        assert "disabled" in r.json()["detail"]
        
        # Simulate development environment
        settings.environment = "development"
        r2 = client.delete("/cases/demo-reset")
        assert r2.status_code == 200
        
        # Simulate production but demo_mode = True
        settings.environment = "production"
        settings.demo_mode = True
        r3 = client.delete("/cases/demo-reset")
        assert r3.status_code == 200
        
    finally:
        settings.environment = original_env
        settings.demo_mode = original_demo
"""

if 'test_demo_reset_disabled_in_production' not in text:
    text += test_code
    p.write_text(text, encoding='utf-8')
print("Successfully added test to test_cases_api.py")
